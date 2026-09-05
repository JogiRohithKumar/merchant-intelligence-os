from enum import Enum
from pydantic import BaseModel
from typing import Optional

class PolicyDecisionEnum(str, Enum):
    ALLOW = 'ALLOW'
    REQUIRE_APPROVAL = 'REQUIRE_APPROVAL'
    REJECT = 'REJECT'

class PolicyResult(BaseModel):
    decision: PolicyDecisionEnum
    reason: str
    conditions: list[str] = []
    audit_required: bool = True
    max_amount: Optional[float] = None
    required_approval_role: Optional[str] = None
