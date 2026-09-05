from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class MerchantStatus(str, enum.Enum):
    active = 'active'
    suspended = 'suspended'

class Merchant(Base):
    __tablename__ = 'merchants'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    business_type = Column(String(100), default='ecommerce')
    country = Column(String(3), default='IN')
    currency = Column(String(3), default='INR')
    status = Column(SAEnum(MerchantStatus), default=MerchantStatus.active)
    monthly_revenue_baseline = Column(Numeric(15, 2), default=0)
    
    # Provider integration state
    razorpay_key_id = Column(String(100), nullable=True)
    razorpay_key_secret = Column(String(100), nullable=True)
    razorpay_webhook_secret = Column(String(100), nullable=True)
    connection_status = Column(String(50), default='not_connected')  # not_connected, connecting, connected, failed
    last_synced_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    users = relationship('User', back_populates='merchant')
    customers = relationship('Customer', back_populates='merchant')
    products = relationship('Product', back_populates='merchant')
    orders = relationship('Order', back_populates='merchant')
    transactions = relationship('Transaction', back_populates='merchant')
    settlements = relationship('Settlement', back_populates='merchant')
    chargebacks = relationship('Chargeback', back_populates='merchant')
    campaigns = relationship('Campaign', back_populates='merchant')
    workflows = relationship('Workflow', back_populates='merchant')
