from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, Enum as SAEnum, Text, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class RiskEventType(str, enum.Enum):
    fraud_alert = 'fraud_alert'
    velocity_breach = 'velocity_breach'
    anomaly = 'anomaly'
    abuse_ring = 'abuse_ring'
    device_fingerprint = 'device_fingerprint'
    chargeback_risk = 'chargeback_risk'

class RiskSeverity(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'

class RiskEvent(Base):
    __tablename__ = 'risk_events'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=True, index=True)
    event_type = Column(SAEnum(RiskEventType), nullable=False)
    risk_score = Column(Float, nullable=False)
    severity = Column(SAEnum(RiskSeverity), nullable=False)
    features = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    is_false_positive = Column(Boolean, nullable=True)
    label = Column(Integer, nullable=True)  # 0=legitimate, 1=risky
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    merchant = relationship('Merchant')
    transaction = relationship('Transaction', back_populates='risk_events')
