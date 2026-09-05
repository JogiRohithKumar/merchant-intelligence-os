from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class OrderStatus(str, enum.Enum):
    pending = 'pending'
    processing = 'processing'
    completed = 'completed'
    cancelled = 'cancelled'
    refunded = 'refunded'

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False, index=True)
    order_number = Column(String(100), unique=True, nullable=False)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.pending)
    subtotal = Column(Numeric(12, 2), default=0)
    discount = Column(Numeric(12, 2), default=0)
    tax = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant', back_populates='orders')
    customer = relationship('Customer')
    transactions = relationship('Transaction', back_populates='order')
    items = relationship('OrderItem', back_populates='order')

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False, index=True)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    
    order = relationship('Order', back_populates='items')
    product = relationship('Product')
