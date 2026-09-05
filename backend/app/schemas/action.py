import uuid
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class ActionRiskLevel(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    PROHIBITED = 'prohibited'

class ActionStatus(str, Enum):
    PROPOSED = 'PROPOSED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    EXECUTING = 'EXECUTING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    UNKNOWN = 'UNKNOWN'

class ProposedAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str
    description: str
    params: dict = Field(default_factory=dict)
    amount_at_risk: Optional[float] = None
    expected_outcome: str
    evidence_ids: list[str] = Field(default_factory=list)
    idempotency_key: str
    risk_level: ActionRiskLevel
    status: ActionStatus = ActionStatus.PROPOSED
    policy_result: Optional[dict] = None
    proposed_at: datetime = Field(default_factory=datetime.utcnow)
