import hmac
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger
from app.database.models.webhook_event import WebhookEvent
from app.database.models.transaction import Transaction, TransactionStatus, TransactionType
from app.database.models.payment_attempt import PaymentAttempt, AttemptStatus, FailureReason
from app.database.models.chargeback import Chargeback, ChargebackStatus
from app.database.models.settlement import Settlement, SettlementStatus

logger = get_logger('integrations.razorpay.webhook')

class RazorpayWebhookHandler:
    def verify_signature(self, body: bytes, signature: str, secret: str = None) -> bool:
        """Verifies Razorpay HMAC-SHA256 signature."""
        webhook_secret = secret or settings.RAZORPAY_WEBHOOK_SECRET
        if not webhook_secret or not signature:
            return False
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

    def ingest_event(
        self,
        db: Session,
        raw_body: bytes,
        signature: str,
        merchant_id: str,
        headers: Dict[str, Any] = None,
        secret: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Ingests and normalizes an external provider event.
        Guarantees idempotency and raw audit preservation.
        Returns: (success, status, result_dict)
        """
        # 1. Parse JSON payload
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except Exception as e:
            return False, 'malformed_json', {'error': f'Invalid JSON payload: {e}'}

        event_type = payload.get('event', 'unknown')
        # Razorpay sends x-razorpay-event-id in headers
        header_event_id = (headers or {}).get('x-razorpay-event-id') or (headers or {}).get('X-Razorpay-Event-Id')
        external_event_id = header_event_id or payload.get('id') or payload.get('event_id') or (
            payload.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
        )
        if not external_event_id:
            # Generate deterministic event fingerprint if provider didn't send event ID
            external_event_id = f"evt_{hashlib.sha256(raw_body).hexdigest()[:24]}"

        # 2. Check Signature (Strict HMAC-SHA256 constant-time verification)
        webhook_secret = secret or settings.RAZORPAY_WEBHOOK_SECRET
        sig_valid = self.verify_signature(raw_body, signature, secret=webhook_secret)
        
        # In non-DEMO/production mode, invalid or missing signature is strictly rejected
        if not sig_valid:
            if not (settings.DEMO_MODE and not signature):
                logger.warning(f"Webhook signature rejected for event {external_event_id}")
                return False, 'invalid_signature', {'error': 'Invalid or missing HMAC signature'}


        # 3. Deduplication Check (Idempotency across incoming events)
        existing = db.query(WebhookEvent).filter(WebhookEvent.external_event_id == external_event_id).first()
        if existing:
            logger.info(f"Duplicate webhook event ignored: {external_event_id}")
            return True, 'duplicate', {'event_id': existing.id, 'status': 'duplicate'}



        # 4. Record raw webhook event
        event_record = WebhookEvent(
            merchant_id=merchant_id,
            source='razorpay',
            event_type=event_type,
            external_event_id=external_event_id,
            payload=payload,
            headers=headers or {},
            signature=signature,
            signature_valid=sig_valid,
            status='received',
            received_at=datetime.now(timezone.utc)
        )
        db.add(event_record)
        db.flush()

        # 5. Normalization Pipeline
        try:
            self._normalize_and_persist(db, event_type, payload, merchant_id)
            event_record.status = 'processed'
            event_record.processed_at = datetime.now(timezone.utc)
            db.commit()
            return True, 'processed', {'event_id': event_record.id, 'event_type': event_type}
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to normalize webhook event {external_event_id}: {e}")
            event_record.status = 'failed'
            event_record.error_message = str(e)
            db.commit()
            return False, 'processing_failed', {'error': str(e)}

    def _normalize_and_persist(self, db: Session, event_type: str, payload: dict, merchant_id: str):
        """Normalizes external event into internal core financial entities."""
        entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        if not entity:
            entity = payload.get('entity', {})

        if event_type in ['payment.captured', 'payment.authorized']:
            tx_id = entity.get('id', f"tx_{hashlib.sha256(str(payload).encode()).hexdigest()[:16]}")
            amount = float(entity.get('amount', 0)) / 100.0  # paise to INR
            if amount == 0:
                amount = float(entity.get('amount_inr', 1000))
            
            # Upsert transaction
            tx = db.query(Transaction).filter(Transaction.gateway_transaction_id == tx_id).first()
            if not tx:
                tx = Transaction(
                    merchant_id=merchant_id,
                    transaction_type=TransactionType.payment,
                    amount=Decimal(str(amount)),
                    currency=entity.get('currency', 'INR'),
                    status=TransactionStatus.success,
                    gateway='razorpay',
                    gateway_transaction_id=tx_id,
                    payment_method=entity.get('method', 'upi'),
                    device_type='mobile',
                    data_source='LIVE_RAZORPAY',
                    created_at=datetime.now(timezone.utc),
                    settled_at=datetime.now(timezone.utc)
                )
                db.add(tx)
                db.flush()
            else:
                tx.status = TransactionStatus.success
                tx.data_source = 'LIVE_RAZORPAY'

            # Log successful attempt
            attempt = PaymentAttempt(
                transaction_id=tx.id,
                merchant_id=merchant_id,
                status=AttemptStatus.success,
                amount=Decimal(str(amount)),
                gateway='razorpay',
                gateway_response_code='200'
            )
            db.add(attempt)

        elif event_type == 'payment.failed':
            tx_id = entity.get('id', f"tx_fail_{hashlib.sha256(str(payload).encode()).hexdigest()[:16]}")
            amount = float(entity.get('amount', 0)) / 100.0
            error_code = entity.get('error_code', 'gateway_timeout')
            
            tx = Transaction(
                merchant_id=merchant_id,
                transaction_type=TransactionType.payment,
                amount=Decimal(str(amount)),
                currency=entity.get('currency', 'INR'),
                status=TransactionStatus.failed,
                gateway='razorpay',
                gateway_transaction_id=tx_id,
                payment_method=entity.get('method', 'card'),
                risk_score=0.25,
                data_source='LIVE_RAZORPAY',
                created_at=datetime.now(timezone.utc)
            )
            db.add(tx)
            db.flush()

            attempt = PaymentAttempt(
                transaction_id=tx.id,
                merchant_id=merchant_id,
                status=AttemptStatus.failed,
                failure_reason=FailureReason.gateway_timeout if 'timeout' in error_code else FailureReason.card_declined,
                amount=Decimal(str(amount)),
                gateway='razorpay',
                gateway_response_code=error_code
            )
            db.add(attempt)

        elif 'dispute' in event_type:
            dispute_id = entity.get('id', f"disp_{uuid.uuid4().hex[:12]}")
            amount = float(entity.get('amount', 0)) / 100.0
            cb = Chargeback(
                merchant_id=merchant_id,
                transaction_id=entity.get('payment_id', 'unknown'),
                chargeback_ref=dispute_id,
                amount=Decimal(str(amount)),
                reason_code=entity.get('reason_code', '4853'),
                status=ChargebackStatus.received,
                created_at=datetime.now(timezone.utc)
            )
            db.add(cb)

razorpay_webhook_handler = RazorpayWebhookHandler()
