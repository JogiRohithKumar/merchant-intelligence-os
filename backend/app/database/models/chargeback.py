from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class ChargebackStatus(str, enum.Enum):
    received = 'received'
    under_review = 'under_review'
    won = 'won'
    lost = 'lost'
    reversed = 'reversed'

class Chargeback(Base):
    __tablename__ = 'chargebacks'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=False, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False, index=True)
    chargeback_ref = Column(String(100), unique=True, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='INR')
    reason_code = Column(String(20), nullable=False)
    reason_description = Column(Text, nullable=True)
    status = Column(SAEnum(ChargebackStatus), default=ChargebackStatus.received)
    evidence_submitted = Column(Boolean, default=False)
    evidence_deadline = Column(DateTime, nullable=True)
    is_segment_b = Column(Boolean, default=False)  # flag for injected anomaly
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant', back_populates='chargebacks')
    transaction = relationship('Transaction', back_populates='chargebacks')
    customer = relationship('Customer', back_populates='chargebacks')
