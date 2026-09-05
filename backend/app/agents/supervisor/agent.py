import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import AsyncGenerator, Optional, List, Tuple, Dict, Any
import json

from app.schemas.state import AgentState, AgentName, Finding, Evidence, RootCauseContribution, Severity
from app.schemas.workflow import WorkflowEvent, WorkflowEventType
from app.schemas.action import ProposedAction, ActionRiskLevel, ActionStatus
from app.agents.registry import agent_registry, AgentCapability
from app.agents.finance.agent import FinanceAgent
from app.agents.risk.agent import RiskAgent
from app.agents.recovery.agent import RecoveryAgent
from app.agents.growth.agent import GrowthAgent
from app.orchestration.events import event_broadcaster
from app.policies.engine import policy_engine
from app.policies.idempotency import IdempotencyChecker, generate_idempotency_key
from app.execution.engine import execution_engine
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('agent.supervisor')

INTENT_PATTERNS = {
    'revenue_investigation': [
        'revenue', 'sales', 'revenue dropped', 'sales dropped', 'dropped 20%', 'decline in sales', 'revenue decline'
    ],
    'settlement_investigation': [
        'settlement', 'payout', 'reconcil', 'mismatch', 'discrepancy', "doesn't match", "does not match", 'expected amount'
    ],
    'failed_payment_recovery': [
        'failed payment', 'failed payments', 'failed transaction', 'payment failure', 'failure rate', 'payment failures', 'recover', 'retry', 'stuck payment'
    ],
    'chargeback_analysis': [
        'chargeback', 'chargebacks', 'dispute', 'disputes', 'fraud', 'fraudulent'
    ],
    'customer_behavior': [
        'customer', 'repeat', 'inactive', 'product', 'conversion', 'stopped buying', 'how can i improve'
    ],
    'cash_forecast': [
        'cash', 'forecast', 'cashflow', 'runway'
    ]
}

CAPABILITY_MAPPING = {
    'revenue_investigation': [
        AgentCapability.REVENUE_ANALYSIS,
        AgentCapability.RECONCILIATION,
        AgentCapability.FRAUD_SCORING,
        AgentCapability.FAILED_PAYMENT_RECOVERY,
        AgentCapability.CONVERSION_ANALYSIS
    ],
    'settlement_investigation': [
        AgentCapability.RECONCILIATION,
        AgentCapability.SETTLEMENT_INVESTIGATION
    ],
    'failed_payment_recovery': [
        AgentCapability.FAILED_PAYMENT_RECOVERY,
        AgentCapability.FRAUD_SCORING
    ],
    'chargeback_analysis': [
        AgentCapability.CHARGEBACK_ANALYSIS,
        AgentCapability.FRAUD_SCORING,
        AgentCapability.RECONCILIATION
    ],
    'customer_behavior': [
        AgentCapability.CONVERSION_ANALYSIS,
        AgentCapability.CUSTOMER_REACTIVATION
    ],
    'cash_forecast': [
        AgentCapability.CASH_FORECASTING
    ]
}

class SupervisorAgent:
    def __init__(self, db: Session, merchant_id: str):
        self.db = db
        self.merchant_id = merchant_id
        self.logger = get_logger('agent.supervisor')

    def _detect_intents(self, query: str) -> list[str]:
        q_lower = query.lower()
        intents = []
        for intent, keywords in INTENT_PATTERNS.items():
            if any(kw in q_lower for kw in keywords):
                intents.append(intent)
        if not intents:
            intents = ['revenue_investigation']
        return intents

    def _plan_agents(self, intents: list[str]) -> Tuple[list[AgentName], list[AgentName], dict]:
        all_capabilities = set()
        for intent in intents:
            caps = CAPABILITY_MAPPING.get(intent, [])
            all_capabilities.update(c.value for c in caps)

        selected = agent_registry.find_agents_for_capabilities(list(all_capabilities))
        all_possible = [AgentName.FINANCE, AgentName.RISK, AgentName.RECOVERY, AgentName.GROWTH]
        rejected = [a for a in all_possible if a not in selected]

        has_recovery = AgentName.RECOVERY in selected
        parallel_1 = [a for a in [AgentName.FINANCE, AgentName.RISK, AgentName.GROWTH] if a in selected]
        sequential_2 = [AgentName.RECOVERY] if has_recovery else []

        execution_plan = {
            'parallel_groups': [
                [a.value for a in parallel_1],
                [a.value for a in sequential_2]
            ],
            'selected_agents': [a.value for a in selected],
            'rejected_agents': [a.value for a in rejected],
            'capabilities': list(all_capabilities),
            'intents': intents
        }
        return selected, rejected, execution_plan

    async def run_workflow(
        self,
        query: str,
        merchant_id: str,
        conversation_id: str,
        workflow_id: str
    ) -> AsyncGenerator[WorkflowEvent, None]:
        state = AgentState(
            user_query=query,
            merchant_id=merchant_id,
            conversation_id=conversation_id,
            workflow_id=workflow_id,
            status='running'
        )

        self._update_workflow_status(workflow_id, 'running', state)

        # 1. Workflow Started Event
        evt_start = WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_STARTED,
            workflow_id=workflow_id,
            agent='supervisor',
            message=f'Analyzing merchant query: {query[:120]}',
            data={'query': query}
        )
        event_broadcaster.emit(workflow_id, evt_start)
        yield evt_start

        # Check transaction volume in database for this specific merchant
        from app.database.models.transaction import Transaction
        merchant_tx_count = self.db.query(Transaction).filter(Transaction.merchant_id == merchant_id).count()

        if merchant_tx_count == 0:
            # Honest Data Dependency: Zero transactions in ledger
            zero_finding = Finding(
                id=str(uuid.uuid4()),
                agent=AgentName.FINANCE,
                finding='Insufficient merchant transaction history to analyze operations. No transactions have entered this merchant account yet.',
                severity=Severity.LOW,
                confidence=1.0,
                recommended_action='Connect Razorpay payment gateway in Settings to begin real-time data ingestion.'
            )
            state.findings.append(zero_finding)
            state.synthesis = (
                "## Merchant Telemetry Status: Zero Transactions Recorded\n\n"
                "Merchant Intelligence OS does not fabricate synthetic insights for active merchant accounts. "
                "Because zero transactions have been ingested for this merchant organization, no revenue leaks, "
                "settlement shortfalls, or recovery candidates exist. "
                "Once you connect Razorpay or stream webhooks, automated multi-agent telemetry will activate immediately."
            )
            self._persist_findings(state, workflow_id, merchant_id)
            self._update_workflow_status(workflow_id, 'completed', state)

            evt_synth = WorkflowEvent(
                event_type=WorkflowEventType.SYNTHESIS_COMPLETED,
                workflow_id=workflow_id,
                agent='supervisor',
                message='Data sufficiency check complete: zero transactions found for this merchant.',
                data={'synthesis': state.synthesis}
            )
            event_broadcaster.emit(workflow_id, evt_synth)
            yield evt_synth

            evt_done = WorkflowEvent(
                event_type=WorkflowEventType.WORKFLOW_COMPLETED,
                workflow_id=workflow_id,
                agent='supervisor',
                message='Zero-data audit complete. Awaiting merchant payment provider connection.',
                data={'findings': 1, 'actions': 0}
            )
            event_broadcaster.emit(workflow_id, evt_done)
            yield evt_done
            return

        # 2. Dynamic Planning & Agent Selection
        intents = self._detect_intents(query)
        state.intent = ', '.join(intents)
        state.entities = {'intents': intents, 'merchant_id': merchant_id, 'time_window_days': 30}

        selected_agents, rejected_agents, execution_plan = self._plan_agents(intents)
        state.execution_plan = execution_plan
        state.active_agents = selected_agents

        evt_plan = WorkflowEvent(
            event_type=WorkflowEventType.AGENT_STARTED,
            workflow_id=workflow_id,
            agent='supervisor',
            message=f'Dynamic DAG planned. Active: {[a.value for a in selected_agents]}, Bypassed: {[a.value for a in rejected_agents]}',
            data=execution_plan
        )
        event_broadcaster.emit(workflow_id, evt_plan)
        yield evt_plan

        # 3. Instantiate and Execute Selected Agents
        agent_instances = {
            AgentName.FINANCE: FinanceAgent(self.db, merchant_id),
            AgentName.RISK: RiskAgent(self.db, merchant_id),
            AgentName.RECOVERY: RecoveryAgent(self.db, merchant_id),
            AgentName.GROWTH: GrowthAgent(self.db, merchant_id)
        }

        all_results = {}

        # Parallel Group 1: (Finance, Risk, Growth) if selected
        group_1 = [a for a in [AgentName.FINANCE, AgentName.RISK, AgentName.GROWTH] if a in selected_agents]
        if group_1:
            for agent_name in group_1:
                evt_agent_start = WorkflowEvent(
                    event_type=WorkflowEventType.AGENT_STARTED,
                    workflow_id=workflow_id,
                    agent=agent_name.value,
                    message=f'{agent_name.value.title()} Agent starting specialized analysis...',
                    data={}
                )
                event_broadcaster.emit(workflow_id, evt_agent_start)
                yield evt_agent_start

            tasks = {name: agent_instances[name].execute(state) for name in group_1}
            done = await asyncio.gather(*[tasks[name] for name in group_1], return_exceptions=True)

            for i, agent_name in enumerate(group_1):
                result = done[i]
                if isinstance(result, Exception):
                    state.errors.append(f'{agent_name.value}: {str(result)}')
                    evt_agent_err = WorkflowEvent(
                        event_type=WorkflowEventType.AGENT_COMPLETED,
                        workflow_id=workflow_id,
                        agent=agent_name.value,
                        message=f'{agent_name.value.title()} Agent failed: {str(result)}',
                        data={'error': str(result)}
                    )
                    event_broadcaster.emit(workflow_id, evt_agent_err)
                    yield evt_agent_err
                else:
                    all_results[agent_name] = result
                    state.findings.extend(result.findings)
                    state.evidence.extend(result.evidence)
                    evt_agent_done = WorkflowEvent(
                        event_type=WorkflowEventType.AGENT_COMPLETED,
                        workflow_id=workflow_id,
                        agent=agent_name.value,
                        message=f'{agent_name.value.title()} Agent completed. Found {len(result.findings)} signals.',
                        data={'findings_count': len(result.findings), 'metrics': result.metrics}
                    )
                    event_broadcaster.emit(workflow_id, evt_agent_done)
                    yield evt_agent_done

        # Sequential Group 2: Recovery
        if AgentName.RECOVERY in selected_agents:
            evt_rec_start = WorkflowEvent(
                event_type=WorkflowEventType.AGENT_STARTED,
                workflow_id=workflow_id,
                agent='recovery',
                message='Recovery Agent starting payment recovery ranking...',
                data={}
            )
            event_broadcaster.emit(workflow_id, evt_rec_start)
            yield evt_rec_start

            recovery_result = await agent_instances[AgentName.RECOVERY].execute(state)
            all_results[AgentName.RECOVERY] = recovery_result
            state.findings.extend(recovery_result.findings)
            state.evidence.extend(recovery_result.evidence)

            evt_rec_done = WorkflowEvent(
                event_type=WorkflowEventType.AGENT_COMPLETED,
                workflow_id=workflow_id,
                agent='recovery',
                message=f'Recovery Agent completed. {len(recovery_result.proposed_actions)} candidate actions proposed.',
                data={'findings_count': len(recovery_result.findings), 'actions_count': len(recovery_result.proposed_actions), 'metrics': recovery_result.metrics}
            )
            event_broadcaster.emit(workflow_id, evt_rec_done)
            yield evt_rec_done

        # 4. Root-Cause Synthesis
        root_causes = self._synthesize_root_causes(state, all_results)
        state.root_causes = root_causes

        synthesis = self._generate_synthesis(state, all_results)
        state.synthesis = synthesis

        evt_synth = WorkflowEvent(
            event_type=WorkflowEventType.SYNTHESIS_COMPLETED,
            workflow_id=workflow_id,
            agent='supervisor',
            message='Multi-agent synthesis and attribution breakdown complete.',
            data={'root_causes': [rc.model_dump() for rc in root_causes], 'synthesis': synthesis[:500]}
        )
        event_broadcaster.emit(workflow_id, evt_synth)
        yield evt_synth

        # 5. Deterministic Policy Evaluation & Execution Pipeline
        all_proposed_actions = []
        for result in all_results.values():
            all_proposed_actions.extend(result.proposed_actions)

        idempotency = IdempotencyChecker(self.db)
        persisted_actions = []

        for action in all_proposed_actions:
            is_dup, prev_result = idempotency.check(action.idempotency_key)
            if is_dup:
                evt_dup = WorkflowEvent(
                    event_type=WorkflowEventType.POLICY_EVALUATED,
                    workflow_id=workflow_id,
                    agent='supervisor',
                    message=f'Action {action.action_type} already executed (Idempotency Key duplicate).',
                    data={'idempotency_key': action.idempotency_key, 'decision': 'DUPLICATE'}
                )
                event_broadcaster.emit(workflow_id, evt_dup)
                yield evt_dup
                continue

            policy_result = policy_engine.evaluate_action(
                action_type=action.action_type,
                params=action.params,
                merchant_context={'merchant_id': merchant_id, 'is_suspended': False}
            )
            decision_str = policy_result.decision.value if hasattr(policy_result.decision, 'value') else str(policy_result.decision)
            conditions_list = getattr(policy_result, 'conditions_failed', getattr(policy_result, 'conditions', []))
            action.policy_result = {'decision': decision_str, 'reason': policy_result.reason, 'conditions': conditions_list}

            if decision_str == 'REJECT':
                action.status = ActionStatus.REJECTED
                evt_pol = WorkflowEvent(
                    event_type=WorkflowEventType.POLICY_EVALUATED,
                    workflow_id=workflow_id,
                    agent='supervisor',
                    message=f'Action {action.action_type} REJECTED by policy: {policy_result.reason}',
                    data={'decision': 'REJECT', 'reason': policy_result.reason}
                )
                event_broadcaster.emit(workflow_id, evt_pol)
                yield evt_pol
                persisted = self._persist_action(action, workflow_id, merchant_id)
                persisted_actions.append(persisted)

            elif decision_str == 'REQUIRE_APPROVAL':
                action.status = ActionStatus.PENDING_APPROVAL
                persisted = self._persist_action(action, workflow_id, merchant_id)
                persisted_actions.append(persisted)
                evt_appr = WorkflowEvent(
                    event_type=WorkflowEventType.APPROVAL_REQUIRED,
                    workflow_id=workflow_id,
                    agent='supervisor',
                    message=f'Action {action.action_type} requires human approval (INR {action.amount_at_risk:,.0f}).',
                    data={'action_id': action.id, 'amount': action.amount_at_risk}
                )
                event_broadcaster.emit(workflow_id, evt_appr)
                yield evt_appr

            else:
                action.status = ActionStatus.APPROVED
                evt_app = WorkflowEvent(
                    event_type=WorkflowEventType.POLICY_EVALUATED,
                    workflow_id=workflow_id,
                    agent='supervisor',
                    message=f'Action {action.action_type} APPROVED by policy. Dispatching automated safe execution...',
                    data={'decision': 'ALLOW'}
                )
                event_broadcaster.emit(workflow_id, evt_app)
                yield evt_app

                persisted = self._persist_action(action, workflow_id, merchant_id)
                if persisted:
                    persisted_actions.append(persisted)
                    exec_res = await execution_engine.execute_action(self.db, persisted, user_id=None)
                    if exec_res.get('success'):
                        evt_exec = WorkflowEvent(
                            event_type=WorkflowEventType.ACTION_EXECUTED,
                            workflow_id=workflow_id,
                            agent='execution_engine',
                            message=f'Auto-executed {action.action_type} (INR {action.amount_at_risk:,.0f}). Gateway status: SUCCESS',
                            data=exec_res
                        )
                        event_broadcaster.emit(workflow_id, evt_exec)
                        yield evt_exec

        state.actions = [a.model_dump() for a in all_proposed_actions[:10]]
        self._persist_findings(state, workflow_id, merchant_id)
        self._update_workflow_status(workflow_id, 'completed', state)

        evt_done = WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_COMPLETED,
            workflow_id=workflow_id,
            agent='supervisor',
            message='Workflow and policy execution complete.',
            data={
                'findings': len(state.findings),
                'actions': len(persisted_actions),
                'pending_approval': sum(1 for a in persisted_actions if a and a.status == 'PENDING_APPROVAL'),
                'auto_approved': sum(1 for a in persisted_actions if a and a.status in ['APPROVED', 'SUCCESS'])
            }
        )
        event_broadcaster.emit(workflow_id, evt_done)
        yield evt_done

    def _synthesize_root_causes(self, state: AgentState, results: dict) -> list[RootCauseContribution]:
        causes = []
        for agent_name, result in results.items():
            for finding in result.findings:
                if finding.severity in [Severity.HIGH, Severity.CRITICAL]:
                    metric_change = 0.0
                    if finding.metric_previous and finding.metric_previous > 0 and finding.metric_current is not None:
                        metric_change = abs((finding.metric_current - finding.metric_previous) / finding.metric_previous)
                    causes.append(RootCauseContribution(
                        cause=finding.finding[:200],
                        contribution_pct=round(metric_change * 100, 1),
                        agent=agent_name,
                        evidence_ids=finding.evidence_ids
                    ))
        total = sum(c.contribution_pct for c in causes)
        if total > 0:
            for c in causes:
                c.contribution_pct = round((c.contribution_pct / total) * 100, 1)
        return causes

    def _generate_synthesis(self, state: AgentState, results: dict) -> str:
        lines = ['## Multi-Agent Financial Diagnostic Summary\n']
        for finding in state.findings:
            if finding.severity in [Severity.HIGH, Severity.CRITICAL]:
                lines.append(f'**{finding.agent.value.upper()}**: {finding.finding}')
                if finding.recommended_action:
                    lines.append(f'  → Recommended Action: {finding.recommended_action}')
                lines.append('')
        if state.root_causes:
            lines.append('\n**Attribution Breakdown:**')
            for rc in state.root_causes:
                lines.append(f'- {rc.agent.value.title()}: {rc.contribution_pct:.1f}% — {rc.cause[:150]}')
        return '\n'.join(lines)

    def _persist_action(self, action: ProposedAction, workflow_id: str, merchant_id: str):
        try:
            from app.database.models.action import Action
            status_val = action.status.value if hasattr(action.status, 'value') else str(action.status)
            risk_val = action.risk_level.value if hasattr(action.risk_level, 'value') else str(action.risk_level)

            existing = self.db.query(Action).filter(Action.idempotency_key == action.idempotency_key).first()
            if existing:
                existing.workflow_id = workflow_id
                existing.policy_result = action.policy_result
                self.db.commit()
                return existing

            db_action = Action(
                id=action.id,
                workflow_id=workflow_id,
                merchant_id=merchant_id,
                action_type=action.action_type,
                description=action.description,
                action_params=action.params,
                risk_level=risk_val,
                status=status_val,
                policy_result=action.policy_result,
                idempotency_key=action.idempotency_key,
                amount_at_risk=action.amount_at_risk,
                expected_outcome=action.expected_outcome,
                evidence_ids=action.evidence_ids or [],
                test_mode=True
            )
            self.db.add(db_action)
            self.db.commit()
            return db_action
        except Exception as e:
            self.db.rollback()
            self.logger.warning(f'Failed to persist action: {e}')
            return None

    def _persist_findings(self, state: AgentState, workflow_id: str, merchant_id: str):
        try:
            from app.database.models.agent_finding import AgentFinding
            for f in state.findings:
                sev_val = f.severity.value if hasattr(f.severity, 'value') else str(f.severity)
                agent_val = f.agent.value if hasattr(f.agent, 'value') else str(f.agent)
                db_f = AgentFinding(
                    id=f.id,
                    workflow_id=workflow_id,
                    merchant_id=merchant_id,
                    agent=agent_val,
                    finding=f.finding,
                    severity=sev_val,
                    evidence_ids=f.evidence_ids or [],
                    confidence=f.confidence,
                    recommended_action=f.recommended_action,
                    metric_label=f.metric_label,
                    metric_previous=f.metric_previous,
                    metric_current=f.metric_current,
                    metric_unit=f.metric_unit
                )
                self.db.merge(db_f)
            self.db.commit()
        except Exception as e:
            self.logger.warning(f'Failed to persist findings: {e}')

    def _update_workflow_status(self, workflow_id: str, status: str, state: AgentState = None):
        try:
            from app.database.models.workflow import Workflow
            wf = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf and state:
                wf = Workflow(
                    id=workflow_id,
                    merchant_id=state.merchant_id,
                    conversation_id=state.conversation_id,
                    user_query=state.user_query,
                    status=status
                )
                self.db.add(wf)
            elif wf:
                wf.status = status
                if status == 'completed':
                    wf.completed_at = datetime.now(timezone.utc)
                if state:
                    wf.state_snapshot = state.model_dump(mode='json')
            self.db.commit()
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            self.logger.warning(f'Failed to update workflow status: {e}')
