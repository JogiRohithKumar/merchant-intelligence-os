from app.engines.growth_simulation import simulate_campaign

def test_simulate_campaign():
    params = {
        'target_count': 10000,
        'budget': 50000.0,
        'campaign_type': 'reactivation'
    }
    historical_data = {
        'current_conversion': 0.038,
        'avg_order_value': 2500,
        'segment_risk_rate': 0.1
    }
    
    res1 = simulate_campaign(params, historical_data, seed=42)
    res2 = simulate_campaign(params, historical_data, seed=42)
    
    assert res1.expected_revenue == res2.expected_revenue
    assert res1.treatment_conversion > res1.control_conversion
    assert res1.risk_exclusions > 0
    assert 0.0 <= res1.p_value <= 1.0
    assert res1.expected_revenue > 0
