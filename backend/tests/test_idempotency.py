from app.policies.idempotency import generate_idempotency_key, IdempotencyChecker
import uuid

def test_generate_idempotency_key():
    params = {'amount': 100}
    key1 = generate_idempotency_key('m1', 'retry_payment', params)
    key2 = generate_idempotency_key('m1', 'retry_payment', params)
    assert key1 == key2
    
    key3 = generate_idempotency_key('m2', 'retry_payment', params)
    assert key1 != key3
    
    key4 = generate_idempotency_key('m1', 'create_campaign', params)
    assert key1 != key4
    
    assert len(key1) == 64  # SHA-256 hex is 64 chars

def test_idempotency_checker(test_db):
    checker = IdempotencyChecker(test_db)
    key = str(uuid.uuid4().hex) * 2  # 64 chars
    
    exists, record = checker.check(key)
    assert exists is False
    assert record is None
    
    # Create an idempotency record in db
    from app.database.models.idempotency import IdempotencyKey
    ik = IdempotencyKey(key=key, merchant_id='m1', action_type='test', status='SUCCESS')
    test_db.add(ik)
    test_db.commit()
    
    exists, record = checker.check(key)
    assert exists is True
    assert record['status'] == 'SUCCESS'
