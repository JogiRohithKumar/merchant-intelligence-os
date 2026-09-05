"""
Deterministic Synthetic Merchant Data Generator
Seed: 42 — always reproducible

Ground-truth anomalies injected:
1. Days 30-35: Payment failure rate 22.4% (baseline: 2.1%) - gateway degradation
2. Segment B: Chargeback rate 4.7% (baseline: 0.8%) - fraud ring
3. Product X (SKU: PROD-X-001): Conversion rate 2.1% (baseline: 4.2%) - pricing mismatch
4. Settlement on day 60: net_amount short by INR 78,000 - settlement mismatch
"""
import random
import uuid
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from faker import Faker
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.core.logging import get_logger

SEED = 42
random.seed(SEED)
fake = Faker('en_IN')
Faker.seed(SEED)

logger = get_logger(__name__)

# Config
NUM_CUSTOMERS = 1_000
NUM_PRODUCTS = 100
NUM_DAYS = 90
NUM_SUBSCRIPTIONS = 200

# Anomaly parameters
ANOMALY_START_DAY = 30
ANOMALY_END_DAY = 35
BASELINE_FAILURE_RATE = 0.021
ANOMALY_FAILURE_RATE = 0.224
SEGMENT_B_CB_RATE = 0.047
BASELINE_CB_RATE = 0.008
PRODUCT_X_CONVERSION = 0.021
BASELINE_CONVERSION = 0.042
SETTLEMENT_MISMATCH_INR = 78_000

PAYMENT_METHODS = ['upi', 'card', 'netbanking', 'wallet', 'emi']
GATEWAYS = ['razorpay', 'payu', 'cashfree']
COUNTRIES = ['IN', 'US', 'GB', 'SG', 'AE']
DEVICES = ['mobile', 'desktop', 'tablet']
CATEGORIES = ['Electronics', 'Apparel', 'FMCG', 'Books', 'Home', 'Sports']
CHANNELS = ['organic', 'paid_search', 'social', 'email', 'referral', 'direct']
FAILURE_REASONS = ['gateway_timeout', 'card_declined', 'insufficient_funds', 'network_error', 'expired_card', 'fraud_block']
CB_REASON_CODES = ['4853', '4855', '4863', '10.4', '13.1', '13.9']

def rnd_amount(low, high):
    # Round to nearest 50
    raw = random.uniform(low, high)
    return round(raw / 50) * 50

def rnd_bool(prob):
    return random.random() < prob

def generate_all_data(db: Session) -> dict:
    """
    Main entry point. Generates all synthetic data and persists to database.
    Returns summary counts.
    """
    from app.database.models import (
        Merchant, User, Customer, Product, Order, OrderItem,
        Transaction, PaymentAttempt, Chargeback, RiskEvent,
        Subscription, Settlement, SettlementItem, Campaign
    )
    
    logger.info('Starting synthetic data generation (seed=42)...')
    now = datetime.now(timezone.utc)
    base_date = now - timedelta(days=NUM_DAYS)
    
    # --- MERCHANT ---
    merchant = Merchant(
        id='merchant-bharat-001',
        name='Bharat Commerce Pvt Ltd',
        business_type='ecommerce',
        country='IN',
        currency='INR',
        status='active',
        monthly_revenue_baseline=Decimal('3240000')
    )
    db.merge(merchant)
    
    # --- DEMO USER ---
    user = User(
        id='user-demo-admin-001',
        email='demo@merchant.com',
        hashed_password=get_password_hash('demo123'),
        full_name='Priya Sharma',
        role='merchant_admin',
        merchant_id='merchant-bharat-001'
    )
    db.merge(user)
    db.flush()
    logger.info('Merchant and demo user created.')
    
    # --- CUSTOMERS ---
    customers = []
    segments = ['A', 'B', 'C', 'D']
    seg_weights = [0.15, 0.20, 0.40, 0.25]  # A=premium, B=fraud-prone, C=standard, D=inactive
    for i in range(NUM_CUSTOMERS):
        seg = random.choices(segments, weights=seg_weights)[0]
        risk = 0.05 if seg == 'A' else (0.35 if seg == 'B' else (0.1 if seg == 'C' else 0.08))
        risk += random.uniform(-0.02, 0.02)
        risk = max(0.0, min(1.0, risk))
        c = Customer(
            id=f'cust-{i:06d}',
            merchant_id='merchant-bharat-001',
            external_id=f'EXT-{i:06d}',
            email=fake.email(),
            full_name=fake.name(),
            segment=seg,
            country=random.choices(COUNTRIES, weights=[0.85,0.06,0.04,0.03,0.02])[0],
            acquisition_channel=random.choices(CHANNELS, weights=[0.3,0.2,0.15,0.15,0.1,0.1])[0],
            total_orders=0,
            total_spend=0.0,
            last_order_at=None,
            risk_score=round(risk, 3),
            is_high_risk=risk > 0.25
        )
        customers.append(c)
        db.add(c)
    db.flush()
    logger.info(f'{NUM_CUSTOMERS} customers created.')
    
    # --- PRODUCTS ---
    products = []
    for i in range(NUM_PRODUCTS):
        cat = random.choice(CATEGORIES)
        price = rnd_amount(500, 15000) if cat == 'Electronics' else rnd_amount(200, 5000)
        is_product_x = (i == 0)  # Product X is always index 0
        p = Product(
            id='product-x-001' if is_product_x else f'prod-{i:05d}',
            merchant_id='merchant-bharat-001',
            sku='PROD-X-001' if is_product_x else f'SKU-{i:05d}',
            name='Bharat Smart LED TV 43" (Product X)' if is_product_x else f'{fake.word().capitalize()} {cat} Item {i}',
            category=cat,
            price=Decimal(str(price)),
            cost=Decimal(str(round(price * 0.6, 2))),
            inventory_count=random.randint(0, 500),
            conversion_rate=PRODUCT_X_CONVERSION if is_product_x else round(BASELINE_CONVERSION + random.uniform(-0.01, 0.02), 4),
            avg_order_value=float(price) * 1.1,
            is_active=True,
            is_anomalous=is_product_x
        )
        products.append(p)
        db.add(p)
    db.flush()
    logger.info(f'{NUM_PRODUCTS} products created.')
    
    # --- ORDERS + TRANSACTIONS ---
    total_transactions = 0
    total_failed_payments = 0
    total_chargebacks = 0
    chargeback_records = []
    transaction_records = []
    
    for day_offset in range(NUM_DAYS):
        current_date = base_date + timedelta(days=day_offset)
        # Volume varies by day-of-week
        dow = current_date.weekday()
        daily_volume = int(random.gauss(120, 20))
        if dow in [5, 6]:  # weekend boost
            daily_volume = int(daily_volume * 1.3)
        
        is_anomaly_day = ANOMALY_START_DAY <= day_offset <= ANOMALY_END_DAY
        failure_rate = ANOMALY_FAILURE_RATE if is_anomaly_day else BASELINE_FAILURE_RATE
        
        for _ in range(daily_volume):
            customer = random.choice(customers)
            product = random.choice(products)
            amount = rnd_amount(500, 25000)
            hour = random.choices(range(24), weights=_hour_weights())[0]
            txn_time = current_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59), tzinfo=timezone.utc)
            
            is_failed = rnd_bool(failure_rate)
            status = 'failed' if is_failed else 'success'
            gw = random.choices(GATEWAYS, weights=[0.6, 0.25, 0.15])[0]
            method = random.choices(PAYMENT_METHODS, weights=[0.45, 0.30, 0.12, 0.08, 0.05])[0]
            
            # Risk score
            base_risk = customer.risk_score
            if is_anomaly_day: base_risk += 0.15
            if amount > 15000: base_risk += 0.1
            if method == 'card' and customer.segment == 'B': base_risk += 0.2
            risk = max(0.0, min(1.0, base_risk + random.gauss(0, 0.05)))
            
            txn_id = f'txn-{uuid.uuid4().hex[:16]}'
            order_id = f'ord-{uuid.uuid4().hex[:12]}'
            order_num = f'ORD-{day_offset:03d}-{_:04d}'
            
            order = Order(
                id=order_id,
                merchant_id='merchant-bharat-001',
                customer_id=customer.id,
                order_number=order_num,
                status='completed' if not is_failed else 'pending',
                subtotal=Decimal(str(amount)),
                discount=Decimal('0'),
                tax=Decimal(str(round(amount * 0.18, 2))),
                total=Decimal(str(round(amount * 1.18, 2))),
                created_at=txn_time
            )
            db.add(order)
            
            txn = Transaction(
                id=txn_id,
                merchant_id='merchant-bharat-001',
                customer_id=customer.id,
                order_id=order_id,
                transaction_type='payment',
                amount=Decimal(str(amount)),
                currency='INR',
                status=status,
                gateway=gw,
                gateway_transaction_id=f'gw-{uuid.uuid4().hex[:20]}',
                payment_method=method,
                country=customer.country,
                device_type=random.choice(DEVICES),
                ip_address=fake.ipv4(),
                risk_score=round(risk, 3),
                is_anomaly_day=is_anomaly_day,
                created_at=txn_time,
                settled_at=txn_time + timedelta(days=2) if not is_failed else None
            )
            db.add(txn)
            transaction_records.append(txn)
            total_transactions += 1
            
            if is_failed:
                retry_count = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
                failure_reason = random.choices(
                    FAILURE_REASONS,
                    weights=[0.35, 0.25, 0.15, 0.1, 0.1, 0.05] if is_anomaly_day else [0.1, 0.3, 0.25, 0.15, 0.15, 0.05]
                )[0]
                recovery_prob = _calc_recovery_prob(failure_reason, retry_count, risk, amount)
                attempt = PaymentAttempt(
                    id=f'pa-{uuid.uuid4().hex[:16]}',
                    transaction_id=txn_id,
                    merchant_id='merchant-bharat-001',
                    attempt_number=retry_count + 1,
                    status='failed',
                    failure_reason=failure_reason,
                    amount=Decimal(str(amount)),
                    gateway=gw,
                    gateway_response_code=_gateway_code(failure_reason),
                    risk_score=round(risk, 3),
                    is_retry=(retry_count > 0),
                    recovery_probability=round(recovery_prob, 4),
                    expected_recovery_value=round(amount * recovery_prob, 2),
                    created_at=txn_time
                )
                db.add(attempt)
                total_failed_payments += 1
            
            # Chargebacks
            if not is_failed:
                cb_rate = SEGMENT_B_CB_RATE if customer.segment == 'B' else BASELINE_CB_RATE
                if rnd_bool(cb_rate):
                    cb = Chargeback(
                        id=f'cb-{uuid.uuid4().hex[:16]}',
                        merchant_id='merchant-bharat-001',
                        transaction_id=txn_id,
                        customer_id=customer.id,
                        chargeback_ref=f'CB-{uuid.uuid4().hex[:12].upper()}',
                        amount=Decimal(str(amount)),
                        currency='INR',
                        reason_code=random.choice(CB_REASON_CODES),
                        reason_description='Customer dispute - item not received',
                        status=random.choices(['received', 'under_review', 'won', 'lost'], weights=[0.3,0.4,0.2,0.1])[0],
                        evidence_submitted=rnd_bool(0.4),
                        evidence_deadline=txn_time + timedelta(days=30),
                        is_segment_b=(customer.segment == 'B'),
                        created_at=txn_time + timedelta(days=random.randint(5, 15))
                    )
                    chargeback_records.append(cb)
                    db.add(cb)
                    total_chargebacks += 1
        
        if day_offset % 10 == 0:
            db.flush()
            logger.info(f'Generated day {day_offset}/{NUM_DAYS}...')
    
    db.flush()
    
    # --- SETTLEMENTS ---
    total_settlements = 0
    for day_offset in range(0, NUM_DAYS, 1):  # daily settlements
        period_date = base_date + timedelta(days=day_offset)
        gross = rnd_amount(800_000, 2_500_000)
        fees = round(gross * 0.02, 2)  # 2% fee
        tax_amt = round(fees * 0.18, 2)  # GST on fees
        refunds_amt = round(gross * 0.015, 2)
        cb_amt = round(gross * 0.005, 2)
        net = round(gross - fees - tax_amt - refunds_amt - cb_amt, 2)
        
        expected = net
        discrepancy = 0.0
        has_mismatch = False
        status = 'matched'
        
        if day_offset == 60:  # Inject settlement mismatch on day 60
            net = net - SETTLEMENT_MISMATCH_INR
            discrepancy = SETTLEMENT_MISMATCH_INR
            has_mismatch = True
            status = 'partially_matched'
        
        s = Settlement(
            id=f'settle-{day_offset:04d}',
            merchant_id='merchant-bharat-001',
            settlement_ref=f'SETL-{uuid.uuid4().hex[:12].upper()}',
            gateway='razorpay',
            period_start=period_date.replace(tzinfo=timezone.utc),
            period_end=(period_date + timedelta(hours=23, minutes=59)).replace(tzinfo=timezone.utc),
            settlement_date=(period_date + timedelta(days=2)).replace(tzinfo=timezone.utc),
            gross_amount=Decimal(str(gross)),
            fees=Decimal(str(fees)),
            tax=Decimal(str(tax_amt)),
            refunds_total=Decimal(str(refunds_amt)),
            chargebacks_total=Decimal(str(cb_amt)),
            net_amount=Decimal(str(net)),
            expected_amount=Decimal(str(expected)),
            discrepancy=Decimal(str(discrepancy)),
            status=status,
            has_mismatch=has_mismatch
        )
        db.add(s)
        total_settlements += 1
    
    db.flush()
    
    # --- SUBSCRIPTIONS ---
    sub_customers = random.sample(customers, min(NUM_SUBSCRIPTIONS, len(customers)))
    plans = ['Basic Plan', 'Pro Plan', 'Enterprise Plan']
    plan_amounts = [999, 2999, 9999]
    for i, cust in enumerate(sub_customers):
        plan_idx = random.randint(0, 2)
        failed_att = random.choices([0, 1, 2, 3], weights=[0.65, 0.20, 0.10, 0.05])[0]
        sub = Subscription(
            id=f'sub-{i:05d}',
            merchant_id='merchant-bharat-001',
            customer_id=cust.id,
            plan_name=plans[plan_idx],
            status='failed' if failed_att >= 2 else ('active' if failed_att == 0 else 'paused'),
            amount=Decimal(str(plan_amounts[plan_idx])),
            billing_cycle='monthly',
            next_billing_date=(now + timedelta(days=random.randint(1, 30))).replace(tzinfo=timezone.utc),
            failed_attempts=failed_att,
            last_failed_at=(now - timedelta(days=random.randint(1, 10))).replace(tzinfo=timezone.utc) if failed_att > 0 else None,
            recovery_status='none' if failed_att == 0 else ('in_progress' if failed_att == 1 else 'abandoned')
        )
        db.add(sub)
    
    db.commit()
    
    summary = {
        'merchant': 'Bharat Commerce Pvt Ltd',
        'demo_user': 'demo@merchant.com / demo123',
        'customers': NUM_CUSTOMERS,
        'products': NUM_PRODUCTS,
        'transactions': total_transactions,
        'failed_payments': total_failed_payments,
        'chargebacks': total_chargebacks,
        'settlements': total_settlements,
        'subscriptions': NUM_SUBSCRIPTIONS,
        'anomalies_injected': [
            f'Gateway failure days {ANOMALY_START_DAY}-{ANOMALY_END_DAY}: failure rate {ANOMALY_FAILURE_RATE*100:.1f}%',
            f'Segment B chargeback rate: {SEGMENT_B_CB_RATE*100:.1f}% (baseline {BASELINE_CB_RATE*100:.1f}%)',
            f'Product X conversion: {PRODUCT_X_CONVERSION*100:.1f}% (baseline {BASELINE_CONVERSION*100:.1f}%)',
            f'Settlement day 60 mismatch: INR {SETTLEMENT_MISMATCH_INR:,}'
        ]
    }
    logger.info(f'Synthetic data generation complete: {summary}')
    return summary

def _hour_weights():
    # Higher traffic 9am-10pm
    weights = [1]*9 + [5,8,10,12,15,18,20,18,15,12,10,8,5,3,2,1,1,1]
    return weights[:24]

def _calc_recovery_prob(failure_reason: str, retry_count: int, risk_score: float, amount: float) -> float:
    base_probs = {
        'gateway_timeout': 0.72,
        'network_error': 0.68,
        'insufficient_funds': 0.35,
        'card_declined': 0.42,
        'expired_card': 0.15,
        'fraud_block': 0.05
    }
    p = base_probs.get(failure_reason, 0.4)
    p -= retry_count * 0.18
    p -= risk_score * 0.3
    if amount > 10000: p -= 0.08
    return max(0.0, min(0.95, p))

def _gateway_code(failure_reason: str) -> str:
    codes = {
        'gateway_timeout': 'GW_TIMEOUT',
        'network_error': 'NET_ERR',
        'insufficient_funds': 'INSUF_FUNDS',
        'card_declined': 'CARD_DECLINED',
        'expired_card': 'CARD_EXPIRED',
        'fraud_block': 'FRAUD_BLOCK',
        'none': 'SUCCESS'
    }
    return codes.get(failure_reason, 'ERR_UNKNOWN')
