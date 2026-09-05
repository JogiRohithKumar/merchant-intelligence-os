import pytest
import concurrent.futures
from app.policies.idempotency import IdempotencyChecker, generate_idempotency_key
from app.database.models.idempotency import IdempotencyKey

def test_i01_duplicate_action_detected(db_session):
    checker = IdempotencyChecker(db_session)
    key = generate_idempotency_key('merchant-bharat-001', 'retry_payment', {'tx_id': 'tx_12345'})
    
    # First check: not duplicate
    is_dup, _ = checker.check(key)
    assert is_dup is False
    
    # Acquire lock and mark SUCCESS
    acquired = checker.acquire_lock(key, 'merchant-bharat-001', 'retry_payment')
    assert acquired is True
    checker.release_lock(key, 'SUCCESS')
    
    # Second check: duplicate detected
    is_dup2, record = checker.check(key)
    assert is_dup2 is True
    assert record['status'] == 'SUCCESS'

def test_i02_concurrent_duplicate_action_single_winner(db_session):
    checker = IdempotencyChecker(db_session)
    key = generate_idempotency_key('merchant-bharat-001', 'retry_payment', {'tx_id': 'tx_concurrent_99'})
    
    results = []
    def attempt_acquire():
        # Each thread attempts to acquire the lock
        return checker.acquire_lock(key, 'merchant-bharat-001', 'retry_payment')

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(attempt_acquire) for _ in range(5)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # Exactly one thread must have acquired the lock
    assert sum(1 for r in results if r is True) == 1
    assert sum(1 for r in results if r is False) == 4

def test_i03_duplicate_webhook_deduplication(db_session):
    from app.integrations.razorpay.webhook import razorpay_webhook_handler
    import json
    
    raw_payload = {
        'id': 'evt_test_dedup_001',
        'event': 'payment.captured',
        'payload': {
            'payment': {
                'entity': {
                    'id': 'pay_test_dedup_100',
                    'amount': 250000,
                    'currency': 'INR',
                    'method': 'upi'
                }
            }
        }
    }
    raw_bytes = json.dumps(raw_payload).encode('utf-8')
    
    # Ingest first time
    ok1, status1, res1 = razorpay_webhook_handler.ingest_event(
        db_session, raw_bytes, signature='', merchant_id='merchant-bharat-001'
    )
    assert ok1 is True
    assert status1 == 'processed'
    
    # Ingest second time with exact same event ID
    ok2, status2, res2 = razorpay_webhook_handler.ingest_event(
        db_session, raw_bytes, signature='', merchant_id='merchant-bharat-001'
    )
    assert ok2 is True
    assert status2 == 'duplicate'
