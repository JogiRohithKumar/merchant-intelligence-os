import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint_healthy(test_db):
    """Verify health endpoint responds with database connected and valid telemetry."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "data_mode" in data

def test_readiness_endpoint(test_db):
    """Verify readiness endpoint."""
    client = TestClient(app)
    response = client.get("/api/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"
    assert data["database"] == "READY"

def test_fresh_user_registration_has_no_default_merchant(test_db):
    """
    CRITICAL: Verify newly registered user starts with merchant_id = None
    and onboarding_required = True. NEVER defaults to Bharat Commerce.
    """
    client = TestClient(app)
    unique_email = f"operator_{uuid.uuid4().hex[:8]}@acme.io"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "SecurePassword123!",
        "full_name": "Acme Operator"
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    token = reg_data["access_token"]
    user = reg_data["user"]
    
    assert user["merchant_id"] is None
    assert user["merchant_name"] is None
    assert user["onboarding_required"] is True

    # Check /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["merchant_id"] is None
    assert me_data["merchant_name"] is None
    assert me_data["onboarding_required"] is True

def test_merchant_creation_and_zero_data_isolation(test_db):
    """
    Verify newly created merchant has 0 transactions, 0 recoverable, 0 risk,
    and cannot see Bharat Commerce or another merchant's data.
    """
    client = TestClient(app)
    unique_email = f"merchant_{uuid.uuid4().hex[:8]}@solostore.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "SecurePassword123!",
        "full_name": "Solo Store Founder"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create new merchant organization
    mch_res = client.post("/api/v1/onboarding/create-merchant", headers=headers, json={
        "name": "Solo Store Online",
        "business_type": "ecommerce",
        "country": "IN",
        "currency": "INR"
    })
    assert mch_res.status_code == 200
    mch_data = mch_res.json()
    assert mch_data["status"] in ["created", "success"]
    new_mch_id = mch_data["merchant"]["id"]
    assert new_mch_id != "merchant-bharat-001"

    # Verify Dashboard metrics for this fresh merchant
    dash_res = client.get("/api/v1/merchant/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["merchant_name"] == "Solo Store Online"
    assert dash_data["total_transactions"] == 0
    assert dash_data["current_revenue"] == 0.0
    assert dash_data["recoverable_revenue"] == 0.0
    assert dash_data["risk_exposure"] == 0.0
    assert dash_data["settlement_exceptions"] == 0.0

    # Verify Transactions endpoint for fresh merchant
    tx_res = client.get("/api/v1/transactions", headers=headers)
    assert tx_res.status_code == 200
    assert tx_res.json()["total"] == 0
    assert tx_res.json()["items"] == []

    # Verify Recovery candidates endpoint for fresh merchant
    rec_res = client.get("/api/v1/recovery/candidates", headers=headers)
    assert rec_res.status_code == 200
    assert rec_res.json()["candidates"] == []

    # Verify Growth metrics endpoint
    growth_res = client.get("/api/v1/growth/metrics", headers=headers)
    assert growth_res.status_code == 200
    assert growth_res.json()["total_transactions"] == 0
    assert growth_res.json()["conversion_rate"] == 0.0

def test_password_reset_flow(test_db):
    """Verify forgot-password token generation and reset-password completion."""
    client = TestClient(app)
    email = f"pwd_user_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "OldPassword123!",
        "full_name": "Reset Test User"
    })

    # Request reset token
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    token = forgot_res.json()["reset_token"]
    assert token is not None

    # Complete reset
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "NewSecurePassword456!"
    })
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"

    # Login with new password
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "NewSecurePassword456!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

def test_webhook_requires_merchant_id_header(test_db):
    """Verify webhook rejects requests without valid X-Merchant-ID header."""
    client = TestClient(app)
    # Missing header
    res_no_hdr = client.post("/api/v1/webhooks/razorpay", headers={"X-Razorpay-Signature": "dummy_sig"}, json={"event": "payment.captured"})
    assert res_no_hdr.status_code == 400
    assert "Missing required X-Merchant-ID" in res_no_hdr.json()["detail"]

    # Non-existent merchant
    res_fake_mch = client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Merchant-ID": "non_existent_merchant_999", "X-Razorpay-Signature": "dummy_sig"},
        json={"event": "payment.captured"}
    )
    assert res_fake_mch.status_code == 404
