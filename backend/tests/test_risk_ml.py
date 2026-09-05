from app.engines.risk_ml import train_risk_model, score_transaction, RiskScore

def test_train_risk_model():
    metrics = train_risk_model()
    assert hasattr(metrics, 'precision')
    assert hasattr(metrics, 'recall')
    assert hasattr(metrics, 'auc')
    assert hasattr(metrics, 'confusion_matrix')
    assert hasattr(metrics, 'n_test_samples')
    
    assert 0.0 <= metrics.precision <= 1.0
    assert 0.0 <= metrics.recall <= 1.0
    assert metrics.auc > 0.5
    assert len(metrics.confusion_matrix) == 2
    assert len(metrics.confusion_matrix[0]) == 2
    assert metrics.confusion_matrix[0][0] >= 0
    assert metrics.n_test_samples > 1000

def test_score_transaction():
    high_risk_tx = {
        'amount': 50000,
        'country': 'NG',
        'hour_of_day': 3,
        'is_new_device': True,
        'ip_velocity': 5,
        'customer_age_days': 2,
        'payment_method': 'card',
        'velocity_1h': 4,
        'historical_chargebacks': 2,
        'refund_rate': 0.25,
        'is_weekend': False,
        'is_anomaly_day': True
    }
    low_risk_tx = {
        'amount': 500,
        'country': 'IN',
        'hour_of_day': 14,
        'is_new_device': False,
        'ip_velocity': 1,
        'customer_age_days': 365,
        'payment_method': 'upi',
        'velocity_1h': 1,
        'historical_chargebacks': 0,
        'refund_rate': 0.01,
        'is_weekend': False,
        'is_anomaly_day': False
    }
    
    high_res = score_transaction(high_risk_tx)
    low_res = score_transaction(low_risk_tx)
    
    assert isinstance(high_res, RiskScore)
    assert 0.0 <= high_res.score <= 1.0
    assert 0.0 <= low_res.score <= 1.0
    assert high_res.score > low_res.score
