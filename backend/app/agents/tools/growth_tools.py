from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.logging import get_logger

logger = get_logger('tools.growth')

def get_conversion_metrics(db: Session, merchant_id: str, start_date: datetime = None, end_date: datetime = None) -> dict:
    from app.database.models.transaction import Transaction
    from app.database.models.order import Order
    
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)
    
    # Current period
    total_txns = db.query(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.created_at.between(start_date, end_date)
    ).scalar() or 0
    
    success_txns = db.query(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == 'success',
        Transaction.created_at.between(start_date, end_date)
    ).scalar() or 0
    
    avg_order_value = db.query(func.avg(Transaction.amount)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == 'success',
        Transaction.created_at.between(start_date, end_date)
    ).scalar() or 0
    
    conversion_rate = (success_txns / total_txns) if total_txns > 0 else 0.0
    
    # Previous period for comparison
    period_len = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_len)
    prev_total = db.query(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.created_at.between(prev_start, start_date)
    ).scalar() or 0
    prev_success = db.query(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == 'success',
        Transaction.created_at.between(prev_start, start_date)
    ).scalar() or 0
    prev_conversion = prev_success / prev_total if prev_total > 0 else 0
    
    return {
        'conversion_rate': round(conversion_rate * 100, 3),  # as %
        'previous_conversion_rate': round(prev_conversion * 100, 3),
        'change_pct': round((conversion_rate - prev_conversion) / prev_conversion * 100 if prev_conversion > 0 else 0, 2),
        'avg_order_value': round(float(avg_order_value), 2),
        'total_transactions': total_txns,
        'successful_transactions': success_txns,
        'period_days': period_len
    }

def get_product_conversion_analysis(db: Session, merchant_id: str, days: int = 30) -> list[dict]:
    from app.database.models.product import Product
    
    products = db.query(Product).filter(
        Product.merchant_id == merchant_id,
        Product.is_active == True
    ).limit(50).all()
    
    return [{
        'id': p.id, 'name': p.name, 'category': p.category, 'sku': p.sku,
        'conversion_rate': p.conversion_rate * 100,  # as %
        'avg_order_value': p.avg_order_value,
        'baseline_conversion': 4.2,  # ground truth baseline
        'change_pct': round((p.conversion_rate - 0.042) / 0.042 * 100, 2),
        'is_anomalous': p.is_anomalous,
        'status': 'low_conversion' if p.conversion_rate < 0.025 else 'normal'
    } for p in products]

def get_segment_repeat_rate(db: Session, merchant_id: str, days: int = 30) -> dict:
    from app.database.models.customer import Customer
    from app.database.models.transaction import Transaction
    from sqlalchemy import case
    
    results = {}
    for seg in ['A', 'B', 'C', 'D']:
        seg_customers = db.query(func.count(Customer.id)).filter(
            Customer.merchant_id == merchant_id,
            Customer.segment == seg
        ).scalar() or 1
        
        repeat = db.query(func.count(Transaction.id)).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.status == 'success',
            Transaction.created_at >= datetime.now(timezone.utc) - timedelta(days=days)
        ).join(Customer, Transaction.customer_id == Customer.id).filter(
            Customer.segment == seg,
            Customer.total_orders > 1
        ).scalar() or 0
        
        results[seg] = round(repeat / seg_customers, 4)
    return results
