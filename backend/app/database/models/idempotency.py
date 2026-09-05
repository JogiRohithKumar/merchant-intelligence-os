from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from app.database.base import Base, generate_uuid

class IdempotencyKey(Base):
    __tablename__ = 'idempotency_keys'

    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String(64), unique=True, nullable=False, index=True)
    merchant_id = Column(String, nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    status = Column(String(50), default='SUCCESS')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
