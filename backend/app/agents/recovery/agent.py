import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.schemas.state import AgentState, AgentName, Severity
from app.schemas.action import ProposedAction, ActionRiskLevel, ActionStatus
from app.schemas.finding import AgentResult
from app.agents.base import BaseAgent
from app.agents.tools.recovery_tools import get_failed_payments, get_recovery_funnel, propose_retry_action
from app.engines.recovery_scoring import rank_candidates
from app.core.config import settings
from app.core.logging import get_logger
import hashlib

logger = get_logger('agent.recovery')

SYSTEM_PROMPT = """
You are the Recovery Agent of Merchant Intelligence OS.
Your objective is to recover legitimate merchant revenue at risk.

You MUST:
1. Get failed payments using the get_failed_payments tool.
2. Calculate recovery probability using calculate_recovery_probability tool.
3. Compute Expected Recovery Value = amount * P(recovery) for each candidate.
4. Rank candidates by Expected Recovery Value descending.
5. Only propose retry actions for candidates with P(recovery) > 0.3.
6. Include evidence IDs for all proposed actions.
7. Report candidates excluded by risk and policy.
8. NEVER execute actions - only propose them.
9. Track: detected, risk_filtered, policy_allowed, attempted, recovered.

You MUST NOT:
- Invent recovery amounts
- Execute actions directly
- Override risk or policy decisions
- Fabricate recovery metrics
"""

class RecoveryAgent(BaseAgent):
    def __init__(self, db: Session, merchant_id: str):
        super().__init__(AgentName.RECOVERY, db, merchant_id)
    
    async def _run(self, state: AgentState) -> AgentResult:
        findings = []
        evidence = []
        proposed_actions = []
        metrics = {}
        
        # 1. Get failed payments from DB
        failed_payments = get_failed_payments(self.db, self.merchant_id, limit=2000)
        
        # 2. Score and rank all candidates
        scored = rank_candidates(failed_payments)
        eligible = [s for s in scored if s.is_eligible]
        excluded = [s for s in scored if not s.is_eligible]
        
        total_failed_amount = sum(s.amount for s in scored)
        eligible_amount = sum(s.amount for s in eligible)
        expected_recovery = sum(s.expected_recovery_value for s in eligible)
        
        metrics['recovery_funnel'] = {
            'detected': len(scored),
            'detected_amount': round(total_failed_amount, 2),
            'eligible': len(eligible),
            'eligible_amount': round(eligible_amount, 2),
            'expected_recovery': round(expected_recovery, 2),
            'excluded': len(excluded),
            'exclusion_breakdown': {
                'risk_blocked': sum(1 for s in excluded if s.exclusion_reason and 'risk_score' in s.exclusion_reason),
                'retry_blocked': sum(1 for s in excluded if s.exclusion_reason and 'retry_count' in s.exclusion_reason),
                'low_probability': sum(1 for s in excluded if s.exclusion_reason and 'probability' in s.exclusion_reason),
                'fraud_blocked': sum(1 for s in excluded if s.exclusion_reason and 'fraud' in s.exclusion_reason),
            }
        }
        
        # Create evidence
        funnel_evidence = self._create_evidence(
            type_='recovery_analysis',
            description=f'Recovery analysis: {len(scored)} failed payments detected. {len(eligible)} eligible for retry. Expected recovery: INR {expected_recovery:,.0f}',
            source='recovery_engine:rank_candidates',
            amount=expected_recovery
        )
        evidence.append(funnel_evidence)
        
        if len(scored) > 0:
            findings.append(self._create_finding(
                finding_text=f'{len(scored)} failed payments totaling INR {total_failed_amount:,.0f} detected. {len(eligible)} eligible for recovery worth INR {eligible_amount:,.0f}. Expected recovery value: INR {expected_recovery:,.0f}.',
                severity=Severity.HIGH if expected_recovery > 100_000 else Severity.MEDIUM,
                confidence=0.87,
                evidence_ids=[funnel_evidence.id],
                recommended_action=f'Initiate recovery retry for {len(eligible)} eligible failed payments.',
                metric_label='Recoverable Revenue',
                metric_curr=expected_recovery,
                metric_unit='INR'
            ))
        
        # 3. Propose retry actions for top eligible candidates
        MAX_AUTO_ACTIONS = 50
        for candidate in eligible[:MAX_AUTO_ACTIONS]:
            # Deterministic idempotency key tied to transaction attempt, NOT workflow ID
            idempotency_key = hashlib.sha256(
                f'{self.merchant_id}:{candidate.transaction_id}:retry_payment:attempt_{candidate.retry_count + 1}'.encode()
            ).hexdigest()
            
            # Risk level based on amount and risk score
            if candidate.amount > settings.MAX_AUTO_RETRY_AMOUNT_INR or candidate.risk_score > 0.4:
                risk_level = ActionRiskLevel.MEDIUM
            else:
                risk_level = ActionRiskLevel.LOW
            
            action = ProposedAction(
                action_type='retry_payment',
                description=f'Retry failed payment of INR {candidate.amount:,.0f} (P(recovery)={candidate.recovery_probability:.2f}, Expected: INR {candidate.expected_recovery_value:,.0f})',
                params={
                    'transaction_id': candidate.transaction_id,
                    'payment_attempt_id': candidate.payment_attempt_id,
                    'amount': candidate.amount,
                    'retry_count': candidate.retry_count,
                    'risk_score': candidate.risk_score,
                    'failure_reason': candidate.failure_reason,
                    'recovery_probability': candidate.recovery_probability
                },
                amount_at_risk=candidate.amount,
                expected_outcome=f'INR {candidate.expected_recovery_value:,.0f} recovered with {candidate.recovery_probability*100:.0f}% probability',
                evidence_ids=[funnel_evidence.id],
                idempotency_key=idempotency_key,
                risk_level=risk_level
            )
            proposed_actions.append(action)
        
        if excluded:
            exc_evidence = self._create_evidence(
                type_='recovery_exclusions',
                description=f'{len(excluded)} candidates excluded. Breakdown: {metrics["recovery_funnel"]["exclusion_breakdown"]}',
                source='recovery_engine:rank_candidates',
                amount=sum(s.amount for s in excluded)
            )
            evidence.append(exc_evidence)
        
        return AgentResult(
            agent=AgentName.RECOVERY,
            status='completed',
            findings=findings,
            evidence=evidence,
            proposed_actions=proposed_actions,
            metrics=metrics
        )
