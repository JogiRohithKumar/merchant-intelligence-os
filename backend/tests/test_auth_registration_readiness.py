import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.models.user import User, UserRole
from app.database.models.merchant import Merchant

client = TestClient(app)

def test_auth_registration_success(db_session):
    """Verify new user registration starts with no default merchant and requires onboarding."""
    payload = {
        "email": "new.merchant.user@example.com",
        "password": "StrongPassword123!",
        "full_name": "Ramesh Patel",
        "role": "operator"
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "access_token" in data
    assert data["user"]["email"] == "new.merchant.user@example.com"
    assert data["user"]["onboarding_required"] is True
    assert data["user"]["merchant_id"] is None

    # Verify persisted in database
    u = db_session.query(User).filter(User.email == "new.merchant.user@example.com").first()
    assert u is not None
    assert u.full_name == "Ramesh Patel"
    assert u.hashed_password != "StrongPassword123!"

def test_auth_registration_duplicate_blocked(db_session):
    """Verify duplicate email registration is rejected with 400 Bad Request."""
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
        "full_name": "First User"
    }
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 200

    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["detail"]

def test_new_user_merchant_creation_onboarding(db_session):
    """Verify brand-new user completes onboarding by creating their own isolated merchant."""
    reg_payload = {
        "email": "fresh.founder@acme.com",
        "password": "StrongPassword123!",
        "full_name": "Fresh Founder"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Dashboard should report has_merchant = False
    dash_resp = client.get("/api/v1/merchant/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    assert dash_resp.json()["has_merchant"] is False

    # Create new merchant via /api/v1/auth/onboarding/create-merchant
    mch_payload = {
        "name": "Acme Superstore Pvt Ltd",
        "business_type": "retail",
        "country": "IN",
        "currency": "INR"
    }
    mch_resp = client.post("/api/v1/auth/onboarding/create-merchant", json=mch_payload, headers=headers)
    assert mch_resp.status_code == 200
    mch_data = mch_resp.json()["merchant"]
    assert mch_data["name"] == "Acme Superstore Pvt Ltd"

    # Refresh headers with new token
    new_token = mch_resp.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Dashboard should now show zero-data state for new merchant
    dash_resp2 = client.get("/api/v1/merchant/dashboard", headers=new_headers)
    assert dash_resp2.status_code == 200
    assert dash_resp2.json()["has_merchant"] is True
    assert dash_resp2.json()["merchant_name"] == "Acme Superstore Pvt Ltd"
    assert dash_resp2.json()["total_transactions"] == 0
    assert dash_resp2.json()["current_revenue"] == 0.0

def test_firebase_login_development_sandbox(db_session):
    """Test simulated Firebase Google token login in sandbox environment."""
    payload = {
        "id_token": "google_token_mock_test_12345",
        "email": "google.dev.user@example.com",
        "full_name": "Google Verified User"
    }
    resp = client.post("/api/v1/auth/firebase-login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "google.dev.user@example.com"
    assert data["user"]["onboarding_required"] is True

    # Verify user was provisioned with firebase_uid
    u = db_session.query(User).filter(User.email == "google.dev.user@example.com").first()
    assert u is not None
    assert u.firebase_uid is not None
    assert u.last_login is not None

def test_readiness_probe_healthy(db_session):
    """Verify /readiness returns structured service health without leaking secrets."""
    resp = client.get("/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "READY"
    assert data["database"] == "READY"
    assert data["configuration"]["automated_execution"] == "DISABLED_SAFE_GATE"
    assert "SECRET" not in str(data)
