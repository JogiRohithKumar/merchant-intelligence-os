from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class SettlementStatus(str, enum.Enum):
    matched = 'matched'
    partially_matched = 'partially_matched'
    unmatched = 'unmatched'
    under_investigation = 'under_investigation'

class MatchStatus(str, enum.Enum):
    matched = 'matched'
    partial = 'partial'
    unmatched = 'unmatched'

class Settlement(Base):
    __tablename__ = 'settlements'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    settlement_ref = Column(String(100), unique=True, nullable=False)
    gateway = Column(String(50), default='razorpay')
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    settlement_date = Column(DateTime, nullable=False, index=True)
    gross_amount = Column(Numeric(15, 2), nullable=False)
    fees = Column(Numeric(12, 2), default=0)
    tax = Column(Numeric(12, 2), default=0)
    refunds_total = Column(Numeric(12, 2), default=0)
    chargebacks_total = Column(Numeric(12, 2), default=0)
    net_amount = Column(Numeric(15, 2), nullable=False)
    expected_amount = Column(Numeric(15, 2), nullable=True)
    discrepancy = Column(Numeric(12, 2), default=0)
    status = Column(SAEnum(SettlementStatus), default=SettlementStatus.matched)
    has_mismatch = Column(Boolean, default=False)  # flag for injected anomaly
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant', back_populates='settlements')
    items = relationship('SettlementItem', back_populates='settlement')

class SettlementItem(Base):
    __tablename__ = 'settlement_items'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    settlement_id = Column(String, ForeignKey('settlements.id'), nullable=False, index=True)
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=True, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    item_type = Column(String(30), default='transaction')  # transaction/fee/refund/chargeback/adjustment
    amount = Column(Numeric(12, 2), nullable=False)
    match_status = Column(SAEnum(MatchStatus), default=MatchStatus.unmatched)
    match_level = Column(String(10), nullable=True)  # '1', '2', '3', '4', or None
    match_confidence = Column(Float, nullable=True)
    discrepancy_amount = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    settlement = relationship('Settlement', back_populates='items')
    transaction = relationship('Transaction', back_populates='settlement_items')
