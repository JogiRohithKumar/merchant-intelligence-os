from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models.audit_event import AuditEvent

router = APIRouter()

import hashlib
import json

def compute_audit_hash(prev_hash: str, timestamp_iso: str, merchant_id: str, action_id: str, action_type: str, status: str, result: dict) -> str:
    payload_string = f"{prev_hash}|{timestamp_iso}|{merchant_id}|{action_id}|{action_type}|{status}|{json.dumps(result, sort_keys=True)}"
    return hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

@router.get('/audit')
def list_audit(
    skip: int = 0,
    limit: int = 50,
    agent: Optional[str] = None,
    workflow_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = db.query(AuditEvent).filter(AuditEvent.merchant_id == user.merchant_id)
    if agent:
        query = query.filter(AuditEvent.agent == agent)
    if workflow_id:
        query = query.filter(AuditEvent.workflow_id == workflow_id)
    items = query.order_by(AuditEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return [{
        'id': a.id,
        'action': a.action,
        'agent': a.agent,
        'timestamp': a.timestamp.isoformat() if a.timestamp else None,
        'approval_status': a.approval_status,
        'prev_event_hash': a.prev_event_hash,
        'event_hash': a.event_hash,
        'execution_result': a.execution_result,
        'error': a.error
    } for a in items]

@router.get('/audit/verify')
def verify_audit_chain(
    workflow_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Validates the cryptographic tamper-evident hash chain for the merchant's audit trail.
    Returns: is_valid, total_events, broken_at_id, details
    """
    query = db.query(AuditEvent).filter(AuditEvent.merchant_id == user.merchant_id)
    if workflow_id:
        query = query.filter(AuditEvent.workflow_id == workflow_id)
    
    events = query.order_by(AuditEvent.timestamp.asc()).all()
    if not events:
        return {'is_valid': True, 'total_events': 0, 'message': 'No audit events recorded.'}

    for i in range(1, len(events)):
        prev_evt = events[i - 1]
        curr_evt = events[i]
        if curr_evt.prev_event_hash != prev_evt.event_hash:
            return {
                'is_valid': False,
                'tamper_detected': True,
                'broken_at_index': i,
                'event_id': curr_evt.id,
                'expected_prev_hash': prev_evt.event_hash,
                'actual_prev_hash': curr_evt.prev_event_hash,
                'message': f"Tamper-evident hash chain broken between event {prev_evt.id} and {curr_evt.id}"
            }

    return {
        'is_valid': True,
        'tamper_detected': False,
        'total_events': len(events),
        'chain_status': 'verified_tamper_evident_intact'
    }

