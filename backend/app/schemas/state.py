import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

class AgentName(str, Enum):
    SUPERVISOR = 'supervisor'
    FINANCE = 'finance'
    RISK = 'risk'
    RECOVERY = 'recovery'
    GROWTH = 'growth'

class Severity(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # transaction, chargeback, settlement, risk_event, payment_attempt
    description: str
    amount: Optional[float] = None
    timestamp: Optional[datetime] = None
    source: str
    record_id: Optional[str] = None  # FK reference

class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentName
    finding: str
    metric_label: Optional[str] = None
    metric_previous: Optional[float] = None
    metric_current: Optional[float] = None
    metric_unit: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity
    evidence_ids: list[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RootCauseContribution(BaseModel):
    cause: str
    contribution_pct: float  # 0-100
    agent: AgentName
    evidence_ids: list[str] = Field(default_factory=list)
    finding_id: Optional[str] = None
    amount_impact: Optional[float] = None

class AgentState(BaseModel):
    user_query: str
    merchant_id: str
    conversation_id: str
    workflow_id: str
    intent: Optional[str] = None
    entities: dict = Field(default_factory=dict)
    execution_plan: Optional[dict] = None
    active_agents: list[AgentName] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    recommendations: list[dict] = Field(default_factory=list)
    root_causes: list[RootCauseContribution] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)
    approvals: list[dict] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    audit_events: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    synthesis: Optional[str] = None
    status: str = 'initializing'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
