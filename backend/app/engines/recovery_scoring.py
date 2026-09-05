"""
Deterministic Recovery Scoring Engine
P(recovery) is calculated from payment features.
Expected Recovery Value = amount * P(recovery)
Never uses LLM for calculation.
"""
from dataclasses import dataclass
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class RecoveryScore:
    payment_attempt_id: str
    transaction_id: str
    amount: float
    failure_reason: str
    retry_count: int
    risk_score: float
    recovery_probability: float
    expected_recovery_value: float
    rank_score: float
    recommendation: str
    is_eligible: bool  # passes basic filters
    exclusion_reason: Optional[str] = None

BASE_RECOVERY_PROBS = {
    'gateway_timeout': 0.72,
    'network_error': 0.68,
    'insufficient_funds': 0.35,
    'card_declined': 0.42,
    'expired_card': 0.15,
    'fraud_block': 0.05,
    'none': 0.50
}

MIN_RECOVERY_PROB = 0.30  # below this threshold, not worth retrying
MAX_RETRY_COUNT = 2       # policy limit
MAX_RISK_SCORE = 0.65     # policy limit

def calculate_recovery_probability(features: dict) -> float:
    """
    Deterministic formula based on failure features.
    Features: failure_reason, retry_count, risk_score, amount, customer_history_score, days_since_failure
    """
    failure_reason = features.get('failure_reason', 'card_declined')
    retry_count = features.get('retry_count', 0)
    risk_score = features.get('risk_score', 0.1)
    amount = float(features.get('amount', 1000))
    customer_history_score = features.get('customer_history_score', 0.5)  # 0-1, higher=better
    days_since_failure = features.get('days_since_failure', 1)
    
    p = BASE_RECOVERY_PROBS.get(failure_reason, 0.4)
    p -= retry_count * 0.18       # each retry reduces probability
    p -= risk_score * 0.30        # high risk reduces probability
    p += customer_history_score * 0.15  # good customer history increases
    if amount > 10_000: p -= 0.08  # large amounts harder to recover
    if days_since_failure > 7: p -= 0.12  # stale failures less recoverable
    if days_since_failure > 30: p -= 0.20
    
    return max(0.0, min(0.95, p))

def score_recovery_candidate(payment: dict) -> RecoveryScore:
    """Score a single failed payment for recovery."""
    amount = float(payment.get('amount', 0))
    if 'retry_count' in payment:
        retry_count = int(payment['retry_count'])
    else:
        retry_count = max(0, int(payment.get('attempt_number', 1)) - 1)
    risk_score = payment.get('risk_score', 0.1)
    failure_reason = payment.get('failure_reason', 'card_declined')
    
    features = {
        'failure_reason': failure_reason,
        'retry_count': retry_count,
        'risk_score': risk_score,
        'amount': amount,
        'customer_history_score': payment.get('customer_history_score', 0.5),
        'days_since_failure': payment.get('days_since_failure', 1)
    }
    
    prob = calculate_recovery_probability(features)
    expected_value = amount * prob
    rank_score = expected_value  # primary ranking by expected value
    
    # Eligibility check
    is_eligible = True
    exclusion_reason = None
    if retry_count >= MAX_RETRY_COUNT:
        is_eligible = False
        exclusion_reason = f'retry_count ({retry_count}) >= max ({MAX_RETRY_COUNT})'
    elif risk_score > MAX_RISK_SCORE:
        is_eligible = False
        exclusion_reason = f'risk_score ({risk_score:.2f}) > threshold ({MAX_RISK_SCORE})'
    elif prob < MIN_RECOVERY_PROB:
        is_eligible = False
        exclusion_reason = f'recovery_probability ({prob:.2f}) < minimum ({MIN_RECOVERY_PROB})'
    elif failure_reason == 'fraud_block':
        is_eligible = False
        exclusion_reason = 'fraud_block failures cannot be retried'
    
    if is_eligible:
        if prob > 0.6:
            recommendation = f'HIGH confidence recovery: schedule retry immediately. Expected: ₹{expected_value:,.0f}'
        else:
            recommendation = f'MEDIUM confidence: schedule retry with customer notification. Expected: ₹{expected_value:,.0f}'
    else:
        recommendation = f'Excluded: {exclusion_reason}'
    
    return RecoveryScore(
        payment_attempt_id=payment.get('id', ''),
        transaction_id=payment.get('transaction_id', ''),
        amount=amount,
        failure_reason=failure_reason,
        retry_count=retry_count,
        risk_score=risk_score,
        recovery_probability=round(prob, 4),
        expected_recovery_value=round(expected_value, 2),
        rank_score=round(rank_score, 2),
        recommendation=recommendation,
        is_eligible=is_eligible,
        exclusion_reason=exclusion_reason
    )

def rank_candidates(payments: list[dict]) -> list[RecoveryScore]:
    """Score and rank all candidates by expected recovery value."""
    scores = [score_recovery_candidate(p) for p in payments]
    return sorted(scores, key=lambda s: s.expected_recovery_value, reverse=True)

def calculate_recovery_metrics(candidates: list[RecoveryScore]) -> dict:
    """Calculate aggregate recovery funnel metrics."""
    total = len(candidates)
    eligible = [c for c in candidates if c.is_eligible]
    risk_blocked = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'risk_score' in c.exclusion_reason]
    retry_blocked = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'retry_count' in c.exclusion_reason]
    low_prob = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'probability' in c.exclusion_reason]
    fraud_blocked = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'fraud' in c.exclusion_reason]
    
    total_amount = sum(c.amount for c in candidates)
    eligible_amount = sum(c.amount for c in eligible)
    expected_recovery = sum(c.expected_recovery_value for c in eligible)
    
    return {
        'total_detected': total,
        'total_amount': round(total_amount, 2),
        'eligible': len(eligible),
        'eligible_amount': round(eligible_amount, 2),
        'expected_recovery': round(expected_recovery, 2),
        'risk_blocked': len(risk_blocked),
        'retry_blocked': len(retry_blocked),
        'low_probability_blocked': len(low_prob),
        'fraud_blocked': len(fraud_blocked),
        'total_blocked': total - len(eligible),
        'blocked_amount': round(total_amount - eligible_amount, 2)
    }
