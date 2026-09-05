from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.base import Base, generate_uuid

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), default='General')
    price = Column(Numeric(12, 2), nullable=False)
    cost = Column(Numeric(12, 2), nullable=True)
    inventory_count = Column(Integer, default=100)
    conversion_rate = Column(Float, default=0.042)
    avg_order_value = Column(Float, default=2500.0)
    is_active = Column(Boolean, default=True)
    is_anomalous = Column(Boolean, default=False)  # flags Product X
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant', back_populates='products')
