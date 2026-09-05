from app.engines.recovery_scoring import calculate_recovery_probability, rank_candidates, calculate_recovery_metrics

def test_calculate_recovery_probability():
    prob_good = calculate_recovery_probability({'failure_reason': 'gateway_timeout', 'retry_count': 0, 'risk_score': 0.1})
    assert prob_good > 0.6
    
    prob_bad = calculate_recovery_probability({'failure_reason': 'expired_card', 'retry_count': 3, 'risk_score': 0.8})
    assert prob_bad < 0.3

def test_rank_candidates():
    candidates = [
        {'id': 'c1', 'failure_reason': 'gateway_timeout', 'retry_count': 0, 'risk_score': 0.1, 'amount': 1000.0},
        {'id': 'c2', 'failure_reason': 'insufficient_funds', 'retry_count': 0, 'risk_score': 0.2, 'amount': 500.0},
        {'id': 'c3', 'failure_reason': 'expired_card', 'retry_count': 2, 'risk_score': 0.3, 'amount': 2000.0},
        {'id': 'c4', 'failure_reason': 'gateway_timeout', 'retry_count': 0, 'risk_score': 0.7, 'amount': 1000.0},
        {'id': 'c5', 'failure_reason': 'gateway_timeout', 'retry_count': 0, 'risk_score': 0.1, 'amount': 0.0}
    ]
    
    results = rank_candidates(candidates)
    
    # Check expected recovery value exact calculation
    for c in results:
        assert round(c.expected_recovery_value, 2) == round(c.amount * c.recovery_probability, 2)
        
    # Check sorting
    assert results[0].expected_recovery_value >= results[1].expected_recovery_value
    
    # Ineligibility reasons
    c3 = next(c for c in results if c.payment_attempt_id == 'c3')
    assert not c3.is_eligible
    assert 'retry_count' in c3.exclusion_reason
    
    c4 = next(c for c in results if c.payment_attempt_id == 'c4')
    assert not c4.is_eligible
    assert 'risk_score' in c4.exclusion_reason
    
    c5 = next(c for c in results if c.payment_attempt_id == 'c5')
    assert c5.expected_recovery_value == 0.0

def test_calculate_recovery_metrics():
    candidates = [
        {'id': 'p1', 'failure_reason': 'gateway_timeout', 'retry_count': 0, 'risk_score': 0.1, 'amount': 100.0},
        {'id': 'p2', 'failure_reason': 'card_declined', 'retry_count': 0, 'risk_score': 0.2, 'amount': 200.0}
    ]
    scored = rank_candidates(candidates)
    metrics = calculate_recovery_metrics(scored)
    assert metrics['total_detected'] == len(candidates)
