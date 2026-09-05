from typing import Optional
from pydantic import BaseModel
from .state import AgentName, Finding, Evidence
from .action import ProposedAction

class AgentResult(BaseModel):
    agent: AgentName
    status: str  # completed, failed, partial
    findings: list[Finding] = []
    evidence: list[Evidence] = []
    proposed_actions: list[ProposedAction] = []
    metrics: dict = {}
    latency_ms: int = 0
    error: Optional[str] = None
