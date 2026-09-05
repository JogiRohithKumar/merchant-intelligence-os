import pytest
import asyncio
from unittest.mock import patch
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.integrations.razorpay.client import razorpay_client
from app.integrations.razorpay.webhook import razorpay_webhook_handler
from app.policies.engine import policy_engine, PolicyDecision
from app.database.models.merchant import Merchant, MerchantStatus
from app.database.models.transaction import Transaction, TransactionStatus, TransactionType
from app.database.models.action import Action, ActionStatus
from app.database.models.audit_event import AuditEvent
from app.database.models.idempotency import IdempotencyKey
from app.core.security import create_access_token

client = TestClient(app)

# -------------------------------------------------------------
# 1. LIVE MODE SAFETY GATING TESTS
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_live_safety_gate_blocks_execution_when_disabled():
    """
    Ensure LIVE execution is strictly halted when AUTOMATED_EXECUTION_ENABLED is False,
    even if DATA_MODE is set to 'LIVE'.
    """
    with patch.object(settings, 'DATA_MODE', 'LIVE'), \
         patch.object(settings, 'DEMO_MODE', False), \
         patch.object(settings, 'AUTOMATED_EXECUTION_ENABLED', False), \
         patch.object(settings, 'RAZORPAY_KEY_ID', 'rzp_live_testkey123'), \
         patch.object(settings, 'RAZORPAY_KEY_SECRET', 'testsecret456'):
        
        res = await razorpay_client.execute_retry(
            transaction_id="tx_test_live_gate_001",
            amount=5000.0,
            merchant_id="merchant-test-live",
            idempotency_key="idemp_live_gate_001"
        )
        assert res['success'] is False
        assert res['status'] == 'BLOCKED_BY_SAFETY_GATE'
        assert 'AUTOMATED_EXECUTION_ENABLED is false' in res['error']

@pytest.mark.asyncio
async def test_live_safety_gate_blocks_execution_when_credentials_missing():
    """
    Ensure LIVE execution is strictly halted when Razorpay credentials are missing.
    """
    with patch.object(settings, 'DATA_MODE', 'LIVE'), \
         patch.object(settings, 'DEMO_MODE', False), \
         patch.object(settings, 'AUTOMATED_EXECUTION_ENABLED', True), \
         patch.object(settings, 'RAZORPAY_KEY_ID', None), \
         patch.object(settings, 'RAZORPAY_KEY_SECRET', None):
        
        res = await razorpay_client.execute_retry(
            transaction_id="tx_test_live_gate_002",
            amount=5000.0,
            merchant_id="merchant-test-live",
            idempotency_key="idemp_live_gate_002"
        )
        assert res['success'] is False
        assert res['status'] == 'BLOCKED_BY_SAFETY_GATE'
        assert 'RAZORPAY_KEY_ID' in res['missing_credentials']
        assert 'RAZORPAY_KEY_SECRET' in res['missing_credentials']

# -------------------------------------------------------------
# 2. WEBHOOK SECURITY & PROVENANCE TESTS
# -------------------------------------------------------------
def test_webhook_missing_signature_rejected(db_session):
    resp = client.post(
        "/api/v1/webhooks/razorpay",
        content=b'{"event":"payment.captured"}',
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 401

def test_webhook_malformed_json_rejected(db_session, demo_merchant):
    with patch.object(razorpay_webhook_handler, 'verify_signature', return_value=True):
        resp = client.post(
            "/api/v1/webhooks/razorpay",
            content=b'invalid-not-json-payload',
            headers={"X-Razorpay-Signature": "dummy_sig", "X-Merchant-Id": "test-merchant-001", "Content-Type": "application/json"}
        )
        assert resp.status_code == 400
        assert "malformed_json" in resp.json().get("detail", "") or "Invalid JSON" in resp.json().get("detail", "")

def test_webhook_header_event_id_deduplication(db_session, demo_merchant):
    """
    Verify x-razorpay-event-id is respected and deduplicated without creating duplicate transactions.
    """
    raw_payload = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_dedup_001","amount":150000,"currency":"INR"}}}}'
    headers = {
        "X-Razorpay-Signature": "valid_sig_mock",
        "X-Razorpay-Event-Id": "evt_unique_header_001",
        "X-Merchant-Id": "test-merchant-001",
        "Content-Type": "application/json"
    }

    with patch.object(razorpay_webhook_handler, 'verify_signature', return_value=True):
        # 1st ingestion
        resp1 = client.post("/api/v1/webhooks/razorpay", content=raw_payload, headers=headers)
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "processed"

        # 2nd ingestion of exact same header event ID
        resp2 = client.post("/api/v1/webhooks/razorpay", content=raw_payload, headers=headers)
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "duplicate"

        # Verify only 1 transaction exists with this gateway id
        txns = db_session.query(Transaction).filter(Transaction.gateway_transaction_id == "pay_dedup_001").all()
        assert len(txns) == 1
        assert txns[0].data_source == "LIVE_RAZORPAY"

# -------------------------------------------------------------
# 3. POLICY BYPASS ATTACK TESTS (EXACT BOUNDARIES)
# -------------------------------------------------------------
def test_policy_risk_score_boundary_precision():
    # 0.650000 -> ALLOW
    res_exact = policy_engine.evaluate('retry_payment', {'amount': 5000, 'risk_score': 0.650000, 'retry_count': 1})
    assert res_exact.decision == PolicyDecision.ALLOW.value

    # 0.649999 -> ALLOW
    res_below = policy_engine.evaluate('retry_payment', {'amount': 5000, 'risk_score': 0.649999, 'retry_count': 1})
    assert res_below.decision == PolicyDecision.ALLOW.value

    # 0.650001 -> REJECT
    res_above = policy_engine.evaluate('retry_payment', {'amount': 5000, 'risk_score': 0.650001, 'retry_count': 1})
    assert res_above.decision == PolicyDecision.REJECT.value
    assert 'risk_score_exceeds_threshold' in res_above.conditions_failed

def test_policy_amount_boundary_precision():
    # 10000.00 -> ALLOW
    res_exact = policy_engine.evaluate('retry_payment', {'amount': 10000.00, 'risk_score': 0.3, 'retry_count': 1})
    assert res_exact.decision == PolicyDecision.ALLOW.value

    # 10000.01 -> REQUIRE_APPROVAL
    res_above = policy_engine.evaluate('retry_payment', {'amount': 10000.01, 'risk_score': 0.3, 'retry_count': 1})
    assert res_above.decision == PolicyDecision.REQUIRE_APPROVAL.value
    assert 'amount_above_auto_limit' in res_above.conditions_failed

def test_policy_retry_count_boundary():
    # 2 -> ALLOW
    res_2 = policy_engine.evaluate('retry_payment', {'amount': 5000, 'risk_score': 0.3, 'retry_count': 2})
    assert res_2.decision == PolicyDecision.ALLOW.value

    # 3 -> REJECT
    res_3 = policy_engine.evaluate('retry_payment', {'amount': 5000, 'risk_score': 0.3, 'retry_count': 3})
    assert res_3.decision == PolicyDecision.REJECT.value

def test_policy_missing_mandatory_params_blocked():
    # Explicit None risk_score
    res_none_risk = policy_engine.evaluate('retry_payment', {'amount': 5000, 'risk_score': None, 'retry_count': 1})
    assert res_none_risk.decision == PolicyDecision.REJECT.value
    assert 'invalid_risk_score' in res_none_risk.conditions_failed

    # Explicit None retry_count
    res_none_retry = policy_engine.evaluate('retry_payment', {'amount': 5000, 'risk_score': 0.2, 'retry_count': None})
    assert res_none_retry.decision == PolicyDecision.REJECT.value
    assert 'invalid_retry_count' in res_none_retry.conditions_failed

    # Malformed non-numeric
    res_malformed = policy_engine.evaluate('retry_payment', {'amount': 'ten-thousand', 'risk_score': 0.2, 'retry_count': 1})
    assert res_malformed.decision == PolicyDecision.REJECT.value
    assert 'malformed_parameters' in res_malformed.conditions_failed


# -------------------------------------------------------------
# 4. HIGH CONCURRENCY IDEMPOTENCY (100 CONCURRENT REQUESTS)
# -------------------------------------------------------------
def test_idempotency_100_concurrent_burst(db_session):
    from concurrent.futures import ThreadPoolExecutor
    from app.policies.idempotency import IdempotencyChecker, generate_idempotency_key

    merchant_id = "test-merchant-burst"
    tx_id = "tx-burst-test-100"
    attempt = 1
    key = generate_idempotency_key(merchant_id, "retry_payment", f"{tx_id}:attempt_{attempt}")

    checker = IdempotencyChecker(db_session)
    results = []

    def attempt_acquire():
        # Each thread attempts to acquire the atomic lock
        return checker.acquire_lock(key, merchant_id, "retry_payment")

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(attempt_acquire) for _ in range(100)]
        for f in futures:
            results.append(f.result())

    # Exactly ONE thread must win the atomic lock
    assert results.count(True) == 1
    assert results.count(False) == 99

    # Next attempt with attempt_number=2 must succeed as a new legitimate action
    key_attempt_2 = generate_idempotency_key(merchant_id, "retry_payment", f"{tx_id}:attempt_2")
    assert checker.acquire_lock(key_attempt_2, merchant_id, "retry_payment") is True

# -------------------------------------------------------------
# 5. CRYPTOGRAPHIC TAMPER-EVIDENT HASH CHAIN & TAMPER DETECTION
# -------------------------------------------------------------
def test_tamper_evident_audit_chain_verification(db_session):
    import hashlib
    merchant_id = "test-merchant-audit"

    # Create 3 chained audit events
    h0 = "0000000000000000000000000000000000000000000000000000000000000000"
    
    # Event 1
    h1 = hashlib.sha256(f"{h0}|evt1".encode()).hexdigest()
    e1 = AuditEvent(
        id="aud-101",
        merchant_id=merchant_id,
        action="EXECUTE_RETRY_PAYMENT",
        prev_event_hash=h0,
        event_hash=h1
    )
    db_session.add(e1)

    # Event 2
    h2 = hashlib.sha256(f"{h1}|evt2".encode()).hexdigest()
    e2 = AuditEvent(
        id="aud-102",
        merchant_id=merchant_id,
        action="EXECUTE_RETRY_PAYMENT",
        prev_event_hash=h1,
        event_hash=h2
    )
    db_session.add(e2)

    # Event 3
    h3 = hashlib.sha256(f"{h2}|evt3".encode()).hexdigest()
    e3 = AuditEvent(
        id="aud-103",
        merchant_id=merchant_id,
        action="EXECUTE_RETRY_PAYMENT",
        prev_event_hash=h2,
        event_hash=h3
    )
    db_session.add(e3)

    # Seed User so get_current_user succeeds
    from app.database.models.user import User, UserRole
    from app.core.security import get_password_hash
    usr = User(
        id="u-audit-admin",
        email="a@m.com",
        hashed_password=get_password_hash("pass123"),
        full_name="Audit Admin",
        role=UserRole.merchant_admin,
        merchant_id=merchant_id
    )
    db_session.add(usr)
    db_session.commit()

    # Verify chain initially intact
    token = create_access_token({"user_id": "u-audit-admin", "merchant_id": merchant_id, "role": "merchant_admin", "email": "a@m.com"})
    resp_valid = client.get("/api/v1/audit/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp_valid.status_code == 200
    assert resp_valid.json()["is_valid"] is True
    assert resp_valid.json()["tamper_detected"] is False

    # Simulate Malicious Tamper on Event #2
    e2.event_hash = "tampered_malicious_hash_value_1234567890abcdef"
    db_session.commit()

    # Verify chain tampering is immediately detected
    resp_tampered = client.get("/api/v1/audit/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp_tampered.status_code == 200
    assert resp_tampered.json()["is_valid"] is False
    assert resp_tampered.json()["tamper_detected"] is True
    assert resp_tampered.json()["broken_at_index"] == 2
