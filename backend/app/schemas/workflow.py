from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class WorkflowEventType(str, Enum):
    WORKFLOW_STARTED = 'workflow_started'
    AGENT_STARTED = 'agent_started'
    AGENT_TOOL_CALLED = 'agent_tool_called'
    FINDING_YIELDED = 'finding_yielded'
    AGENT_COMPLETED = 'agent_completed'
    SYNTHESIS_COMPLETED = 'synthesis_completed'
    POLICY_EVALUATED = 'policy_evaluated'
    APPROVAL_REQUIRED = 'approval_required'
    ACTION_EXECUTED = 'action_executed'
    WORKFLOW_COMPLETED = 'workflow_completed'
    WORKFLOW_FAILED = 'workflow_failed'

class WorkflowEvent(BaseModel):
    event_type: WorkflowEventType
    workflow_id: str
    agent: Optional[str] = None
    message: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
