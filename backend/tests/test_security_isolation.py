import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.database.models.transaction import Transaction, TransactionStatus, TransactionType
from app.database.models.merchant import Merchant, MerchantStatus
from app.database.models.action import Action, ActionStatus
from decimal import Decimal

client = TestClient(app)

from app.database.models.user import User, UserRole
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_merchants(db_session):
    # Ensure Merchant A and Merchant B exist
    ma = db_session.query(Merchant).filter(Merchant.id == 'merchant-alpha-001').first()
    if not ma:
        ma = Merchant(id='merchant-alpha-001', name='Merchant Alpha', status=MerchantStatus.active)
        db_session.add(ma)
    
    mb = db_session.query(Merchant).filter(Merchant.id == 'merchant-beta-002').first()
    if not mb:
        mb = Merchant(id='merchant-beta-002', name='Merchant Beta', status=MerchantStatus.active)
        db_session.add(mb)

    # Seed users
    ua = db_session.query(User).filter(User.id == 'user-alpha-001').first()
    if not ua:
        ua = User(
            id='user-alpha-001',
            email='alpha@merchant.com',
            hashed_password=get_password_hash('testpass123'),
            full_name='Alpha Admin',
            role=UserRole.merchant_admin,
            merchant_id='merchant-alpha-001'
        )
        db_session.add(ua)

    ub = db_session.query(User).filter(User.id == 'user-beta-viewer').first()
    if not ub:
        ub = User(
            id='user-beta-viewer',
            email='viewer@beta.com',
            hashed_password=get_password_hash('testpass123'),
            full_name='Beta Viewer',
            role=UserRole.finance_user,
            merchant_id='merchant-beta-002'
        )
        db_session.add(ub)

    # Add transaction belonging to Merchant B
    tx_b = db_session.query(Transaction).filter(Transaction.id == 'tx-secret-beta-999').first()
    if not tx_b:
        tx_b = Transaction(
            id='tx-secret-beta-999',
            merchant_id='merchant-beta-002',
            amount=Decimal('5000.00'),
            status=TransactionStatus.success,
            transaction_type=TransactionType.payment
        )
        db_session.add(tx_b)

    # Add action belonging to Merchant B
    act_b = db_session.query(Action).filter(Action.id == 'act-secret-beta-777').first()
    if not act_b:
        act_b = Action(
            id='act-secret-beta-777',
            workflow_id='wf-beta-001',
            merchant_id='merchant-beta-002',
            action_type='retry_payment',
            idempotency_key='idemp-beta-unique-777',
            status=ActionStatus.PENDING_APPROVAL,
            amount_at_risk=5000.0
        )
        db_session.add(act_b)

    db_session.commit()


def test_s01_cross_merchant_access_blocked():
    # Token for Merchant Alpha
    token_a = create_access_token({
        'user_id': 'user-alpha-001',
        'merchant_id': 'merchant-alpha-001',
        'role': 'merchant_admin',
        'email': 'alpha@merchant.com'
    })
    headers = {'Authorization': f'Bearer {token_a}'}

    # Merchant Alpha attempts to inspect Merchant Beta's transaction
    resp = client.get('/api/v1/transactions/tx-secret-beta-999', headers=headers)
    assert resp.status_code in [404, 200]
    if resp.status_code == 200:
        # Should return error Not found
        assert 'error' in resp.json() or resp.json().get('id') != 'tx-secret-beta-999'

def test_s02_unauthorized_approval_blocked():
    # User from Merchant Beta but with read-only role 'finance_user'
    token_viewer = create_access_token({
        'user_id': 'user-beta-viewer',
        'merchant_id': 'merchant-beta-002',
        'role': 'finance_user',
        'email': 'viewer@beta.com'
    })
    headers = {'Authorization': f'Bearer {token_viewer}'}

    # Attempt to approve action requiring admin
    resp = client.post('/api/v1/actions/act-secret-beta-777/approve', headers=headers)
    assert resp.status_code == 403
    assert 'Unauthorized' in resp.json()['detail']

def test_s03_expired_jwt_blocked():
    # Create expired token (-10 minutes)
    expired_token = create_access_token(
        {
            'user_id': 'user-alpha-001',
            'merchant_id': 'merchant-alpha-001',
            'role': 'merchant_admin',
            'email': 'alpha@merchant.com'
        },
        expires_delta=timedelta(minutes=-10)
    )
    headers = {'Authorization': f'Bearer {expired_token}'}
    resp = client.get('/api/v1/transactions', headers=headers)
    assert resp.status_code == 401

def test_s04_invalid_jwt_blocked():
    headers = {'Authorization': 'Bearer invalid-garbage-token-tampered'}
    resp = client.get('/api/v1/transactions', headers=headers)
    assert resp.status_code == 401

def test_s05_cross_tenant_action_approval_blocked():
    # Merchant Alpha attempts to approve Merchant Beta's action
    token_a = create_access_token({
        'user_id': 'user-alpha-001',
        'merchant_id': 'merchant-alpha-001',
        'role': 'merchant_admin',
        'email': 'alpha@merchant.com'
    })
    headers = {'Authorization': f'Bearer {token_a}'}

    resp = client.post('/api/v1/actions/act-secret-beta-777/approve', headers=headers)
    assert resp.status_code == 404  # Merchant A cannot even see Merchant B's action
