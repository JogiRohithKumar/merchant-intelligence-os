import hashlib
import json
import threading
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database.models.idempotency import IdempotencyKey
from app.database.models.action import Action
from app.core.logging import get_logger

logger = get_logger('policy.idempotency')
_in_memory_locks = {}
_lock_mutex = threading.Lock()

def generate_idempotency_key(merchant_id: str, action: str, resource_id_or_params: Any, workflow_id: Optional[str] = None) -> str:
    """Generate a deterministic 64-char SHA-256 hash."""
    if isinstance(resource_id_or_params, dict):
        serialized = json.dumps(resource_id_or_params, sort_keys=True)
    else:
        serialized = str(resource_id_or_params)
    
    parts = [merchant_id, action, serialized]
    if workflow_id:
        parts.append(workflow_id)
    payload = ":".join(parts)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

class IdempotencyChecker:
    def __init__(self, db: Session):
        self.db = db

    def check(self, key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Returns (is_duplicate, previous_record_dict_or_None)."""
        try:
            # Check Action table
            existing_action = self.db.query(Action).filter(Action.idempotency_key == key).first()
            if existing_action and existing_action.status in ['SUCCESS', 'EXECUTING', Action.status]:
                status_val = existing_action.status.value if hasattr(existing_action.status, 'value') else str(existing_action.status)
                return True, {'status': status_val, 'action_id': existing_action.id, 'result': existing_action.execution_result}
            
            # Check IdempotencyKey table
            ik = self.db.query(IdempotencyKey).filter(IdempotencyKey.key == key).first()
            if ik:
                return True, {'status': ik.status, 'action_type': ik.action_type}
        except Exception as e:
            logger.warning(f"Error during idempotency check: {e}")

        return False, None

    def acquire_lock(self, key: str, merchant_id: str, action_type: str) -> bool:
        """
        Thread-safe and DB-unique atomic lock acquisition.
        Returns True if lock acquired, False if key already exists or currently running.
        """
        with _lock_mutex:
            if key in _in_memory_locks:
                return False
            _in_memory_locks[key] = True

        try:
            # First check existing completed or executing
            existing = self.db.query(IdempotencyKey).filter(IdempotencyKey.key == key).first()
            if existing:
                with _lock_mutex:
                    _in_memory_locks.pop(key, None)
                return False

            new_lock = IdempotencyKey(
                key=key,
                merchant_id=merchant_id,
                action_type=action_type,
                status='EXECUTING'
            )
            self.db.add(new_lock)
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            with _lock_mutex:
                _in_memory_locks.pop(key, None)
            return False
        except Exception as e:
            self.db.rollback()
            with _lock_mutex:
                _in_memory_locks.pop(key, None)
            logger.warning(f"Failed to acquire idempotency lock: {e}")
            return False

    def release_lock(self, key: str, final_status: str = 'SUCCESS'):
        """Releases memory lock and marks persistent status."""
        with _lock_mutex:
            _in_memory_locks.pop(key, None)
        try:
            lock = self.db.query(IdempotencyKey).filter(IdempotencyKey.key == key).first()
            if lock:
                lock.status = final_status
                self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to update idempotency status: {e}")
