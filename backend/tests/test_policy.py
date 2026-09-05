from app.policies.engine import PolicyEngine

def test_policy_engine():
    engine = PolicyEngine()
    
    # retry_payment
    res1 = engine.evaluate(action_type='retry_payment', context={'retry_count': 0, 'amount': 5000})
    assert res1.decision == 'ALLOW'
    
    res2 = engine.evaluate(action_type='retry_payment', context={'retry_count': 3, 'amount': 5000})
    assert res2.decision == 'REJECT'
    assert any('retry' in cond.lower() for cond in res2.conditions_failed)
    
    res3 = engine.evaluate(action_type='retry_payment', context={'retry_count': 0, 'amount': 50000})
    assert res3.decision == 'REQUIRE_APPROVAL'
    
    # create_campaign
    res4 = engine.evaluate(action_type='create_campaign', context={'budget': 500000})
    assert res4.decision == 'REQUIRE_APPROVAL'
    
    res5 = engine.evaluate(action_type='create_campaign', context={'budget': 25000})
    assert res5.decision == 'ALLOW'
    
    # unknown action type
    res6 = engine.evaluate(action_type='unknown_action', context={})
    assert res6.decision == 'REJECT'
    
    # read-only
    for action in ['reconcile', 'forecast_cash', 'get_transactions']:
        res = engine.evaluate(action_type=action, context={})
        assert res.decision == 'ALLOW'
        
    # suspended merchant
    res7 = engine.evaluate(action_type='retry_payment', context={'retry_count': 0, 'amount': 500, 'is_suspended': True})
    assert res7.decision == 'REJECT'
    assert len(res7.conditions_failed) > 0
