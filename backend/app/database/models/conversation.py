from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class MessageRole(str, enum.Enum):
    user = 'user'
    assistant = 'assistant'
    system = 'system'

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    messages = relationship('Message', back_populates='conversation')

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False)
    role = Column(SAEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    conversation = relationship('Conversation', back_populates='messages')
