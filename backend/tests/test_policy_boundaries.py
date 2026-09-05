import pytest
from app.policies.engine import PolicyEngine

@pytest.fixture
def policy():
    return PolicyEngine()

def test_p01_risk_below_threshold(policy):
    # risk = 0.64 -> ALLOW
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.64, 'amount': 5000, 'retry_count': 1})
    assert res.decision == 'ALLOW'

def test_p02_risk_exact_threshold(policy):
    # risk = 0.65 -> ALLOW
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.65, 'amount': 5000, 'retry_count': 1})
    assert res.decision == 'ALLOW'

def test_p03_risk_above_threshold(policy):
    # risk = 0.66 -> REJECT
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.66, 'amount': 5000, 'retry_count': 1})
    assert res.decision == 'REJECT'
    assert 'risk_score_exceeds_threshold' in res.conditions_failed

def test_p04_amount_below_limit(policy):
    # amount = 9999 -> ALLOW
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.1, 'amount': 9999, 'retry_count': 1})
    assert res.decision == 'ALLOW'

def test_p05_amount_exact_limit(policy):
    # amount = 10000 -> ALLOW
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.1, 'amount': 10000, 'retry_count': 1})
    assert res.decision == 'ALLOW'

def test_p06_amount_above_limit(policy):
    # amount = 10001 -> REQUIRE_APPROVAL
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.1, 'amount': 10001, 'retry_count': 1})
    assert res.decision == 'REQUIRE_APPROVAL'
    assert 'amount_above_auto_limit' in res.conditions_failed

def test_p07_retry_within_limit(policy):
    # retry = 1 -> ALLOW
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.1, 'amount': 5000, 'retry_count': 1})
    assert res.decision == 'ALLOW'

def test_p08_retry_at_limit(policy):
    # retry = 2 -> ALLOW
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.1, 'amount': 5000, 'retry_count': 2})
    assert res.decision == 'ALLOW'

def test_p09_retry_above_limit(policy):
    # retry = 3 -> REJECT
    res = policy.evaluate(action_type='retry_payment', context={'risk_score': 0.1, 'amount': 5000, 'retry_count': 3})
    assert res.decision == 'REJECT'
    assert any('retry' in c for c in res.conditions_failed)

def test_p10_prohibited_action(policy):
    for action in ['freeze_merchant_account', 'unilateral_fee_change', 'wipe_ledger']:
        res = policy.evaluate(action_type=action, context={})
        assert res.decision == 'REJECT'
        assert 'prohibited_action' in res.conditions_failed
