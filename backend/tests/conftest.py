import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('JWT_SECRET', 'test-secret-key-for-testing')
os.environ.setdefault('DEMO_MODE', 'true')

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from app.database.base import Base
from app.database.models import *
from app.core.security import get_password_hash, create_access_token

@pytest.fixture(scope='function')
def test_db():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    
    @event.listens_for(engine, 'connect')
    def set_pragmas(dbapi_conn, conn_record):
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA foreign_keys=OFF')  # OFF for easier testing
        cursor.close()
    
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()
    from app.database.session import get_db
    from app.main import app
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield db
    finally:
        app.dependency_overrides.pop(get_db, None)
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope='function')
def db_session(test_db):
    return test_db



@pytest.fixture
def demo_merchant(test_db):
    from app.database.models.merchant import Merchant
    m = Merchant(id='test-merchant-001', name='Test Merchant', country='IN', currency='INR', status='active', monthly_revenue_baseline=Decimal('1000000'))
    test_db.add(m)
    test_db.commit()
    return m

@pytest.fixture
def demo_user(test_db, demo_merchant):
    from app.database.models.user import User
    u = User(id='test-user-001', email='test@merchant.com', hashed_password=get_password_hash('testpass123'), full_name='Test User', role='merchant_admin', merchant_id='test-merchant-001')
    test_db.add(u)
    test_db.commit()
    return u

@pytest.fixture
def auth_headers(demo_user):
    token = create_access_token({'user_id': demo_user.id, 'merchant_id': demo_user.merchant_id, 'role': demo_user.role.value, 'email': demo_user.email})
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def demo_transactions(test_db, demo_merchant):
    from app.database.models.transaction import Transaction
    from app.database.models.customer import Customer
    c = Customer(id='test-cust-001', merchant_id='test-merchant-001', email='c@test.com', full_name='Test Customer', risk_score=0.1)
    test_db.add(c)
    now = datetime.now(timezone.utc)
    txns = []
    for i in range(20):
        t = Transaction(id=f'txn-test-{i:03d}', merchant_id='test-merchant-001', customer_id='test-cust-001', amount=Decimal(str(1000 + i * 500)), currency='INR', status='success', gateway='razorpay', gateway_transaction_id=f'gw-test-{i:03d}', payment_method='upi', country='IN', risk_score=0.1, created_at=now - timedelta(days=i))
        txns.append(t)
        test_db.add(t)
    for i in range(10):
        t = Transaction(id=f'txn-fail-{i:03d}', merchant_id='test-merchant-001', customer_id='test-cust-001', amount=Decimal(str(2000 + i * 300)), currency='INR', status='failed', gateway='razorpay', gateway_transaction_id=f'gw-fail-{i:03d}', payment_method='card', country='IN', risk_score=0.3, created_at=now - timedelta(days=i))
        txns.append(t)
        test_db.add(t)
    test_db.commit()
    return txns

@pytest.fixture
def demo_failed_payments(test_db, demo_transactions):
    from app.database.models.payment_attempt import PaymentAttempt
    attempts = []
    now = datetime.now(timezone.utc)
    for i in range(10):
        a = PaymentAttempt(id=f'pa-test-{i:03d}', transaction_id=f'txn-fail-{i:03d}', merchant_id='test-merchant-001', attempt_number=1, status='failed', failure_reason='gateway_timeout' if i < 5 else 'card_declined', amount=Decimal(str(2000 + i * 300)), gateway='razorpay', risk_score=0.3, is_retry=False, recovery_probability=0.65 if i < 5 else 0.4, expected_recovery_value=(2000 + i * 300) * (0.65 if i < 5 else 0.4), created_at=now - timedelta(days=i))
        attempts.append(a)
        test_db.add(a)
    test_db.commit()
    return attempts
