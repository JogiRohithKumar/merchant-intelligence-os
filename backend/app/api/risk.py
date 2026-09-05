from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models.risk_event import RiskEvent
from app.database.models.chargeback import Chargeback
from app.engines.risk_ml import get_model_metrics, score_transaction, RiskScore

router = APIRouter()

@router.get('/risk/events')
def list_risk_events(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user=Depends(get_current_user)):
    events = db.query(RiskEvent).filter(RiskEvent.merchant_id == user.merchant_id).order_by(RiskEvent.created_at.desc()).offset(skip).limit(limit).all()
    return [{'id': e.id, 'event_type': e.event_type.value, 'severity': e.severity.value, 'risk_score': e.risk_score, 'created_at': e.created_at} for e in events]

@router.get('/risk/model/metrics')
def model_metrics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_model_metrics()

@router.post('/risk/score')
def score_single_transaction(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Run live machine learning inference on a candidate transaction."""
    tx_id = payload.get('transaction_id')
    score_res = score_transaction(payload, transaction_id=tx_id)
    return {
        'transaction_id': score_res.transaction_id,
        'risk_score': score_res.score,
        'label': score_res.label,
        'confidence': score_res.confidence,
        'explanation': score_res.explanation,
        'features': score_res.features,
        'model_version': score_res.model_version,
        'provenance': score_res.provenance
    }

@router.get('/risk/chargebacks')
def list_chargebacks(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cbs = db.query(Chargeback).filter(Chargeback.merchant_id == user.merchant_id).order_by(Chargeback.created_at.desc()).offset(skip).limit(limit).all()
    return [{'id': c.id, 'amount': float(c.amount), 'status': c.status.value, 'reason_code': c.reason_code, 'created_at': c.created_at} for c in cbs]
