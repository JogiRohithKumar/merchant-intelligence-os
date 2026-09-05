from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models.action import Action, ActionStatus
from app.execution.engine import execution_engine

router = APIRouter()

class RejectRequest(BaseModel):
    reason: Optional[str] = None

@router.get('/actions')
def list_actions(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    query = db.query(Action).filter(Action.merchant_id == user.merchant_id)
    if status:
        query = query.filter(Action.status == status)
    items = query.order_by(Action.proposed_at.desc()).offset(skip).limit(limit).all()
    return [{
        'id': a.id,
        'action_type': a.action_type,
        'status': a.status.value if hasattr(a.status, 'value') else a.status,
        'description': a.description,
        'risk_level': a.risk_level.value if hasattr(a.risk_level, 'value') else a.risk_level,
        'amount_at_risk': a.amount_at_risk,
        'idempotency_key': a.idempotency_key,
        'policy_result': a.policy_result,
        'expected_outcome': a.expected_outcome,
        'execution_result': a.execution_result,
        'execution_error': a.execution_error,
        'proposed_at': a.proposed_at.isoformat() if a.proposed_at else None,
        'executed_at': a.executed_at.isoformat() if a.executed_at else None,
        'test_mode': a.test_mode
    } for a in items]

@router.post('/actions/{action_id}/approve')
async def approve_action(
    action_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # 1. Enforce merchant isolation
    action = db.query(Action).filter(
        Action.id == action_id,
        Action.merchant_id == user.merchant_id
    ).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Action not found')

    # 2. Enforce Role Authorization (Phase 7 & 16)
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ['merchant_admin', 'operator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized: Only merchant administrators or operators can approve financial recovery actions.'
        )

    # 3. Check State Transitions
    if action.status == ActionStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot approve a rejected action.')

    if action.status == ActionStatus.SUCCESS:
        return {'status': 'success', 'message': 'Action was already executed.', 'action_id': action.id}

    # 4. Dispatch through ActionExecutionEngine
    user_identifier = getattr(user, 'id', getattr(user, 'user_id', None))
    result = await execution_engine.execute_action(db, action, user_id=user_identifier)
    return {'status': 'success', 'execution': result}

@router.post('/actions/{action_id}/reject')
def reject_action(
    action_id: str,
    req: RejectRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    action = db.query(Action).filter(
        Action.id == action_id,
        Action.merchant_id == user.merchant_id
    ).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Action not found')

    action.status = ActionStatus.REJECTED
    action.execution_error = req.reason or 'Rejected by administrator'
    db.commit()
    return {'status': 'success', 'action_id': action.id}
