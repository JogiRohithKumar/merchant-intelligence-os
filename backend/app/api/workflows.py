from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.database.models.workflow import Workflow
from app.api.auth import get_current_user, verify_token
from app.orchestration.events import event_broadcaster
import json
import asyncio

router = APIRouter()

@router.get('/workflows')
def list_workflows(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    workflows = db.query(Workflow).filter(
        Workflow.merchant_id == user.merchant_id
    ).order_by(Workflow.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            'id': w.id,
            'status': w.status.value if hasattr(w.status, 'value') else str(w.status),
            'user_query': w.user_query,
            'intent': w.intent,
            'created_at': w.created_at.isoformat() if w.created_at else None,
            'completed_at': w.completed_at.isoformat() if w.completed_at else None
        }
        for w in workflows
    ]

@router.get('/workflows/{workflow_id}')
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # Enforce strict merchant tenant isolation
    w = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.merchant_id == user.merchant_id
    ).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Workflow not found')
    
    findings = [
        {
            'id': f.id,
            'agent': f.agent,
            'finding': f.finding,
            'severity': f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
            'confidence': f.confidence,
            'evidence_ids': f.evidence_ids or [],
            'recommended_action': f.recommended_action,
            'metric_label': f.metric_label,
            'metric_previous': f.metric_previous,
            'metric_current': f.metric_current,
            'metric_unit': f.metric_unit,
            'created_at': f.created_at.isoformat() if f.created_at else None
        }
        for f in w.findings
    ] if w.findings else []

    actions = [
        {
            'id': a.id,
            'action_type': a.action_type,
            'status': a.status.value if hasattr(a.status, 'value') else str(a.status),
            'description': a.description,
            'amount_at_risk': a.amount_at_risk,
            'risk_level': a.risk_level.value if hasattr(a.risk_level, 'value') else str(a.risk_level),
            'idempotency_key': a.idempotency_key,
            'policy_result': a.policy_result,
            'expected_outcome': a.expected_outcome,
            'execution_result': a.execution_result
        }
        for a in w.actions
    ] if w.actions else []
    
    return {
        'id': w.id,
        'status': w.status.value if hasattr(w.status, 'value') else str(w.status),
        'user_query': w.user_query,
        'intent': w.intent,
        'execution_plan': w.execution_plan,
        'state_snapshot': w.state_snapshot,
        'created_at': w.created_at.isoformat() if w.created_at else None,
        'completed_at': w.completed_at.isoformat() if w.completed_at else None,
        'findings': findings,
        'actions': actions
    }

@router.get('/workflows/{workflow_id}/events')
async def stream_events(
    workflow_id: str,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Support token in Query or Header for standard EventSource
    raw_token = token
    if not raw_token and authorization and authorization.startswith('Bearer '):
        raw_token = authorization.replace('Bearer ', '')

    # In production, require valid token
    token_data = None
    if raw_token:
        token_data = verify_token(raw_token)

    # Verify workflow exists and enforce tenant isolation if token present
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Workflow not found')

    if token_data and w.merchant_id != token_data.merchant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden: Cross-merchant stream access blocked')

    async def event_generator():
        try:
            async for event in event_broadcaster.stream(workflow_id):
                yield f'data: {json.dumps(event.model_dump(mode="json"))}\n\n'
        except asyncio.CancelledError:
            pass
        finally:
            yield 'data: {"event_type": "stream_closed"}\n\n'

    return StreamingResponse(event_generator(), media_type='text/event-stream')
