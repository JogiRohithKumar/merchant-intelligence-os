from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.base import Base, generate_uuid

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    # IMMUTABLE - append-only cryptographically chained ledger
    
    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    conversation_id = Column(String(100), nullable=True)
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=True, index=True)
    agent = Column(String(50), nullable=True, index=True)
    action = Column(String(200), nullable=False)
    input_summary = Column(Text, nullable=True)
    evidence_ids = Column(JSON, default=list)
    recommendation = Column(Text, nullable=True)
    policy_result = Column(JSON, nullable=True)
    approval_status = Column(String(30), nullable=True)
    execution_result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    # Tamper-evident SHA-256 hash chaining
    prev_event_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=True, index=True)
    
    merchant = relationship('Merchant')
    workflow = relationship('Workflow', back_populates='audit_events')
