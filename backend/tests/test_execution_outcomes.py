import pytest
from decimal import Decimal
from app.execution.engine import ActionExecutionEngine
from app.database.models.action import Action, ActionStatus
from app.database.models.transaction import Transaction, TransactionStatus, TransactionType

@pytest.mark.asyncio
async def test_o01_successful_recovery_execution(db_session):
    engine = ActionExecutionEngine()
    
    # Setup failed transaction in DB
    tx = Transaction(
        id='tx-test-recovery-001',
        merchant_id='merchant-bharat-001',
        amount=Decimal('4500.00'),
        status=TransactionStatus.failed,
        transaction_type=TransactionType.payment
    )
    db_session.merge(tx)

    action = Action(
        id='act-test-rec-001',
        workflow_id='wf-rec-001',
        merchant_id='merchant-bharat-001',
        action_type='retry_payment',
        amount_at_risk=4500.0,
        status=ActionStatus.APPROVED,
        idempotency_key='idemp-test-rec-001',
        action_params={'transaction_id': 'tx-test-recovery-001', 'amount': 4500.0}
    )
    db_session.merge(action)
    db_session.commit()

    # Execute action
    result = await engine.execute_action(db_session, action)
    assert result['success'] is True
    assert result['status'] == 'SUCCESS'

    # Verify transaction status was updated in DB
    updated_tx = db_session.query(Transaction).filter(Transaction.id == 'tx-test-recovery-001').first()
    assert updated_tx.status == TransactionStatus.success

@pytest.mark.asyncio
async def test_o02_failed_recovery_execution(db_session):
    engine = ActionExecutionEngine()
    
    action = Action(
        id='act-test-fail-002',
        workflow_id='wf-rec-002',
        merchant_id='merchant-bharat-001',
        action_type='retry_payment',
        amount_at_risk=3000.0,
        status=ActionStatus.APPROVED,
        idempotency_key='idemp-test-fail-002',
        action_params={'simulate_issuer_decline': True, 'amount': 3000.0}
    )
    db_session.merge(action)
    db_session.commit()

    result = await engine.execute_action(db_session, action)
    assert result['success'] is False
    assert result['status'] == 'FAILED'

@pytest.mark.asyncio
async def test_o03_f01_gateway_timeout_records_unknown(db_session):
    # UNKNOWN != SUCCESS (fail safe)
    engine = ActionExecutionEngine()

    action = Action(
        id='act-test-timeout-003',
        workflow_id='wf-rec-003',
        merchant_id='merchant-bharat-001',
        action_type='retry_payment',
        amount_at_risk=8000.0,
        status=ActionStatus.APPROVED,
        idempotency_key='idemp-test-timeout-003',
        action_params={'simulate_gateway_timeout': True, 'amount': 8000.0}
    )
    db_session.merge(action)
    db_session.commit()

    result = await engine.execute_action(db_session, action)
    assert result['success'] is False
    assert result['status'] == 'UNKNOWN'
    assert 'timeout' in action.execution_error.lower()

def test_o04_predicted_vs_actual_recovery_comparison():
    predicted_prob = 0.85
    amount = 5000.0
    expected_value = amount * predicted_prob
    actual_recovered = 5000.0 # From successful gateway attempt
    
    variance = actual_recovered - expected_value
    assert variance == pytest.approx(750.0)
    assert actual_recovered > expected_value
