from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class CustomerSegment(str, enum.Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    external_id = Column(String(100), index=True)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    segment = Column(SAEnum(CustomerSegment), default=CustomerSegment.C)
    country = Column(String(3), default='IN')
    acquisition_channel = Column(String(50), default='organic')
    total_orders = Column(Integer, default=0)
    total_spend = Column(Float, default=0.0)
    last_order_at = Column(DateTime, nullable=True)
    risk_score = Column(Float, default=0.1)
    is_high_risk = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant', back_populates='customers')
    transactions = relationship('Transaction', back_populates='customer')
    chargebacks = relationship('Chargeback', back_populates='customer')
    subscriptions = relationship('Subscription', back_populates='customer')
