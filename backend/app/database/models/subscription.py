from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class SubscriptionStatus(str, enum.Enum):
    active = 'active'
    paused = 'paused'
    cancelled = 'cancelled'
    failed = 'failed'

class BillingCycle(str, enum.Enum):
    weekly = 'weekly'
    monthly = 'monthly'
    annual = 'annual'

class RecoveryStatus(str, enum.Enum):
    none = 'none'
    in_progress = 'in_progress'
    recovered = 'recovered'
    abandoned = 'abandoned'

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False, index=True)
    plan_name = Column(String(100), nullable=False)
    status = Column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.active)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='INR')
    billing_cycle = Column(SAEnum(BillingCycle), default=BillingCycle.monthly)
    next_billing_date = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    last_failed_at = Column(DateTime, nullable=True)
    recovery_status = Column(SAEnum(RecoveryStatus), default=RecoveryStatus.none)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant')
    customer = relationship('Customer', back_populates='subscriptions')
