from sqlalchemy import Column, String, DateTime, Float, JSON, Text, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class ActionStatus(str, enum.Enum):
    PROPOSED = 'PROPOSED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    EXECUTING = 'EXECUTING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    UNKNOWN = 'UNKNOWN'

class ActionRiskLevel(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    prohibited = 'prohibited'

class Action(Base):
    __tablename__ = 'actions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    action_params = Column(JSON, nullable=True)
    risk_level = Column(SAEnum(ActionRiskLevel), default=ActionRiskLevel.medium)
    status = Column(SAEnum(ActionStatus), default=ActionStatus.PROPOSED)
    policy_result = Column(JSON, nullable=True)
    idempotency_key = Column(String(64), unique=True, nullable=False, index=True)
    execution_result = Column(JSON, nullable=True)
    execution_error = Column(Text, nullable=True)
    amount_at_risk = Column(Float, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    evidence_ids = Column(JSON, default=list)
    proposed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    approved_by = Column(String, ForeignKey('users.id'), nullable=True)
    test_mode = Column(Boolean, default=True)
    
    workflow = relationship('Workflow', back_populates='actions')
    merchant = relationship('Merchant')
    approver = relationship('User')
