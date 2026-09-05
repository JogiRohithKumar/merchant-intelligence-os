from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class UserRole(str, enum.Enum):
    merchant_admin = 'merchant_admin'
    finance_user = 'finance_user'
    risk_user = 'risk_user'
    operator = 'operator'
    customer = 'customer'

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for pure Firebase Google Auth users
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.operator)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=True, index=True)  # Nullable for brand new users awaiting onboarding
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)
    account_status = Column(String(32), default='active', nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant', back_populates='users')
