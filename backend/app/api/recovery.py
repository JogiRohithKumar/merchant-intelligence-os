from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user
from app.agents.tools.recovery_tools import get_recovery_funnel
from app.database.models.action import Action, ActionStatus

router = APIRouter()

@router.get('/recovery/candidates')
def get_candidates(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not user.merchant_id:
        return {
            'detected': 0,
            'detected_amount': 0.0,
            'eligible': 0,
            'eligible_amount': 0.0,
            'expected_recovery': 0.0,
            'risk_blocked': 0,
            'retry_blocked': 0,
            'low_prob_blocked': 0,
            'fraud_blocked': 0,
            'blocked_amount': 0.0,
            'candidates': []
        }
    return get_recovery_funnel(db, user.merchant_id)

@router.get('/recovery/metrics')
def get_metrics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not user.merchant_id:
        return {'recovery_rate': 0.0, 'total_recovered': 0.0}

    from sqlalchemy import func
    from app.database.models.payment_attempt import PaymentAttempt

    total_attempts = db.query(func.count(PaymentAttempt.id)).filter(
        PaymentAttempt.merchant_id == user.merchant_id,
        PaymentAttempt.is_retry == True
    ).scalar() or 0

    successful_retries = db.query(func.count(PaymentAttempt.id)).filter(
        PaymentAttempt.merchant_id == user.merchant_id,
        PaymentAttempt.is_retry == True,
        PaymentAttempt.status == 'success'
    ).scalar() or 0

    total_recovered = db.query(func.sum(PaymentAttempt.amount)).filter(
        PaymentAttempt.merchant_id == user.merchant_id,
        PaymentAttempt.is_retry == True,
        PaymentAttempt.status == 'success'
    ).scalar() or 0.0

    recovery_rate = (successful_retries / total_attempts * 100.0) if total_attempts > 0 else 0.0

    return {
        'recovery_rate': round(recovery_rate, 2),
        'total_recovered': float(total_recovered)
    }

@router.post('/recovery/{action_id}/approve')
def approve_action(action_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    action = db.query(Action).filter(Action.id == action_id, Action.merchant_id == user.merchant_id).first()
    if not action:
        raise HTTPException(status_code=404, detail='Not found')
    action.status = ActionStatus.APPROVED
    db.commit()
    return {'status': 'success'}

@router.post('/recovery/{action_id}/reject')
def reject_action(action_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    action = db.query(Action).filter(Action.id == action_id, Action.merchant_id == user.merchant_id).first()
    if not action:
        raise HTTPException(status_code=404, detail='Not found')
    action.status = ActionStatus.REJECTED
    db.commit()
    return {'status': 'success'}
