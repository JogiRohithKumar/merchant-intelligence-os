import pytest
import hmac
import hashlib
import json
from app.integrations.razorpay.webhook import razorpay_webhook_handler
from app.database.models.webhook_event import WebhookEvent
from app.database.models.transaction import Transaction, TransactionStatus

def test_w01_valid_signature_ingestion(db_session):
    secret = 'test-secret-key-123'
    payload = {
        'id': 'evt_valid_001',
        'event': 'payment.captured',
        'payload': {
            'payment': {
                'entity': {
                    'id': 'pay_sig_ok_001',
                    'amount': 150000,
                    'currency': 'INR',
                    'method': 'upi'
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode('utf-8')
    valid_sig = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()

    ok = razorpay_webhook_handler.verify_signature(raw_body, valid_sig, secret)
    assert ok is True

    success, status, result = razorpay_webhook_handler.ingest_event(
        db_session, raw_body, valid_sig, merchant_id='merchant-bharat-001', secret=secret
    )
    assert success is True
    assert status == 'processed'

    # Verify transaction in DB
    tx = db_session.query(Transaction).filter(Transaction.gateway_transaction_id == 'pay_sig_ok_001').first()
    assert tx is not None
    assert tx.status == TransactionStatus.success

def test_w02_invalid_signature_detection():
    secret = 'test-secret-key-123'
    raw_body = b'{"event": "payment.failed"}'
    fake_sig = 'tampered-signature-invalid-hash'

    ok = razorpay_webhook_handler.verify_signature(raw_body, fake_sig, secret)
    assert ok is False

def test_w03_failed_payment_event_normalization(db_session):
    payload = {
        'id': 'evt_fail_norm_001',
        'event': 'payment.failed',
        'payload': {
            'payment': {
                'entity': {
                    'id': 'pay_fail_002',
                    'amount': 320000,
                    'currency': 'INR',
                    'error_code': 'gateway_timeout'
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode('utf-8')
    success, status, result = razorpay_webhook_handler.ingest_event(
        db_session, raw_body, signature='', merchant_id='merchant-bharat-001'
    )
    assert success is True
    assert status == 'processed'

    tx = db_session.query(Transaction).filter(Transaction.gateway_transaction_id == 'pay_fail_002').first()
    assert tx is not None
    assert tx.status == TransactionStatus.failed
