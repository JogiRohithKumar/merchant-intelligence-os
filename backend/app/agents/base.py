from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy.orm import Session
from app.schemas.state import AgentState, AgentName, Finding, Evidence, Severity
from app.schemas.finding import AgentResult
from app.schemas.workflow import WorkflowEvent, WorkflowEventType
from app.engines.rag_knowledge import query_knowledge, KnowledgeChunk
from app.core.logging import get_logger

class BaseAgent(ABC):
    def __init__(self, name: AgentName, db: Session, merchant_id: str):
        self.name = name
        self.db = db
        self.merchant_id = merchant_id
        self.logger = get_logger(f'agent.{name.value}')
        self._events: list[WorkflowEvent] = []
    
    async def execute(self, state: AgentState) -> AgentResult:
        """Main execution wrapper with timing and error handling."""
        start = datetime.now(timezone.utc)
        self.logger.info(f'Agent {self.name.value} starting for workflow {state.workflow_id}')
        try:
            result = await self._run(state)
            elapsed = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            result.latency_ms = elapsed
            self._write_audit(state, result)
            return result
        except Exception as e:
            self.logger.error(f'Agent {self.name.value} failed: {e}')
            elapsed = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            return AgentResult(
                agent=self.name,
                status='failed',
                error=str(e),
                latency_ms=elapsed
            )
    
    @abstractmethod
    async def _run(self, state: AgentState) -> AgentResult:
        pass
    
    def _make_event(self, workflow_id: str, event_type: WorkflowEventType, message: str, data: dict = None) -> WorkflowEvent:
        return WorkflowEvent(
            event_type=event_type,
            workflow_id=workflow_id,
            agent=self.name.value,
            message=message,
            data=data or {}
        )
    
    def _create_evidence(self, type_: str, description: str, source: str, amount: Optional[float] = None, record_id: Optional[str] = None) -> Evidence:
        return Evidence(
            id=str(uuid.uuid4()),
            type=type_,
            description=description,
            amount=amount,
            source=source,
            record_id=record_id
        )
    
    def _create_finding(self, finding_text: str, severity: Severity, confidence: float,
                        evidence_ids: list[str], recommended_action: Optional[str] = None,
                        metric_label: Optional[str] = None, metric_prev: Optional[float] = None,
                        metric_curr: Optional[float] = None, metric_unit: Optional[str] = None) -> Finding:
        return Finding(
            agent=self.name,
            finding=finding_text,
            metric_label=metric_label,
            metric_previous=metric_prev,
            metric_current=metric_curr,
            metric_unit=metric_unit,
            confidence=confidence,
            severity=severity,
            evidence_ids=evidence_ids,
            recommended_action=recommended_action
        )
    
    def _query_knowledge(self, question: str, n: int = 2) -> list[KnowledgeChunk]:
        return query_knowledge(question, n_results=n)
    
    def _write_audit(self, state: AgentState, result: AgentResult):
        try:
            import hashlib
            import json
            from datetime import datetime, timezone
            from app.database.models.audit_event import AuditEvent
            evidence_ids = []
            for f in result.findings:
                evidence_ids.extend(f.evidence_ids)

            last_event = self.db.query(AuditEvent).filter(
                AuditEvent.merchant_id == self.merchant_id
            ).order_by(AuditEvent.timestamp.desc()).first()

            prev_hash = last_event.event_hash if (last_event and last_event.event_hash) else "0000000000000000000000000000000000000000000000000000000000000000"
            now = datetime.now(timezone.utc)
            action_name = f'{self.name.value}_execution'
            event_id = str(uuid.uuid4())
            exec_res = {'status': result.status, 'findings_count': len(result.findings), 'actions_count': len(result.proposed_actions)}

            payload_string = f"{prev_hash}|{now.isoformat()}|{self.merchant_id}|{event_id}|{action_name}|COMPLETED|{json.dumps(exec_res, sort_keys=True)}"
            current_hash = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

            event = AuditEvent(
                id=event_id,
                merchant_id=self.merchant_id,
                conversation_id=state.conversation_id,
                workflow_id=state.workflow_id,
                agent=self.name.value,
                action=action_name,
                input_summary=f'Query: {state.user_query[:200]}',
                evidence_ids=evidence_ids,
                recommendation=result.findings[0].recommended_action if result.findings else None,
                execution_result=exec_res,
                latency_ms=result.latency_ms,
                prev_event_hash=prev_hash,
                event_hash=current_hash,
                timestamp=now
            )
            self.db.add(event)
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            self.logger.warning(f'Failed to write audit event: {e}')
