from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class TransactionType(str, enum.Enum):
    payment = 'payment'
    refund = 'refund'
    chargeback = 'chargeback'
    adjustment = 'adjustment'

class TransactionStatus(str, enum.Enum):
    success = 'success'
    failed = 'failed'
    pending = 'pending'
    disputed = 'disputed'

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=True, index=True)
    order_id = Column(String, ForeignKey('orders.id'), nullable=True, index=True)
    transaction_type = Column(SAEnum(TransactionType), default=TransactionType.payment)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='INR')
    status = Column(SAEnum(TransactionStatus), default=TransactionStatus.pending, index=True)
    gateway = Column(String(50), default='razorpay')
    gateway_transaction_id = Column(String(200), unique=True, nullable=True, index=True)
    payment_method = Column(String(50), default='upi')
    country = Column(String(3), default='IN')
    device_type = Column(String(20), default='mobile')
    ip_address = Column(String(50), nullable=True)
    risk_score = Column(Float, default=0.1)
    is_anomaly_day = Column(Boolean, default=False)  # flags gateway degradation window
    data_source = Column(String(50), default='DEMO', nullable=False)  # 'LIVE_RAZORPAY', 'SANDBOX', 'DEMO'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    settled_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant', back_populates='transactions')
    customer = relationship('Customer', back_populates='transactions')
    order = relationship('Order', back_populates='transactions')
    payment_attempts = relationship('PaymentAttempt', back_populates='transaction')
    risk_events = relationship('RiskEvent', back_populates='transaction')
    settlement_items = relationship('SettlementItem', back_populates='transaction')
    chargebacks = relationship('Chargeback', back_populates='transaction')
