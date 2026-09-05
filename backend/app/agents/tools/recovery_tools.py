from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.logging import get_logger
from app.engines.recovery_scoring import score_recovery_candidate, rank_candidates, calculate_recovery_metrics, RecoveryScore

logger = get_logger('tools.recovery')

def get_failed_payments(db: Session, merchant_id: str, start_date: datetime = None, end_date: datetime = None, limit: int = 500) -> list[dict]:
    from app.database.models.payment_attempt import PaymentAttempt
    from app.database.models.customer import Customer
    
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    q = db.query(PaymentAttempt).filter(
        PaymentAttempt.merchant_id == merchant_id,
        PaymentAttempt.status == 'failed',
        PaymentAttempt.created_at >= start_date
    )
    if end_date:
        q = q.filter(PaymentAttempt.created_at <= end_date)
    
    attempts = q.order_by(PaymentAttempt.created_at.desc()).limit(limit).all()
    
    result = []
    now = datetime.now(timezone.utc)
    for a in attempts:
        days_since = (now - a.created_at.replace(tzinfo=timezone.utc) if a.created_at else timedelta(days=1)).days
        result.append({
            'id': a.id,
            'transaction_id': a.transaction_id,
            'amount': float(a.amount),
            'failure_reason': a.failure_reason.value,
            'attempt_number': a.attempt_number,
            'retry_count': max(0, a.attempt_number - 1),
            'risk_score': a.risk_score,
            'gateway': a.gateway,
            'is_retry': a.is_retry,
            'recovery_probability': a.recovery_probability,
            'expected_recovery_value': a.expected_recovery_value,
            'days_since_failure': days_since,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'customer_history_score': 0.5  # would join with customer table
        })
    return result

def get_recovery_funnel(db: Session, merchant_id: str, days: int = 30) -> dict:
    from app.database.models.payment_attempt import PaymentAttempt
    from app.engines.recovery_scoring import calculate_recovery_metrics
    
    payments = get_failed_payments(db, merchant_id, limit=2000)
    scored = rank_candidates(payments)
    metrics = calculate_recovery_metrics(scored)
    
    # Calculate totals from DB
    total_amount = sum(float(p['amount']) for p in payments)
    eligible = [s for s in scored if s.is_eligible]
    
    return {
        'detected': metrics['total_detected'],
        'detected_amount': metrics['total_amount'],
        'eligible': metrics['eligible'],
        'eligible_amount': metrics['eligible_amount'],
        'expected_recovery': metrics['expected_recovery'],
        'risk_blocked': metrics['risk_blocked'],
        'retry_blocked': metrics['retry_blocked'],
        'low_prob_blocked': metrics['low_probability_blocked'],
        'fraud_blocked': metrics['fraud_blocked'],
        'blocked_amount': metrics['blocked_amount'],
        'candidates': [{
            'id': s.payment_attempt_id,
            'transaction_id': s.transaction_id,
            'amount': s.amount,
            'failure_reason': s.failure_reason,
            'retry_count': s.retry_count,
            'recovery_probability': s.recovery_probability,
            'expected_value': s.expected_recovery_value,
            'risk_score': s.risk_score,
            'is_eligible': s.is_eligible,
            'exclusion_reason': s.exclusion_reason,
            'recommendation': s.recommendation
        } for s in scored[:50]]  # top 50
    }

def propose_retry_action(payment_id: str, transaction_id: str, amount: float, recovery_prob: float, workflow_id: str, merchant_id: str) -> dict:
    """Propose a retry action (does NOT execute, only proposes for policy evaluation)."""
    import hashlib
    idempotency_key = hashlib.sha256(f'{merchant_id}:{transaction_id}:retry_payment:{workflow_id}'.encode()).hexdigest()
    return {
        'action_type': 'retry_payment',
        'transaction_id': transaction_id,
        'payment_attempt_id': payment_id,
        'amount': amount,
        'recovery_probability': recovery_prob,
        'expected_recovery_value': round(amount * recovery_prob, 2),
        'idempotency_key': idempotency_key
    }
