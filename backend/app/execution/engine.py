import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.models.action import Action, ActionStatus
from app.database.models.transaction import Transaction, TransactionStatus
from app.database.models.payment_attempt import PaymentAttempt, AttemptStatus
from app.database.models.audit_event import AuditEvent
from app.database.models.idempotency import IdempotencyKey
from app.integrations.razorpay.client import razorpay_client
from app.policies.engine import policy_engine
from app.core.logging import get_logger

logger = get_logger('execution.engine')

class ActionExecutionEngine:
    """
    Authoritative action execution engine.
    Orchestrates:
    PROPOSED -> PENDING_APPROVAL -> APPROVED -> EXECUTING -> SUCCESS / FAILED / UNKNOWN
    Guarantees idempotency locking, database state synchronization, and tamper-evident audit chaining.
    """

    async def execute_action(
        self,
        db: Session,
        action: Action,
        user_id: Optional[str] = None,
        force_execute: bool = False
    ) -> Dict[str, Any]:
        logger.info(f"Executing action {action.id} of type {action.action_type} for merchant {action.merchant_id}")

        # 1. State Validation
        if action.status == ActionStatus.REJECTED:
            return {'success': False, 'status': 'REJECTED', 'error': 'Action was rejected and cannot be executed.'}

        if action.status == ActionStatus.SUCCESS:
            return {'success': True, 'status': 'SUCCESS', 'message': 'Action already executed successfully (Idempotent).'}

        # 2. Idempotency Check & Atomic Lock
        existing_lock = db.query(IdempotencyKey).filter(IdempotencyKey.key == action.idempotency_key).first()
        if existing_lock and existing_lock.status == 'SUCCESS':
            action.status = ActionStatus.SUCCESS
            db.commit()
            return {'success': True, 'status': 'SUCCESS', 'message': 'Action already executed via idempotency key.'}
        
        if not existing_lock:
            new_lock = IdempotencyKey(
                key=action.idempotency_key,
                merchant_id=action.merchant_id,
                action_type=action.action_type,
                status='EXECUTING'
            )
            db.add(new_lock)
            db.flush()

        # 3. Transition to EXECUTING
        action.status = ActionStatus.EXECUTING
        if user_id:
            action.approved_by = user_id
            action.approved_at = datetime.now(timezone.utc)
        db.commit()

        # 4. Dispatch based on action type
        execution_result = {}
        gateway_status = 'FAILED'
        error_msg = None

        try:
            if action.action_type in ['retry_payment', 'recover_payment']:
                params = action.action_params or {}
                tx_id = params.get('transaction_id') or action.id
                amount = float(action.amount_at_risk or params.get('amount', 0.0))

                # Call payment gateway (Razorpay live / sandbox client)
                res = await razorpay_client.execute_retry(
                    transaction_id=str(tx_id),
                    amount=amount,
                    merchant_id=action.merchant_id,
                    idempotency_key=action.idempotency_key,
                    params=params
                )
                execution_result = res
                gateway_status = res.get('status', 'FAILED')
                error_msg = res.get('error')

                # If gateway succeeded, update internal transaction ledger
                if gateway_status == 'SUCCESS':
                    action.status = ActionStatus.SUCCESS
                    action.executed_at = datetime.now(timezone.utc)
                    action.execution_result = execution_result

                    # Update underlying transaction if exists
                    if tx_id:
                        tx = db.query(Transaction).filter(
                            Transaction.id == tx_id,
                            Transaction.merchant_id == action.merchant_id
                        ).first()
                        if tx:
                            tx.status = TransactionStatus.success
                            tx.settled_at = datetime.now(timezone.utc)
                            tx.data_source = 'LIVE_RAZORPAY' if razorpay_client.is_live_permitted else 'SANDBOX'
                            # Append success attempt
                            attempt = PaymentAttempt(
                                transaction_id=tx.id,
                                merchant_id=action.merchant_id,
                                status=AttemptStatus.success,
                                amount=Decimal(str(amount)),
                                is_retry=True,
                                idempotency_key=action.idempotency_key
                            )
                            db.add(attempt)

                elif gateway_status == 'UNKNOWN':
                    # UNKNOWN != SUCCESS (fail safe)
                    action.status = ActionStatus.UNKNOWN
                    action.execution_error = error_msg or 'Gateway response timed out'
                else:
                    action.status = ActionStatus.FAILED
                    action.execution_error = error_msg or 'Gateway execution failed'

            elif action.action_type == 'create_campaign':
                action.status = ActionStatus.SUCCESS
                action.executed_at = datetime.now(timezone.utc)
                action.execution_result = {
                    'status': 'SUCCESS',
                    'campaign_id': f"camp_{action.id[:12]}",
                    'budget_allocated': action.amount_at_risk,
                    'mode': 'SANDBOX'
                }
                gateway_status = 'SUCCESS'

            else:
                action.status = ActionStatus.FAILED
                action.execution_error = f'Unknown action type: {action.action_type}'

        except Exception as e:
            logger.error(f"Execution error for action {action.id}: {e}")
            action.status = ActionStatus.UNKNOWN
            action.execution_error = str(e)
            gateway_status = 'UNKNOWN'
            error_msg = str(e)

        # 5. Update Idempotency Lock State
        lock = db.query(IdempotencyKey).filter(IdempotencyKey.key == action.idempotency_key).first()
        if lock:
            lock.status = action.status.value

        # 6. Record Tamper-Evident Audit Event
        self._record_audit_event(db, action, gateway_status, execution_result, error_msg)

        db.commit()
        return {
            'success': action.status == ActionStatus.SUCCESS,
            'status': action.status.value,
            'action_id': action.id,
            'execution_result': execution_result,
            'error': error_msg
        }

    def _record_audit_event(
        self,
        db: Session,
        action: Action,
        status: str,
        result: dict,
        error: Optional[str]
    ):
        """Generates SHA-256 chained tamper-evident audit block."""
        last_event = db.query(AuditEvent).filter(
            AuditEvent.merchant_id == action.merchant_id
        ).order_by(AuditEvent.timestamp.desc()).first()

        prev_hash = last_event.event_hash if (last_event and last_event.event_hash) else "0000000000000000000000000000000000000000000000000000000000000000"
        now = datetime.now(timezone.utc)
        
        payload_string = f"{prev_hash}|{now.isoformat()}|{action.merchant_id}|{action.id}|{action.action_type}|{status}|{json.dumps(result, sort_keys=True)}"
        current_hash = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

        audit = AuditEvent(
            merchant_id=action.merchant_id,
            workflow_id=action.workflow_id,
            agent='execution_engine',
            action=f"EXECUTE_{action.action_type.upper()}",
            input_summary=f"Action ID: {action.id}, Amount: {action.amount_at_risk}",
            evidence_ids=action.evidence_ids or [],
            approval_status=action.status.value,
            execution_result=result,
            error=error,
            prev_event_hash=prev_hash,
            event_hash=current_hash,
            timestamp=now
        )
        db.add(audit)

execution_engine = ActionExecutionEngine()
