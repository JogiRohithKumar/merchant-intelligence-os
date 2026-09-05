from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from app.core.logging import get_logger

logger = get_logger('policy.engine')

class PolicyDecision(str, Enum):
    ALLOW = 'ALLOW'
    REQUIRE_APPROVAL = 'REQUIRE_APPROVAL'
    REJECT = 'REJECT'

@dataclass
class PolicyResult:
    decision: str  # 'ALLOW', 'REQUIRE_APPROVAL', 'REJECT'
    reason: str
    conditions_failed: List[str] = field(default_factory=list)
    audit_required: bool = True
    max_amount: Optional[float] = None
    required_approval_role: Optional[str] = None

class PolicyEngine:
    """
    Deterministic policy engine.
    Strictly enforces mathematical boundaries, circuit breakers, and safety thresholds.
    The LLM may explain decisions but can NEVER override this engine.
    """
    MAX_AUTO_RETRY_AMOUNT = 10_000.0
    MAX_RETRY_COUNT = 2
    MAX_RISK_SCORE_AUTO = 0.65
    MAX_CAMPAIGN_AUTO_BUDGET = 50_000.0

    PROHIBITED_ACTIONS = {
        'freeze_merchant_account',
        'unilateral_fee_change',
        'wipe_ledger',
        'force_delete',
        'bypass_compliance'
    }

    def evaluate(self, action_type: str, context: Optional[Dict[str, Any]] = None) -> PolicyResult:
        context = context or {}
        params = context.get('params', context)
        merchant_context = context.get('merchant_context', {})
        is_suspended = context.get('is_suspended', False) or merchant_context.get('is_suspended', False)

        # 1. Prohibited Destructive Actions
        if action_type in self.PROHIBITED_ACTIONS:
            return PolicyResult(
                decision=PolicyDecision.REJECT.value,
                reason=f'Action {action_type} is prohibited by governance safety policy.',
                conditions_failed=['prohibited_action']
            )

        # 2. Account Status Check
        if is_suspended:
            return PolicyResult(
                decision=PolicyDecision.REJECT.value,
                reason='Merchant account suspended: automated operations halted.',
                conditions_failed=['merchant_suspended']
            )

        # 3. Read-only Safe Operations
        if action_type in ['reconcile', 'forecast_cash', 'get_transactions', 'get_settlements', 'generate_chargeback_evidence']:
            return PolicyResult(
                decision=PolicyDecision.ALLOW.value,
                reason='Read-only safe analytical operation',
                conditions_failed=[]
            )

        # 4. Payment Retry Actions (Critical Financial Boundary)
        if action_type in ['retry_payment', 'recover_payment']:
            try:
                # If explicit None or invalid format, handle safely
                if params.get('risk_score') is None and 'risk_score' in params:
                    return PolicyResult(
                        decision=PolicyDecision.REJECT.value,
                        reason='Invalid None risk_score provided.',
                        conditions_failed=['invalid_risk_score']
                    )
                risk_score = float(params.get('risk_score', 0.0))

                if params.get('retry_count') is None and 'retry_count' in params:
                    return PolicyResult(
                        decision=PolicyDecision.REJECT.value,
                        reason='Invalid None retry_count provided.',
                        conditions_failed=['invalid_retry_count']
                    )
                retry_count = int(params.get('retry_count', 0))

                amount = float(params.get('amount', 0.0))
                if amount < 0:
                    return PolicyResult(
                        decision=PolicyDecision.REJECT.value,
                        reason='Invalid negative transaction amount.',
                        conditions_failed=['invalid_amount']
                    )
            except (ValueError, TypeError) as e:
                return PolicyResult(
                    decision=PolicyDecision.REJECT.value,
                    reason=f'Malformed parameter format: {e}',
                    conditions_failed=['malformed_parameters']
                )


            # Rule 1: Risk Boundary (risk_score <= 0.65)
            # 0.649999 -> ALLOW, 0.65 -> ALLOW, 0.650001 -> REJECT
            if risk_score > self.MAX_RISK_SCORE_AUTO:
                return PolicyResult(
                    decision=PolicyDecision.REJECT.value,
                    reason=f'ML risk score ({risk_score:.6f}) exceeds maximum allowable threshold ({self.MAX_RISK_SCORE_AUTO})',
                    conditions_failed=['risk_score_exceeds_threshold']
                )


            # Rule 2: Retry Circuit Breaker (retry_count <= 2)
            # 1 -> ALLOW, 2 -> ALLOW, 3 -> REJECT
            if retry_count > self.MAX_RETRY_COUNT:
                return PolicyResult(
                    decision=PolicyDecision.REJECT.value,
                    reason=f'Maximum retry count ({self.MAX_RETRY_COUNT}) exceeded (current attempts: {retry_count})',
                    conditions_failed=['retry_limit_reached', 'max_retries_exceeded']
                )

            # Rule 3: Financial Exposure Threshold (amount <= 10,000)
            # 9,999 -> ALLOW, 10,000 -> ALLOW, 10,001 -> REQUIRE_APPROVAL
            if amount > self.MAX_AUTO_RETRY_AMOUNT:
                return PolicyResult(
                    decision=PolicyDecision.REQUIRE_APPROVAL.value,
                    reason=f'Amount INR {amount:,.2f} exceeds auto-retry limit (INR {self.MAX_AUTO_RETRY_AMOUNT:,.0f}). Requires human sign-off.',
                    conditions_failed=['amount_above_auto_limit'],
                    required_approval_role='merchant_admin',
                    max_amount=amount
                )

            return PolicyResult(
                decision=PolicyDecision.ALLOW.value,
                reason='Payment retry approved: all safety boundaries verified',
                conditions_failed=[]
            )

        # 5. Growth Campaign Actions
        if action_type in ['create_campaign', 'launch_campaign']:
            budget = float(params.get('budget', 0.0))
            if budget > self.MAX_CAMPAIGN_AUTO_BUDGET:
                return PolicyResult(
                    decision=PolicyDecision.REQUIRE_APPROVAL.value,
                    reason=f'Campaign budget INR {budget:,.2f} exceeds auto-approval limit (INR {self.MAX_CAMPAIGN_AUTO_BUDGET:,.0f})',
                    conditions_failed=['budget_above_limit'],
                    required_approval_role='merchant_admin',
                    max_amount=budget
                )
            return PolicyResult(
                decision=PolicyDecision.ALLOW.value,
                reason='Campaign approved: within auto-budget limits',
                conditions_failed=[]
            )

        # 6. Unrecognized action type
        return PolicyResult(
            decision=PolicyDecision.REJECT.value,
            reason=f'Unknown or unpermitted action type: {action_type}',
            conditions_failed=['unknown_action']
        )

    def evaluate_action(self, action_type: str, params: Dict[str, Any], merchant_context: Dict[str, Any]) -> PolicyResult:
        context = {**params, 'merchant_context': merchant_context, 'params': params}
        return self.evaluate(action_type=action_type, context=context)

policy_engine = PolicyEngine()
