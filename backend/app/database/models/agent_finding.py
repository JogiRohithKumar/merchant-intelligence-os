from sqlalchemy import Column, String, DateTime, Float, JSON, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class FindingSeverity(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'

class AgentFinding(Base):
    __tablename__ = 'agent_findings'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    agent = Column(String(50), nullable=False)
    finding = Column(Text, nullable=False)
    severity = Column(SAEnum(FindingSeverity), default=FindingSeverity.medium)
    evidence_ids = Column(JSON, default=list)
    confidence = Column(Float, default=0.5)
    recommended_action = Column(Text, nullable=True)
    metric_label = Column(String(100), nullable=True)
    metric_previous = Column(Float, nullable=True)
    metric_current = Column(Float, nullable=True)
    metric_unit = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    workflow = relationship('Workflow', back_populates='findings')
    merchant = relationship('Merchant')
