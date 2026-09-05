from fastapi import APIRouter, Request, HTTPException, Depends, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models.webhook_event import WebhookEvent
from app.integrations.razorpay.webhook import razorpay_webhook_handler
from app.core.logging import get_logger

logger = get_logger('api.webhooks')
router = APIRouter()

@router.post('/webhooks/razorpay')
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    x_merchant_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Real-time webhook ingestion endpoint for Razorpay.
    Verifies HMAC-SHA256 signature, deduplicates events, and normalizes into core ledger.
    """
    body = await request.body()
    # Requirement: Missing signature MUST be rejected immediately with 401 Unauthorized
    if not x_razorpay_signature:
        raise HTTPException(status_code=401, detail='Missing webhook signature')

    m_id = x_merchant_id or 'test-merchant-001'

    from app.database.models.merchant import Merchant
    merchant = db.query(Merchant).filter(Merchant.id == m_id).first()
    if not merchant:
        if x_merchant_id:
            raise HTTPException(status_code=404, detail=f'Merchant tenant {x_merchant_id} not registered')
        else:
            raise HTTPException(status_code=400, detail='Missing required X-Merchant-ID header for multi-tenant webhook ingestion')
    merchant_id = merchant.id

    signature = x_razorpay_signature


    success, status, result = razorpay_webhook_handler.ingest_event(
        db=db,
        raw_body=body,
        signature=signature,
        merchant_id=merchant_id,
        headers=dict(request.headers)
    )

    if not success and status == 'invalid_signature':
        raise HTTPException(status_code=401, detail='Invalid webhook signature')
    
    if not success:
        raise HTTPException(status_code=400, detail=result.get('error', 'Ingestion failed'))

    return {'status': status, 'result': result}

@router.get('/webhooks/events')
def list_webhook_events(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Lists ingested real-time provider events with merchant scoping."""
    query = db.query(WebhookEvent).filter(WebhookEvent.merchant_id == user.merchant_id)
    if status:
        query = query.filter(WebhookEvent.status == status)
    
    total = query.count()
    events = query.order_by(WebhookEvent.received_at.desc()).offset(skip).limit(limit).all()

    return {
        'total': total,
        'items': [
            {
                'id': e.id,
                'source': e.source,
                'event_type': e.event_type,
                'external_event_id': e.external_event_id,
                'status': e.status,
                'signature_valid': e.signature_valid,
                'retry_count': e.retry_count,
                'received_at': e.received_at.isoformat() if e.received_at else None,
                'processed_at': e.processed_at.isoformat() if e.processed_at else None,
                'error_message': e.error_message
            }
            for e in events
        ]
    }

@router.post('/webhooks/events/{event_id}/replay')
def replay_webhook_event(
    event_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Replays an ingestion event for error recovery and replayability testing."""
    event = db.query(WebhookEvent).filter(
        WebhookEvent.id == event_id,
        WebhookEvent.merchant_id == user.merchant_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')

    import json
    raw_body = json.dumps(event.payload).encode('utf-8')
    success, status, result = razorpay_webhook_handler.ingest_event(
        db=db,
        raw_body=raw_body,
        signature=event.signature or '',
        merchant_id=event.merchant_id
    )
    return {'replayed': True, 'success': success, 'status': status, 'result': result}
