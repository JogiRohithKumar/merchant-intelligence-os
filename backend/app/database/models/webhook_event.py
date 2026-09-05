from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.base import Base, generate_uuid

class WebhookEvent(Base):
    __tablename__ = 'webhook_events'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    source = Column(String(50), nullable=False, default='razorpay', index=True)
    event_type = Column(String(100), nullable=False, index=True)
    external_event_id = Column(String(200), unique=True, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=True)
    signature = Column(String(255), nullable=True)
    signature_valid = Column(Boolean, default=False)
    status = Column(String(30), default='received', index=True) # received, processed, duplicate, failed, dead_letter
    error_message = Column(String(500), nullable=True)
    retry_count = Column(Integer, default=0)
    occurred_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant')
