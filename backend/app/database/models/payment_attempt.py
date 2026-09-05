from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class FailureReason(str, enum.Enum):
    insufficient_funds = 'insufficient_funds'
    card_declined = 'card_declined'
    gateway_timeout = 'gateway_timeout'
    fraud_block = 'fraud_block'
    expired_card = 'expired_card'
    network_error = 'network_error'
    none = 'none'

class AttemptStatus(str, enum.Enum):
    success = 'success'
    failed = 'failed'
    timeout = 'timeout'
    unknown = 'unknown'

class PaymentAttempt(Base):
    __tablename__ = 'payment_attempts'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    status = Column(SAEnum(AttemptStatus), default=AttemptStatus.failed)
    failure_reason = Column(SAEnum(FailureReason), default=FailureReason.none)
    amount = Column(Numeric(12, 2), nullable=False)
    gateway = Column(String(50), default='razorpay')
    gateway_response_code = Column(String(20), nullable=True)
    risk_score = Column(Float, default=0.1)
    is_retry = Column(Boolean, default=False)
    recovery_probability = Column(Float, nullable=True)
    expected_recovery_value = Column(Float, nullable=True)
    idempotency_key = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    transaction = relationship('Transaction', back_populates='payment_attempts')
    merchant = relationship('Merchant')
