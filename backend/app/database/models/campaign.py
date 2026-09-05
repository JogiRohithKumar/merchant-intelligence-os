from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float, Integer, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class CampaignType(str, enum.Enum):
    reactivation = 'reactivation'
    upsell = 'upsell'
    cross_sell = 'cross_sell'
    new_customer = 'new_customer'

class CampaignStatus(str, enum.Enum):
    draft = 'draft'
    simulated = 'simulated'
    pending_approval = 'pending_approval'
    active = 'active'
    completed = 'completed'
    cancelled = 'cancelled'

class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    campaign_type = Column(SAEnum(CampaignType), nullable=False)
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.draft)
    target_segment = Column(String(10), nullable=True)
    target_count = Column(Integer, nullable=True)
    budget = Column(Numeric(12, 2), nullable=True)
    expected_conversion_rate = Column(Float, nullable=True)
    expected_revenue = Column(Float, nullable=True)
    expected_roi = Column(Float, nullable=True)
    actual_conversion_rate = Column(Float, nullable=True)
    actual_revenue = Column(Float, nullable=True)
    actual_roi = Column(Float, nullable=True)
    simulation_results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activated_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant', back_populates='campaigns')
