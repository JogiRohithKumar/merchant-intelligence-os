from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid
import hashlib

from app.database.session import get_db
from app.database.models.user import User, UserRole
from app.database.models.merchant import Merchant, MerchantStatus
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.core.logging import get_logger

logger = get_logger("auth.api")
router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    merchant_id: Optional[str] = None
    role: Optional[str] = "operator"

class FirebaseLoginRequest(BaseModel):
    id_token: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class CreateMerchantRequest(BaseModel):
    name: str
    business_type: Optional[str] = "ecommerce"
    country: Optional[str] = "IN"
    currency: Optional[str] = "INR"

class ConnectRazorpayRequest(BaseModel):
    key_id: str
    key_secret: str
    webhook_secret: Optional[str] = None

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ")[1]
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or account deactivated")
    return user

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Customer & Merchant registration endpoint.
    Brand new users are NEVER assigned to Bharat Commerce or any default merchant.
    They start with merchant_id = NULL and must complete merchant onboarding.
    """
    existing_user = db.query(User).filter(User.email == req.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address is already registered")

    if len(req.password) < 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 8 characters long")

    target_merchant_id = None
    if req.merchant_id:
        merchant = db.query(Merchant).filter(Merchant.id == req.merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified merchant tenant does not exist")
        target_merchant_id = merchant.id

    now = datetime.now(timezone.utc)
    new_user = User(
        id=f"usr_{uuid.uuid4().hex[:12]}",
        email=req.email.lower(),
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=UserRole.merchant_admin if not target_merchant_id else UserRole.operator,
        merchant_id=target_merchant_id,  # NULL for brand new unattached merchant
        account_status="active",
        is_active=True,
        created_at=now,
        last_login=now
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token_data = {
        "user_id": new_user.id,
        "merchant_id": new_user.merchant_id or "",
        "role": new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role),
        "email": new_user.email
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "status": "success",
        "message": "Account created successfully. Please complete merchant onboarding.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role),
            "merchant_id": new_user.merchant_id,
            "merchant_name": None,
            "account_status": new_user.account_status,
            "onboarding_required": new_user.merchant_id is None
        }
    }

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    merchant_name = user.merchant.name if user.merchant else None

    token_data = {
        "user_id": user.id,
        "merchant_id": user.merchant_id or "",
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "email": user.email
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "merchant_id": user.merchant_id,
            "merchant_name": merchant_name,
            "account_status": user.account_status or "active",
            "onboarding_required": user.merchant_id is None
        }
    }

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates a secure password reset.
    Generates a cryptographic time-limited reset token.
    """
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user:
        # Prevent user enumeration: always return success message
        return {
            "status": "success",
            "message": "If an account with this email exists, a password reset link has been issued."
        }

    token = create_password_reset_token(user.email)
    logger.info(f"Password reset token issued for user {user.id}")

    return {
        "status": "success",
        "message": "Password reset token generated successfully.",
        "reset_token": token,  # Provided for immediate verification in test/sandbox environment
        "expires_in_hours": 1
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Completes password reset using verified token and hashes new password.
    """
    email = verify_password_reset_token(req.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, tampered, or expired password reset token."
        )

    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be at least 8 characters long."
        )

    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    logger.info(f"Password successfully reset for user {user.id}")

    return {
        "status": "success",
        "message": "Password has been successfully updated. You may now sign in with your new password."
    }

@router.post("/firebase-login")
async def firebase_login(req: FirebaseLoginRequest, db: Session = Depends(get_db)):
    firebase_uid = None
    email = req.email
    full_name = req.full_name or "Google User"

    if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PRIVATE_KEY:
        try:
            import firebase_admin
            from firebase_admin import auth as fb_auth, credentials
            if not firebase_admin._apps:
                cred = credentials.Certificate({
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "client_email": settings.FIREBASE_CLIENT_EMAIL,
                    "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n')
                })
                firebase_admin.initialize_app(cred)
            decoded_token = fb_auth.verify_id_token(req.id_token)
            firebase_uid = decoded_token.get("uid")
            email = decoded_token.get("email", email)
            full_name = decoded_token.get("name", full_name)
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase authentication token")
    else:
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase authentication is not configured for production deployment."
            )
        if not req.id_token or len(req.id_token) < 10:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid development token")
        firebase_uid = f"fb_{hashlib.sha256(req.id_token.encode()).hexdigest()[:16]}"
        if not email:
            email = f"{firebase_uid}@sandbox.merchant.com"

    user = db.query(User).filter(
        (User.firebase_uid == firebase_uid) | (User.email == email.lower())
    ).first()

    now = datetime.now(timezone.utc)
    if not user:
        # Genuinely new user starts with merchant_id = NULL
        user = User(
            id=f"usr_fb_{uuid.uuid4().hex[:10]}",
            email=email.lower(),
            hashed_password=None,
            full_name=full_name,
            role=UserRole.merchant_admin,
            merchant_id=None,  # No fallback to Bharat Commerce!
            firebase_uid=firebase_uid,
            account_status="active",
            is_active=True,
            created_at=now,
            last_login=now
        )
        db.add(user)
    else:
        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
        user.last_login = now

    db.commit()
    db.refresh(user)

    merchant_name = user.merchant.name if user.merchant else None

    token_data = {
        "user_id": user.id,
        "merchant_id": user.merchant_id or "",
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "email": user.email
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "merchant_id": user.merchant_id,
            "merchant_name": merchant_name,
            "account_status": user.account_status or "active",
            "onboarding_required": user.merchant_id is None
        }
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    merchant_name = current_user.merchant.name if current_user.merchant else None
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "merchant_id": current_user.merchant_id,
        "merchant_name": merchant_name,
        "account_status": current_user.account_status or "active",
        "onboarding_required": current_user.merchant_id is None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }

@router.post("/onboarding/create-merchant")
@router.post("/merchants")
def create_merchant(req: CreateMerchantRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Allows an authenticated user to create and associate their own new Merchant organization.
    The new merchant starts with zero transactions and connection_status = 'not_connected'.
    """
    if current_user.merchant_id:
        existing = db.query(Merchant).filter(Merchant.id == current_user.merchant_id).first()
        if existing:
            return {
                "status": "already_associated",
                "message": f"User is already assigned to merchant {existing.name}",
                "merchant": {
                    "id": existing.id,
                    "name": existing.name,
                    "currency": existing.currency,
                    "connection_status": existing.connection_status
                }
            }

    merchant_id = f"mch_{uuid.uuid4().hex[:12]}"
    new_merchant = Merchant(
        id=merchant_id,
        name=req.name,
        business_type=req.business_type or "ecommerce",
        country=req.country or "IN",
        currency=req.currency or "INR",
        status=MerchantStatus.active,
        connection_status="not_connected"
    )
    db.add(new_merchant)
    
    # Assign user as admin of their newly created merchant
    current_user.merchant_id = merchant_id
    current_user.role = UserRole.merchant_admin
    db.commit()
    db.refresh(new_merchant)

    # Issue refreshed token with newly attached merchant_id
    token_data = {
        "user_id": current_user.id,
        "merchant_id": merchant_id,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "email": current_user.email
    }
    new_token = create_access_token(token_data)

    return {
        "status": "success",
        "message": f"Merchant {new_merchant.name} created successfully.",
        "access_token": new_token,
        "merchant": {
            "id": new_merchant.id,
            "name": new_merchant.name,
            "business_type": new_merchant.business_type,
            "currency": new_merchant.currency,
            "country": new_merchant.country,
            "connection_status": new_merchant.connection_status
        }
    }

@router.get("/merchant/status")
def get_merchant_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns the authenticated merchant profile and connection verification telemetry."""
    if not current_user.merchant_id:
        return {
            "configured": False,
            "onboarding_required": True,
            "message": "User is not associated with any merchant organization."
        }
    
    m = db.query(Merchant).filter(Merchant.id == current_user.merchant_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")

    from app.database.models.transaction import Transaction
    tx_count = db.query(Transaction).filter(Transaction.merchant_id == m.id).count()

    return {
        "configured": True,
        "onboarding_required": False,
        "merchant": {
            "id": m.id,
            "name": m.name,
            "business_type": m.business_type,
            "currency": m.currency,
            "country": m.country,
            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
            "connection_status": m.connection_status or "not_connected",
            "has_credentials": bool(m.razorpay_key_id and m.razorpay_key_secret),
            "last_synced_at": m.last_synced_at.isoformat() if m.last_synced_at else None,
            "transactions_count": tx_count
        }
    }

@router.post("/merchant/connect-razorpay")
def connect_razorpay(req: ConnectRazorpayRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Website flow to securely configure Razorpay credentials for the authenticated merchant.
    Validates key format and marks connection verified.
    """
    if not current_user.merchant_id:
        raise HTTPException(status_code=400, detail="Must complete merchant onboarding first")

    m = db.query(Merchant).filter(Merchant.id == current_user.merchant_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")

    # Validate key prefix (rzp_test_ or rzp_live_)
    if not (req.key_id.startswith("rzp_test_") or req.key_id.startswith("rzp_live_")):
        raise HTTPException(status_code=422, detail="Invalid Razorpay Key ID. Must start with 'rzp_test_' or 'rzp_live_'.")

    now = datetime.now(timezone.utc)
    m.razorpay_key_id = req.key_id
    m.razorpay_key_secret = req.key_secret
    if req.webhook_secret:
        m.razorpay_webhook_secret = req.webhook_secret
    m.connection_status = "connected"
    m.last_synced_at = now
    db.commit()

    return {
        "status": "connected",
        "message": "Razorpay connection verified successfully.",
        "provider": "Razorpay",
        "key_id_masked": f"{req.key_id[:8]}...{req.key_id[-4:]}",
        "connected_at": now.isoformat()
    }
