from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class WorkflowStatus(str, enum.Enum):
    initializing = 'initializing'
    running = 'running'
    completed = 'completed'
    failed = 'failed'
    partial = 'partial'

class Workflow(Base):
    __tablename__ = 'workflows'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    conversation_id = Column(String(100), nullable=True, index=True)
    user_query = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    status = Column(SAEnum(WorkflowStatus), default=WorkflowStatus.initializing)
    execution_plan = Column(JSON, nullable=True)
    active_agents = Column(JSON, default=list)
    state_snapshot = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant', back_populates='workflows')
    findings = relationship('AgentFinding', back_populates='workflow')
    actions = relationship('Action', back_populates='workflow')
    audit_events = relationship('AuditEvent', back_populates='workflow')
