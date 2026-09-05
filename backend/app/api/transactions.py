from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models.transaction import Transaction, TransactionStatus

router = APIRouter()

@router.get('/transactions')
def list_transactions(skip: int = 0, limit: int = 50, status: Optional[str] = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    query = db.query(Transaction).filter(Transaction.merchant_id == user.merchant_id)
    if status:
        query = query.filter(Transaction.status == status)
    total = query.count()
    items = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        'total': total,
        'items': [
            {
                'id': t.id,
                'amount': float(t.amount),
                'status': t.status.value if hasattr(t.status, 'value') else t.status,
                'gateway': t.gateway,
                'payment_method': t.payment_method,
                'currency': t.currency,
                'risk_score': t.risk_score,
                'created_at': t.created_at
            } for t in items
        ]
    }

@router.get('/transactions/{tx_id}')
def get_transaction(tx_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.merchant_id == user.merchant_id).first()
    if not t:
        return {'error': 'Not found'}
    return {
        'id': t.id,
        'amount': float(t.amount),
        'status': t.status.value if hasattr(t.status, 'value') else t.status,
        'payment_attempts': [{'id': a.id, 'status': a.status, 'gateway': a.gateway} for a in t.payment_attempts],
        'risk_events': [{'id': r.id, 'event_type': r.event_type.value if hasattr(r.event_type, 'value') else r.event_type, 'severity': r.severity.value if hasattr(r.severity, 'value') else r.severity} for r in t.risk_events],
        'settlement_items': [{'id': s.id, 'amount': float(s.amount)} for s in t.settlement_items]
    }
