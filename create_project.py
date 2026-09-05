import os

ROOT_DIR = r"C:\Users\rohit\.gemini\antigravity\scratch\merchant-intelligence-os"

files = {
    "docker-compose.yml": """version: '3.9'
services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: merchant_os
      POSTGRES_USER: merchant_os
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-merchant_os_secret}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U merchant_os"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - merchant-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - merchant-net

  backend:
    build: ./backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      DATABASE_URL: postgresql://merchant_os:${POSTGRES_PASSWORD:-merchant_os_secret}@postgres:5432/merchant_os
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - model_data:/app/data/models
      - chroma_data:/app/data/chroma_db
    networks:
      - merchant-net

  worker:
    build: ./backend
    restart: unless-stopped
    command: celery -A app.workers.tasks worker --loglevel=info --concurrency=4
    env_file: .env
    environment:
      DATABASE_URL: postgresql://merchant_os:${POSTGRES_PASSWORD:-merchant_os_secret}@postgres:5432/merchant_os
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - model_data:/app/data/models
    networks:
      - merchant-net

  frontend:
    build: ./frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - merchant-net

volumes:
  postgres_data:
  model_data:
  chroma_data:

networks:
  merchant-net:
    driver: bridge
""",
    ".env.example": """APP_ENV=development
DATABASE_URL=sqlite:///./merchant_os.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-me-in-production-use-a-32-char-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
VECTOR_DB_PATH=./data/chroma_db
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=merchant-intelligence
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
DEMO_MODE=true
LOG_LEVEL=INFO
MAX_RETRY_COUNT=2
MAX_AUTO_RETRY_AMOUNT_INR=10000
MAX_RISK_SCORE_AUTO=0.65
MAX_CAMPAIGN_AUTO_BUDGET_INR=50000
""",
    "README.md": """# Merchant Intelligence OS

## Product Overview
Merchant Intelligence OS is a comprehensive platform for managing e-commerce operations, analyzing risk, managing payment recoveries, forecasting cash flow, and simulating growth strategies.

## Technology Stack
| Component | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Celery |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| Database | PostgreSQL (dev: SQLite) |
| Cache/Broker | Redis |
| ML/AI | scikit-learn, Gemini API |

## Local Setup
1. `cp .env.example .env`
2. `docker-compose up -d`
3. `docker-compose exec backend python seed.py`

## Limitations
- Simulated data only
- Real payment gateway integrations are mocked
""",
    "backend/Dockerfile": """FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data/chroma_db /app/data/models /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    "backend/requirements.txt": """fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
sqlalchemy==2.0.35
alembic==1.13.3
psycopg2-binary==2.9.9
aiosqlite==0.20.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
httpx==0.27.2
celery==5.4.0
redis==5.1.1
numpy==1.26.4
pandas==2.2.3
scikit-learn==1.5.2
joblib==1.4.2
python-dotenv==1.0.1
rich==13.9.2
typer==0.12.5
pytest==8.3.3
pytest-asyncio==0.24.0
faker==30.3.0
freezegun==1.5.1
annotated-types==0.7.0
email-validator==2.2.0
""",
    "backend/app/__init__.py": "",
    "backend/app/core/__init__.py": "",
    "backend/app/core/config.py": """from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    APP_ENV: str = 'development'
    DATABASE_URL: str = 'sqlite:///./merchant_os.db'
    REDIS_URL: str = 'redis://localhost:6379/0'
    JWT_SECRET: str = 'dev-secret-change-in-production'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = 'gemini-2.5-flash'
    VECTOR_DB_PATH: str = './data/chroma_db'
    FRONTEND_URL: str = 'http://localhost:3000'
    BACKEND_URL: str = 'http://localhost:8000'
    DEMO_MODE: bool = True
    LOG_LEVEL: str = 'INFO'
    MAX_RETRY_COUNT: int = 2
    MAX_AUTO_RETRY_AMOUNT_INR: float = 10000.0
    MAX_RISK_SCORE_AUTO: float = 0.65
    MAX_CAMPAIGN_AUTO_BUDGET_INR: float = 50000.0
    
    @property
    def is_demo_mode(self) -> bool:
        return self.DEMO_MODE
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == 'production'
    
    @property
    def database_url_sync(self) -> str:
        # For Alembic compatibility
        url = self.DATABASE_URL
        if 'postgresql+asyncpg' in url:
            return url.replace('postgresql+asyncpg', 'postgresql')
        return url

settings = Settings()
""",
    "backend/app/core/security.py": """from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from .config import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class TokenData(BaseModel):
    user_id: str
    merchant_id: str
    role: str
    email: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire, 'type': 'access'})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({'exp': expire, 'type': 'refresh'})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str, token_type: str = 'access') -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get('type') != token_type:
            return None
        return TokenData(
            user_id=payload['user_id'],
            merchant_id=payload['merchant_id'],
            role=payload['role'],
            email=payload['email']
        )
    except JWTError:
        return None

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
""",
    "backend/app/core/exceptions.py": """from fastapi import HTTPException, status

class MerchantNotFoundError(HTTPException):
    def __init__(self, merchant_id: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f'Merchant {merchant_id} not found')

class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = 'Not authorized to access this resource'):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class PolicyRejectionError(HTTPException):
    def __init__(self, reason: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f'Policy rejected action: {reason}')

class DuplicateActionError(HTTPException):
    def __init__(self, idempotency_key: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f'Action already executed. Idempotency key: {idempotency_key}')

class AgentExecutionError(HTTPException):
    def __init__(self, agent: str, error: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Agent {agent} failed: {error}')

class WorkflowNotFoundError(HTTPException):
    def __init__(self, workflow_id: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f'Workflow {workflow_id} not found')
""",
    "backend/app/core/logging.py": """import logging
import sys
from .config import settings

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return logger
""",
    "backend/app/database/__init__.py": "",
    "backend/app/database/base.py": """from sqlalchemy.orm import DeclarativeBase
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Base(DeclarativeBase):
    pass
""",
    "backend/app/database/session.py": """from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
from app.core.config import settings
from app.core.logging import get_logger
from .base import Base

logger = get_logger(__name__)

# Import all models to ensure they're registered
from app.database.models import *  # noqa

def create_db_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith('sqlite'):
        engine = create_engine(
            db_url,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=False
        )
        # Enable WAL mode for SQLite
        @event.listens_for(engine, 'connect')
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()
    else:
        engine = create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20, echo=False)
    return engine

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    logger.info('Initializing database tables...')
    Base.metadata.create_all(bind=engine)
    logger.info('Database tables initialized.')
""",
    "backend/app/database/models/__init__.py": """from .user import User
from .merchant import Merchant
from .customer import Customer
from .product import Product
from .order import Order, OrderItem
from .transaction import Transaction
from .payment_attempt import PaymentAttempt
from .chargeback import Chargeback
from .risk_event import RiskEvent
from .subscription import Subscription
from .settlement import Settlement, SettlementItem
from .campaign import Campaign
from .workflow import Workflow
from .agent_finding import AgentFinding
from .action import Action
from .audit_event import AuditEvent
from .conversation import Conversation, Message

__all__ = [
    'User', 'Merchant', 'Customer', 'Product', 'Order', 'OrderItem',
    'Transaction', 'PaymentAttempt', 'Chargeback', 'RiskEvent',
    'Subscription', 'Settlement', 'SettlementItem', 'Campaign',
    'Workflow', 'AgentFinding', 'Action', 'AuditEvent',
    'Conversation', 'Message'
]
""",
    "backend/app/database/models/user.py": """from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class UserRole(str, enum.Enum):
    merchant_admin = 'merchant_admin'
    finance_user = 'finance_user'
    risk_user = 'risk_user'
    operator = 'operator'

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.merchant_admin)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant', back_populates='users')
""",
    "backend/app/database/models/merchant.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class MerchantStatus(str, enum.Enum):
    active = 'active'
    suspended = 'suspended'

class Merchant(Base):
    __tablename__ = 'merchants'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    business_type = Column(String(100), default='ecommerce')
    country = Column(String(3), default='IN')
    currency = Column(String(3), default='INR')
    status = Column(SAEnum(MerchantStatus), default=MerchantStatus.active)
    monthly_revenue_baseline = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    users = relationship('User', back_populates='merchant')
    customers = relationship('Customer', back_populates='merchant')
    products = relationship('Product', back_populates='merchant')
    orders = relationship('Order', back_populates='merchant')
    transactions = relationship('Transaction', back_populates='merchant')
    settlements = relationship('Settlement', back_populates='merchant')
    chargebacks = relationship('Chargeback', back_populates='merchant')
    campaigns = relationship('Campaign', back_populates='merchant')
    workflows = relationship('Workflow', back_populates='merchant')
""",
    "backend/app/database/models/customer.py": """from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class CustomerSegment(str, enum.Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    external_id = Column(String(100), index=True)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    segment = Column(SAEnum(CustomerSegment), default=CustomerSegment.C)
    country = Column(String(3), default='IN')
    acquisition_channel = Column(String(50), default='organic')
    total_orders = Column(Integer, default=0)
    total_spend = Column(Float, default=0.0)
    last_order_at = Column(DateTime, nullable=True)
    risk_score = Column(Float, default=0.1)
    is_high_risk = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant', back_populates='customers')
    transactions = relationship('Transaction', back_populates='customer')
    chargebacks = relationship('Chargeback', back_populates='customer')
    subscriptions = relationship('Subscription', back_populates='customer')
""",
    "backend/app/database/models/product.py": """from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Numeric
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
""",
    "backend/app/database/models/order.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Integer
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
""",
    "backend/app/database/models/transaction.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class TransactionType(str, enum.Enum):
    payment = 'payment'
    refund = 'refund'
    chargeback = 'chargeback'
    adjustment = 'adjustment'

class TransactionStatus(str, enum.Enum):
    success = 'success'
    failed = 'failed'
    pending = 'pending'
    disputed = 'disputed'

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=True, index=True)
    order_id = Column(String, ForeignKey('orders.id'), nullable=True, index=True)
    transaction_type = Column(SAEnum(TransactionType), default=TransactionType.payment)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='INR')
    status = Column(SAEnum(TransactionStatus), default=TransactionStatus.pending, index=True)
    gateway = Column(String(50), default='razorpay')
    gateway_transaction_id = Column(String(200), unique=True, nullable=True, index=True)
    payment_method = Column(String(50), default='upi')
    country = Column(String(3), default='IN')
    device_type = Column(String(20), default='mobile')
    ip_address = Column(String(50), nullable=True)
    risk_score = Column(Float, default=0.1)
    is_anomaly_day = Column(Boolean, default=False)  # flags gateway degradation window
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    settled_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant', back_populates='transactions')
    customer = relationship('Customer', back_populates='transactions')
    order = relationship('Order', back_populates='transactions')
    payment_attempts = relationship('PaymentAttempt', back_populates='transaction')
    risk_events = relationship('RiskEvent', back_populates='transaction')
    settlement_items = relationship('SettlementItem', back_populates='transaction')
    chargebacks = relationship('Chargeback', back_populates='transaction')
""",
    "backend/app/database/models/payment_attempt.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class FailureReason(str, enum.Enum):
    insufficient_funds = 'insufficient_funds'
    card_declined = 'card_declined'
    gateway_timeout = 'gateway_timeout'
    fraud_block = 'fraud_block'
    expired_card = 'expired_card'
    network_error = 'network_error'
    none = 'none'

class AttemptStatus(str, enum.Enum):
    success = 'success'
    failed = 'failed'
    timeout = 'timeout'
    unknown = 'unknown'

class PaymentAttempt(Base):
    __tablename__ = 'payment_attempts'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    status = Column(SAEnum(AttemptStatus), default=AttemptStatus.failed)
    failure_reason = Column(SAEnum(FailureReason), default=FailureReason.none)
    amount = Column(Numeric(12, 2), nullable=False)
    gateway = Column(String(50), default='razorpay')
    gateway_response_code = Column(String(20), nullable=True)
    risk_score = Column(Float, default=0.1)
    is_retry = Column(Boolean, default=False)
    recovery_probability = Column(Float, nullable=True)
    expected_recovery_value = Column(Float, nullable=True)
    idempotency_key = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    transaction = relationship('Transaction', back_populates='payment_attempts')
    merchant = relationship('Merchant')
""",
    "backend/app/database/models/chargeback.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class ChargebackStatus(str, enum.Enum):
    received = 'received'
    under_review = 'under_review'
    won = 'won'
    lost = 'lost'
    reversed = 'reversed'

class Chargeback(Base):
    __tablename__ = 'chargebacks'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=False, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False, index=True)
    chargeback_ref = Column(String(100), unique=True, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='INR')
    reason_code = Column(String(20), nullable=False)
    reason_description = Column(Text, nullable=True)
    status = Column(SAEnum(ChargebackStatus), default=ChargebackStatus.received)
    evidence_submitted = Column(Boolean, default=False)
    evidence_deadline = Column(DateTime, nullable=True)
    is_segment_b = Column(Boolean, default=False)  # flag for injected anomaly
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant', back_populates='chargebacks')
    transaction = relationship('Transaction', back_populates='chargebacks')
    customer = relationship('Customer', back_populates='chargebacks')
""",
    "backend/app/database/models/risk_event.py": """from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, Enum as SAEnum, Text, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class RiskEventType(str, enum.Enum):
    fraud_alert = 'fraud_alert'
    velocity_breach = 'velocity_breach'
    anomaly = 'anomaly'
    abuse_ring = 'abuse_ring'
    device_fingerprint = 'device_fingerprint'
    chargeback_risk = 'chargeback_risk'

class RiskSeverity(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'

class RiskEvent(Base):
    __tablename__ = 'risk_events'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    transaction_id = Column(String, ForeignKey('transactions.id'), nullable=True, index=True)
    event_type = Column(SAEnum(RiskEventType), nullable=False)
    risk_score = Column(Float, nullable=False)
    severity = Column(SAEnum(RiskSeverity), nullable=False)
    features = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    is_false_positive = Column(Boolean, nullable=True)
    label = Column(Integer, nullable=True)  # 0=legitimate, 1=risky
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    merchant = relationship('Merchant')
    transaction = relationship('Transaction', back_populates='risk_events')
""",
    "backend/app/database/models/subscription.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class SubscriptionStatus(str, enum.Enum):
    active = 'active'
    paused = 'paused'
    cancelled = 'cancelled'
    failed = 'failed'

class BillingCycle(str, enum.Enum):
    weekly = 'weekly'
    monthly = 'monthly'
    annual = 'annual'

class RecoveryStatus(str, enum.Enum):
    none = 'none'
    in_progress = 'in_progress'
    recovered = 'recovered'
    abandoned = 'abandoned'

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False, index=True)
    plan_name = Column(String(100), nullable=False)
    status = Column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.active)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='INR')
    billing_cycle = Column(SAEnum(BillingCycle), default=BillingCycle.monthly)
    next_billing_date = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    last_failed_at = Column(DateTime, nullable=True)
    recovery_status = Column(SAEnum(RecoveryStatus), default=RecoveryStatus.none)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    merchant = relationship('Merchant')
    customer = relationship('Customer', back_populates='subscriptions')
""",
    "backend/app/database/models/settlement.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float
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
""",
    "backend/app/database/models/campaign.py": """from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Enum as SAEnum, Float, Integer, JSON
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
""",
    "backend/app/database/models/workflow.py": """from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class WorkflowStatus(str, enum.Enum):
    initializing = 'initializing'
    running = 'running'
    completed = 'completed'
    failed = 'failed'
    partial = 'partial'

class Workflow(Base):
    __tablename__ = 'workflows'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    conversation_id = Column(String(100), nullable=True, index=True)
    user_query = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    status = Column(SAEnum(WorkflowStatus), default=WorkflowStatus.initializing)
    execution_plan = Column(JSON, nullable=True)
    active_agents = Column(JSON, default=list)
    state_snapshot = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)
    
    merchant = relationship('Merchant', back_populates='workflows')
    findings = relationship('AgentFinding', back_populates='workflow')
    actions = relationship('Action', back_populates='workflow')
    audit_events = relationship('AuditEvent', back_populates='workflow')
""",
    "backend/app/database/models/agent_finding.py": """from sqlalchemy import Column, String, DateTime, Float, JSON, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class FindingSeverity(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'

class AgentFinding(Base):
    __tablename__ = 'agent_findings'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    agent = Column(String(50), nullable=False)
    finding = Column(Text, nullable=False)
    severity = Column(SAEnum(FindingSeverity), default=FindingSeverity.medium)
    evidence_ids = Column(JSON, default=list)
    confidence = Column(Float, default=0.5)
    recommended_action = Column(Text, nullable=True)
    metric_label = Column(String(100), nullable=True)
    metric_previous = Column(Float, nullable=True)
    metric_current = Column(Float, nullable=True)
    metric_unit = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    workflow = relationship('Workflow', back_populates='findings')
    merchant = relationship('Merchant')
""",
    "backend/app/database/models/action.py": """from sqlalchemy import Column, String, DateTime, Float, JSON, Text, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.base import Base, generate_uuid

class ActionStatus(str, enum.Enum):
    PROPOSED = 'PROPOSED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    EXECUTING = 'EXECUTING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    UNKNOWN = 'UNKNOWN'

class ActionRiskLevel(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    prohibited = 'prohibited'

class Action(Base):
    __tablename__ = 'actions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    action_params = Column(JSON, nullable=True)
    risk_level = Column(SAEnum(ActionRiskLevel), default=ActionRiskLevel.medium)
    status = Column(SAEnum(ActionStatus), default=ActionStatus.PROPOSED)
    policy_result = Column(JSON, nullable=True)
    idempotency_key = Column(String(64), unique=True, nullable=False, index=True)
    execution_result = Column(JSON, nullable=True)
    execution_error = Column(Text, nullable=True)
    amount_at_risk = Column(Float, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    evidence_ids = Column(JSON, default=list)
    proposed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    approved_by = Column(String, ForeignKey('users.id'), nullable=True)
    test_mode = Column(Boolean, default=True)
    
    workflow = relationship('Workflow', back_populates='actions')
    merchant = relationship('Merchant')
    approver = relationship('User')
""",
    "backend/app/database/models/audit_event.py": """from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.base import Base, generate_uuid

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    # IMMUTABLE - never update rows in this table
    
    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey('merchants.id'), nullable=False, index=True)
    conversation_id = Column(String(100), nullable=True)
    workflow_id = Column(String, ForeignKey('workflows.id'), nullable=True, index=True)
    agent = Column(String(50), nullable=True, index=True)
    action = Column(String(200), nullable=False)
    input_summary = Column(Text, nullable=True)
    evidence_ids = Column(JSON, default=list)
    recommendation = Column(Text, nullable=True)
    policy_result = Column(JSON, nullable=True)
    approval_status = Column(String(30), nullable=True)
    execution_result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    merchant = relationship('Merchant')
    workflow = relationship('Workflow', back_populates='audit_events')
""",
    "backend/app/database/models/conversation.py": """from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SAEnum
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
""",
    "backend/app/synthetic/__init__.py": "",
    "backend/app/synthetic/generator.py": '''"""
Deterministic Synthetic Merchant Data Generator
Seed: 42 — always reproducible

Ground-truth anomalies injected:
1. Days 30-35: Payment failure rate 22.4% (baseline: 2.1%) - gateway degradation
2. Segment B: Chargeback rate 4.7% (baseline: 0.8%) - fraud ring
3. Product X (SKU: PROD-X-001): Conversion rate 2.1% (baseline: 4.2%) - pricing mismatch
4. Settlement on day 60: net_amount short by INR 78,000 - settlement mismatch
"""
import random
import uuid
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from faker import Faker
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.core.logging import get_logger

SEED = 42
random.seed(SEED)
fake = Faker('en_IN')
Faker.seed(SEED)

logger = get_logger(__name__)

# Config
NUM_CUSTOMERS = 10_000
NUM_PRODUCTS = 500
NUM_DAYS = 90
NUM_SUBSCRIPTIONS = 1_000

# Anomaly parameters
ANOMALY_START_DAY = 30
ANOMALY_END_DAY = 35
BASELINE_FAILURE_RATE = 0.021
ANOMALY_FAILURE_RATE = 0.224
SEGMENT_B_CB_RATE = 0.047
BASELINE_CB_RATE = 0.008
PRODUCT_X_CONVERSION = 0.021
BASELINE_CONVERSION = 0.042
SETTLEMENT_MISMATCH_INR = 78_000

PAYMENT_METHODS = ['upi', 'card', 'netbanking', 'wallet', 'emi']
GATEWAYS = ['razorpay', 'payu', 'cashfree']
COUNTRIES = ['IN', 'US', 'GB', 'SG', 'AE']
DEVICES = ['mobile', 'desktop', 'tablet']
CATEGORIES = ['Electronics', 'Apparel', 'FMCG', 'Books', 'Home', 'Sports']
CHANNELS = ['organic', 'paid_search', 'social', 'email', 'referral', 'direct']
FAILURE_REASONS = ['gateway_timeout', 'card_declined', 'insufficient_funds', 'network_error', 'expired_card', 'fraud_block']
CB_REASON_CODES = ['4853', '4855', '4863', '10.4', '13.1', '13.9']

def rnd_amount(low, high):
    # Round to nearest 50
    raw = random.uniform(low, high)
    return round(raw / 50) * 50

def rnd_bool(prob):
    return random.random() < prob

def generate_all_data(db: Session) -> dict:
    """
    Main entry point. Generates all synthetic data and persists to database.
    Returns summary counts.
    """
    from app.database.models import (
        Merchant, User, Customer, Product, Order, OrderItem,
        Transaction, PaymentAttempt, Chargeback, RiskEvent,
        Subscription, Settlement, SettlementItem, Campaign
    )
    
    logger.info('Starting synthetic data generation (seed=42)...')
    now = datetime.now(timezone.utc)
    base_date = now - timedelta(days=NUM_DAYS)
    
    # --- MERCHANT ---
    merchant = Merchant(
        id='merchant-bharat-001',
        name='Bharat Commerce Pvt Ltd',
        business_type='ecommerce',
        country='IN',
        currency='INR',
        status='active',
        monthly_revenue_baseline=Decimal('3240000')
    )
    db.merge(merchant)
    
    # --- DEMO USER ---
    user = User(
        id='user-demo-admin-001',
        email='demo@merchant.com',
        hashed_password=get_password_hash('demo123'),
        full_name='Priya Sharma',
        role='merchant_admin',
        merchant_id='merchant-bharat-001'
    )
    db.merge(user)
    db.flush()
    logger.info('Merchant and demo user created.')
    
    # --- CUSTOMERS ---
    customers = []
    segments = ['A', 'B', 'C', 'D']
    seg_weights = [0.15, 0.20, 0.40, 0.25]  # A=premium, B=fraud-prone, C=standard, D=inactive
    for i in range(NUM_CUSTOMERS):
        seg = random.choices(segments, weights=seg_weights)[0]
        risk = 0.05 if seg == 'A' else (0.35 if seg == 'B' else (0.1 if seg == 'C' else 0.08))
        risk += random.uniform(-0.02, 0.02)
        risk = max(0.0, min(1.0, risk))
        c = Customer(
            id=f'cust-{i:06d}',
            merchant_id='merchant-bharat-001',
            external_id=f'EXT-{i:06d}',
            email=fake.email(),
            full_name=fake.name(),
            segment=seg,
            country=random.choices(COUNTRIES, weights=[0.85,0.06,0.04,0.03,0.02])[0],
            acquisition_channel=random.choices(CHANNELS, weights=[0.3,0.2,0.15,0.15,0.1,0.1])[0],
            total_orders=0,
            total_spend=0.0,
            last_order_at=None,
            risk_score=round(risk, 3),
            is_high_risk=risk > 0.25
        )
        customers.append(c)
        db.add(c)
    db.flush()
    logger.info(f'{NUM_CUSTOMERS} customers created.')
    
    # --- PRODUCTS ---
    products = []
    for i in range(NUM_PRODUCTS):
        cat = random.choice(CATEGORIES)
        price = rnd_amount(500, 15000) if cat == 'Electronics' else rnd_amount(200, 5000)
        is_product_x = (i == 0)  # Product X is always index 0
        p = Product(
            id='product-x-001' if is_product_x else f'prod-{i:05d}',
            merchant_id='merchant-bharat-001',
            sku='PROD-X-001' if is_product_x else f'SKU-{i:05d}',
            name='Bharat Smart LED TV 43" (Product X)' if is_product_x else f'{fake.word().capitalize()} {cat} Item {i}',
            category=cat,
            price=Decimal(str(price)),
            cost=Decimal(str(round(price * 0.6, 2))),
            inventory_count=random.randint(0, 500),
            conversion_rate=PRODUCT_X_CONVERSION if is_product_x else round(BASELINE_CONVERSION + random.uniform(-0.01, 0.02), 4),
            avg_order_value=float(price) * 1.1,
            is_active=True,
            is_anomalous=is_product_x
        )
        products.append(p)
        db.add(p)
    db.flush()
    logger.info(f'{NUM_PRODUCTS} products created.')
    
    # --- ORDERS + TRANSACTIONS ---
    total_transactions = 0
    total_failed_payments = 0
    total_chargebacks = 0
    chargeback_records = []
    transaction_records = []
    
    for day_offset in range(NUM_DAYS):
        current_date = base_date + timedelta(days=day_offset)
        # Volume varies by day-of-week
        dow = current_date.weekday()
        daily_volume = int(random.gauss(1200, 150))
        if dow in [5, 6]:  # weekend boost
            daily_volume = int(daily_volume * 1.3)
        
        is_anomaly_day = ANOMALY_START_DAY <= day_offset <= ANOMALY_END_DAY
        failure_rate = ANOMALY_FAILURE_RATE if is_anomaly_day else BASELINE_FAILURE_RATE
        
        for _ in range(daily_volume):
            customer = random.choice(customers)
            product = random.choice(products)
            amount = rnd_amount(500, 25000)
            hour = random.choices(range(24), weights=_hour_weights())[0]
            txn_time = current_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59), tzinfo=timezone.utc)
            
            is_failed = rnd_bool(failure_rate)
            status = 'failed' if is_failed else 'success'
            gw = random.choices(GATEWAYS, weights=[0.6, 0.25, 0.15])[0]
            method = random.choices(PAYMENT_METHODS, weights=[0.45, 0.30, 0.12, 0.08, 0.05])[0]
            
            # Risk score
            base_risk = customer.risk_score
            if is_anomaly_day: base_risk += 0.15
            if amount > 15000: base_risk += 0.1
            if method == 'card' and customer.segment == 'B': base_risk += 0.2
            risk = max(0.0, min(1.0, base_risk + random.gauss(0, 0.05)))
            
            txn_id = f'txn-{uuid.uuid4().hex[:16]}'
            order_id = f'ord-{uuid.uuid4().hex[:12]}'
            order_num = f'ORD-{day_offset:03d}-{_:04d}'
            
            order = Order(
                id=order_id,
                merchant_id='merchant-bharat-001',
                customer_id=customer.id,
                order_number=order_num,
                status='completed' if not is_failed else 'pending',
                subtotal=Decimal(str(amount)),
                discount=Decimal('0'),
                tax=Decimal(str(round(amount * 0.18, 2))),
                total=Decimal(str(round(amount * 1.18, 2))),
                created_at=txn_time
            )
            db.add(order)
            
            txn = Transaction(
                id=txn_id,
                merchant_id='merchant-bharat-001',
                customer_id=customer.id,
                order_id=order_id,
                transaction_type='payment',
                amount=Decimal(str(amount)),
                currency='INR',
                status=status,
                gateway=gw,
                gateway_transaction_id=f'gw-{uuid.uuid4().hex[:20]}',
                payment_method=method,
                country=customer.country,
                device_type=random.choice(DEVICES),
                ip_address=fake.ipv4(),
                risk_score=round(risk, 3),
                is_anomaly_day=is_anomaly_day,
                created_at=txn_time,
                settled_at=txn_time + timedelta(days=2) if not is_failed else None
            )
            db.add(txn)
            transaction_records.append(txn)
            total_transactions += 1
            
            if is_failed:
                retry_count = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
                failure_reason = random.choices(
                    FAILURE_REASONS,
                    weights=[0.35, 0.25, 0.15, 0.1, 0.1, 0.05] if is_anomaly_day else [0.1, 0.3, 0.25, 0.15, 0.15, 0.05]
                )[0]
                recovery_prob = _calc_recovery_prob(failure_reason, retry_count, risk, amount)
                attempt = PaymentAttempt(
                    id=f'pa-{uuid.uuid4().hex[:16]}',
                    transaction_id=txn_id,
                    merchant_id='merchant-bharat-001',
                    attempt_number=retry_count + 1,
                    status='failed',
                    failure_reason=failure_reason,
                    amount=Decimal(str(amount)),
                    gateway=gw,
                    gateway_response_code=_gateway_code(failure_reason),
                    risk_score=round(risk, 3),
                    is_retry=(retry_count > 0),
                    recovery_probability=round(recovery_prob, 4),
                    expected_recovery_value=round(amount * recovery_prob, 2),
                    created_at=txn_time
                )
                db.add(attempt)
                total_failed_payments += 1
            
            # Chargebacks
            if not is_failed:
                cb_rate = SEGMENT_B_CB_RATE if customer.segment == 'B' else BASELINE_CB_RATE
                if rnd_bool(cb_rate):
                    cb = Chargeback(
                        id=f'cb-{uuid.uuid4().hex[:16]}',
                        merchant_id='merchant-bharat-001',
                        transaction_id=txn_id,
                        customer_id=customer.id,
                        chargeback_ref=f'CB-{uuid.uuid4().hex[:12].upper()}',
                        amount=Decimal(str(amount)),
                        currency='INR',
                        reason_code=random.choice(CB_REASON_CODES),
                        reason_description='Customer dispute - item not received',
                        status=random.choices(['received', 'under_review', 'won', 'lost'], weights=[0.3,0.4,0.2,0.1])[0],
                        evidence_submitted=rnd_bool(0.4),
                        evidence_deadline=txn_time + timedelta(days=30),
                        is_segment_b=(customer.segment == 'B'),
                        created_at=txn_time + timedelta(days=random.randint(5, 15))
                    )
                    chargeback_records.append(cb)
                    db.add(cb)
                    total_chargebacks += 1
        
        if day_offset % 10 == 0:
            db.flush()
            logger.info(f'Generated day {day_offset}/{NUM_DAYS}...')
    
    db.flush()
    
    # --- SETTLEMENTS ---
    total_settlements = 0
    for day_offset in range(0, NUM_DAYS, 1):  # daily settlements
        period_date = base_date + timedelta(days=day_offset)
        gross = rnd_amount(800_000, 2_500_000)
        fees = round(gross * 0.02, 2)  # 2% fee
        tax_amt = round(fees * 0.18, 2)  # GST on fees
        refunds_amt = round(gross * 0.015, 2)
        cb_amt = round(gross * 0.005, 2)
        net = round(gross - fees - tax_amt - refunds_amt - cb_amt, 2)
        
        expected = net
        discrepancy = 0.0
        has_mismatch = False
        status = 'matched'
        
        if day_offset == 60:  # Inject settlement mismatch on day 60
            net = net - SETTLEMENT_MISMATCH_INR
            discrepancy = SETTLEMENT_MISMATCH_INR
            has_mismatch = True
            status = 'partially_matched'
        
        s = Settlement(
            id=f'settle-{day_offset:04d}',
            merchant_id='merchant-bharat-001',
            settlement_ref=f'SETL-{uuid.uuid4().hex[:12].upper()}',
            gateway='razorpay',
            period_start=period_date.replace(tzinfo=timezone.utc),
            period_end=(period_date + timedelta(hours=23, minutes=59)).replace(tzinfo=timezone.utc),
            settlement_date=(period_date + timedelta(days=2)).replace(tzinfo=timezone.utc),
            gross_amount=Decimal(str(gross)),
            fees=Decimal(str(fees)),
            tax=Decimal(str(tax_amt)),
            refunds_total=Decimal(str(refunds_amt)),
            chargebacks_total=Decimal(str(cb_amt)),
            net_amount=Decimal(str(net)),
            expected_amount=Decimal(str(expected)),
            discrepancy=Decimal(str(discrepancy)),
            status=status,
            has_mismatch=has_mismatch
        )
        db.add(s)
        total_settlements += 1
    
    db.flush()
    
    # --- SUBSCRIPTIONS ---
    sub_customers = random.sample(customers, min(NUM_SUBSCRIPTIONS, len(customers)))
    plans = ['Basic Plan', 'Pro Plan', 'Enterprise Plan']
    plan_amounts = [999, 2999, 9999]
    for i, cust in enumerate(sub_customers):
        plan_idx = random.randint(0, 2)
        failed_att = random.choices([0, 1, 2, 3], weights=[0.65, 0.20, 0.10, 0.05])[0]
        sub = Subscription(
            id=f'sub-{i:05d}',
            merchant_id='merchant-bharat-001',
            customer_id=cust.id,
            plan_name=plans[plan_idx],
            status='failed' if failed_att >= 2 else ('active' if failed_att == 0 else 'paused'),
            amount=Decimal(str(plan_amounts[plan_idx])),
            billing_cycle='monthly',
            next_billing_date=(now + timedelta(days=random.randint(1, 30))).replace(tzinfo=timezone.utc),
            failed_attempts=failed_att,
            last_failed_at=(now - timedelta(days=random.randint(1, 10))).replace(tzinfo=timezone.utc) if failed_att > 0 else None,
            recovery_status='none' if failed_att == 0 else ('in_progress' if failed_att == 1 else 'abandoned')
        )
        db.add(sub)
    
    db.commit()
    
    summary = {
        'merchant': 'Bharat Commerce Pvt Ltd',
        'demo_user': 'demo@merchant.com / demo123',
        'customers': NUM_CUSTOMERS,
        'products': NUM_PRODUCTS,
        'transactions': total_transactions,
        'failed_payments': total_failed_payments,
        'chargebacks': total_chargebacks,
        'settlements': total_settlements,
        'subscriptions': NUM_SUBSCRIPTIONS,
        'anomalies_injected': [
            f'Gateway failure days {ANOMALY_START_DAY}-{ANOMALY_END_DAY}: failure rate {ANOMALY_FAILURE_RATE*100:.1f}%',
            f'Segment B chargeback rate: {SEGMENT_B_CB_RATE*100:.1f}% (baseline {BASELINE_CB_RATE*100:.1f}%)',
            f'Product X conversion: {PRODUCT_X_CONVERSION*100:.1f}% (baseline {BASELINE_CONVERSION*100:.1f}%)',
            f'Settlement day 60 mismatch: INR {SETTLEMENT_MISMATCH_INR:,}'
        ]
    }
    logger.info(f'Synthetic data generation complete: {summary}')
    return summary

def _hour_weights():
    # Higher traffic 9am-10pm
    weights = [1]*9 + [5,8,10,12,15,18,20,18,15,12,10,8,5,3,2,1,1,1]
    return weights[:24]

def _calc_recovery_prob(failure_reason: str, retry_count: int, risk_score: float, amount: float) -> float:
    base_probs = {
        'gateway_timeout': 0.72,
        'network_error': 0.68,
        'insufficient_funds': 0.35,
        'card_declined': 0.42,
        'expired_card': 0.15,
        'fraud_block': 0.05
    }
    p = base_probs.get(failure_reason, 0.4)
    p -= retry_count * 0.18
    p -= risk_score * 0.3
    if amount > 10000: p -= 0.08
    return max(0.0, min(0.95, p))

def _gateway_code(failure_reason: str) -> str:
    codes = {
        'gateway_timeout': 'GW_TIMEOUT',
        'network_error': 'NET_ERR',
        'insufficient_funds': 'INSUF_FUNDS',
        'card_declined': 'CARD_DECLINED',
        'expired_card': 'CARD_EXPIRED',
        'fraud_block': 'FRAUD_BLOCK',
        'none': 'SUCCESS'
    }
    return codes.get(failure_reason, 'ERR_UNKNOWN')
''',
    "backend/app/engines/__init__.py": "",
    "backend/app/engines/reconciliation.py": '''"""
Deterministic 4-Level Reconciliation Engine
No LLM involvement in matching logic.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import timedelta
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ReconciliationItem:
    settlement_item_id: str
    transaction_id: Optional[str]
    settlement_amount: float
    transaction_amount: Optional[float]
    match_level: Optional[int]
    match_confidence: float
    discrepancy: float
    match_status: str  # 'matched', 'partial', 'unmatched'
    possible_reason: Optional[str] = None

@dataclass
class ReconciliationResult:
    total_records: int
    matched: int
    partial: int
    unmatched: int
    match_rate: float
    discrepancy_amount: float
    items: list = field(default_factory=list)
    exceptions: list = field(default_factory=list)

def reconcile_batch(transactions: list[dict], settlement_items: list[dict]) -> ReconciliationResult:
    """
    4-level deterministic matching.
    transactions: list of {id, gateway_transaction_id, order_id, customer_id, amount, created_at, gateway}
    settlement_items: list of {id, gateway_transaction_id, order_id, amount, settlement_date, gateway, customer_id}
    """
    results = []
    matched = 0
    partial = 0
    unmatched = 0
    total_discrepancy = 0.0
    
    # Build lookup indexes
    txn_by_gw_id = {t['gateway_transaction_id']: t for t in transactions if t.get('gateway_transaction_id')}
    txn_by_order_id = {t['order_id']: t for t in transactions if t.get('order_id')}
    txn_by_amount_time = {}  # (amount, day, customer) -> txn
    for t in transactions:
        if t.get('created_at') and t.get('customer_id'):
            key = (round(float(t['amount']), 2), t['created_at'][:10], t.get('customer_id', ''))
            txn_by_amount_time[key] = t
    
    for item in settlement_items:
        matched_txn = None
        match_level = None
        confidence = 0.0
        discrepancy = 0.0
        
        # Level 1: Exact gateway transaction ID match
        gw_id = item.get('gateway_transaction_id')
        if gw_id and gw_id in txn_by_gw_id:
            matched_txn = txn_by_gw_id[gw_id]
            match_level = 1
            confidence = 1.0
        
        # Level 2: Order ID match
        if not matched_txn:
            order_id = item.get('order_id')
            if order_id and order_id in txn_by_order_id:
                matched_txn = txn_by_order_id[order_id]
                match_level = 2
                confidence = 0.92
        
        # Level 3: Amount + Date + Customer
        if not matched_txn:
            settle_date = (item.get('settlement_date') or '')[:10]
            # Settlement date is ~2 days after transaction
            from datetime import datetime
            try:
                sd = datetime.fromisoformat(settle_date)
                possible_txn_dates = [(sd - timedelta(days=d)).strftime('%Y-%m-%d') for d in range(0, 4)]
            except:
                possible_txn_dates = [settle_date]
            
            for txn_date in possible_txn_dates:
                key = (round(float(item['amount']), 2), txn_date, item.get('customer_id', ''))
                if key in txn_by_amount_time:
                    matched_txn = txn_by_amount_time[key]
                    match_level = 3
                    confidence = 0.78
                    break
        
        # Level 4: Fuzzy — amount within 2% + same gateway + same day window
        if not matched_txn:
            item_amount = float(item['amount'])
            for t in transactions:
                t_amount = float(t['amount'])
                if abs(t_amount - item_amount) / max(item_amount, 1) < 0.02:
                    if t.get('gateway') == item.get('gateway'):
                        matched_txn = t
                        match_level = 4
                        confidence = 0.61
                        break
        
        if matched_txn:
            discrepancy = float(item['amount']) - float(matched_txn['amount'])
            if abs(discrepancy) < 0.01:
                match_status = 'matched'
                matched += 1
            else:
                match_status = 'partial'
                partial += 1
            total_discrepancy += abs(discrepancy)
            
            possible_reason = None
            if abs(discrepancy) > 0:
                if discrepancy < 0:
                    possible_reason = 'Gateway fee / tax deduction'
                else:
                    possible_reason = 'Amount adjustment or partial refund'
        else:
            match_status = 'unmatched'
            unmatched += 1
            confidence = 0.0
            possible_reason = 'No matching transaction found — possible fee, adjustment, or data gap'
        
        results.append(ReconciliationItem(
            settlement_item_id=item['id'],
            transaction_id=matched_txn['id'] if matched_txn else None,
            settlement_amount=float(item['amount']),
            transaction_amount=float(matched_txn['amount']) if matched_txn else None,
            match_level=match_level,
            match_confidence=round(confidence, 3),
            discrepancy=round(discrepancy, 2),
            match_status=match_status,
            possible_reason=possible_reason
        ))
    
    total = len(settlement_items)
    match_rate = (matched + partial * 0.5) / total if total > 0 else 0.0
    
    exceptions = [r for r in results if r.match_status == 'unmatched' or abs(r.discrepancy) > 100]
    
    return ReconciliationResult(
        total_records=total,
        matched=matched,
        partial=partial,
        unmatched=unmatched,
        match_rate=round(match_rate, 4),
        discrepancy_amount=round(total_discrepancy, 2),
        items=results,
        exceptions=exceptions
    )
''',
    "backend/app/engines/risk_ml.py": '''"""
ML-based Risk Scoring Engine
Uses scikit-learn RandomForestClassifier trained on synthetic data.
The LLM may explain results but NEVER replaces this model.
"""
import os
import random
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)
MODEL_PATH = Path('./data/models/risk_model.pkl')
DATASET_PATH = Path('./data/risk_dataset.csv')

@dataclass
class RiskScore:
    transaction_id: Optional[str]
    score: float  # 0-1
    label: int    # 0=legitimate, 1=risky
    confidence: float
    features: dict
    explanation: str

@dataclass
class ModelMetrics:
    precision: float
    recall: float
    fpr: float
    fnr: float
    auc: float
    confusion_matrix: list  # [[TN, FP], [FN, TP]]
    feature_importance: dict
    n_test_samples: int
    threshold: float

_model = None
_scaler = None
_metrics: Optional[ModelMetrics] = None
_FEATURE_NAMES = [
    'amount_log', 'country_risk', 'is_new_device', 'ip_velocity',
    'customer_age_days', 'payment_method_risk', 'velocity_1h',
    'historical_chargebacks', 'refund_rate', 'hour_of_day',
    'is_weekend', 'is_anomaly_day'
]

def _generate_training_data(n_samples: int = 50_000):
    """Generate synthetic risk training data with known patterns."""
    import random as rnd
    rnd.seed(42)
    np.random.seed(42)
    
    X, y = [], []
    for i in range(n_samples):
        amount = np.random.lognormal(8, 1.5)  # INR
        country_risk = np.random.choice([0.1, 0.2, 0.5, 0.8], p=[0.7, 0.15, 0.1, 0.05])
        is_new_device = int(np.random.random() < 0.15)
        ip_velocity = np.random.poisson(1.5)
        customer_age = np.random.exponential(365)
        method_risk = np.random.choice([0.1, 0.2, 0.4, 0.6], p=[0.45, 0.30, 0.15, 0.10])  # upi, card, wallet, netbanking
        velocity_1h = np.random.poisson(2)
        hist_cb = np.random.choice([0, 1, 2, 3], p=[0.80, 0.12, 0.05, 0.03])
        refund_rate = np.clip(np.random.beta(1, 20), 0, 0.5)
        hour = np.random.randint(0, 24)
        is_weekend = int(np.random.random() < 0.28)
        is_anomaly = int(np.random.random() < 0.07)
        
        features = [
            np.log1p(amount), country_risk, is_new_device, min(ip_velocity, 10),
            min(customer_age, 1000) / 1000, method_risk, min(velocity_1h, 10),
            hist_cb, refund_rate, hour / 24, is_weekend, is_anomaly
        ]
        
        # Label rules: known fraud patterns
        fraud_score = (
            (country_risk > 0.4) * 0.3 +
            is_new_device * 0.25 +
            (ip_velocity > 5) * 0.3 +
            (amount > 50000) * 0.1 +
            (hist_cb >= 2) * 0.4 +
            (refund_rate > 0.2) * 0.2 +
            is_anomaly * 0.35 +
            (velocity_1h > 5) * 0.25
        )
        label = int(fraud_score > 0.6 or (fraud_score > 0.4 and rnd.random() < 0.4))
        
        X.append(features)
        y.append(label)
    
    return np.array(X), np.array(y)

def train_risk_model() -> ModelMetrics:
    """Train the Random Forest model and compute metrics on held-out test set."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import precision_score, recall_score, roc_auc_score, confusion_matrix
    import joblib
    
    logger.info('Training risk ML model...')
    X, y = _generate_training_data(50_000)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=20,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train_s, y_train)
    
    # Compute metrics on held-out test set
    y_pred = clf.predict(X_test_s)
    y_prob = clf.predict_proba(X_test_s)[:, 1]
    
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    auc = roc_auc_score(y_test, y_prob)
    
    feature_importance = dict(zip(_FEATURE_NAMES, clf.feature_importances_.tolist()))
    
    # Save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': clf, 'scaler': scaler}, str(MODEL_PATH))
    logger.info(f'Risk model saved. Precision={precision:.3f}, Recall={recall:.3f}, AUC={auc:.3f}')
    
    metrics = ModelMetrics(
        precision=round(precision, 4),
        recall=round(recall, 4),
        fpr=round(fpr, 4),
        fnr=round(fnr, 4),
        auc=round(auc, 4),
        confusion_matrix=[[int(tn), int(fp)], [int(fn), int(tp)]],
        feature_importance=feature_importance,
        n_test_samples=len(y_test),
        threshold=0.5
    )
    return metrics

def _load_model():
    global _model, _scaler, _metrics
    if _model is not None:
        return
    import joblib
    if MODEL_PATH.exists():
        data = joblib.load(str(MODEL_PATH))
        _model = data['model']
        _scaler = data['scaler']
        logger.info('Risk model loaded from disk.')
    else:
        logger.info('No saved model found, training now...')
        _metrics = train_risk_model()
        data = joblib.load(str(MODEL_PATH))
        _model = data['model']
        _scaler = data['scaler']

def score_transaction(features: dict, transaction_id: Optional[str] = None) -> RiskScore:
    """Score a transaction using the trained ML model."""
    _load_model()
    
    amount = features.get('amount', 1000)
    country_risk = {'IN': 0.1, 'US': 0.2, 'NG': 0.8, 'RU': 0.8}.get(features.get('country', 'IN'), 0.3)
    is_new_device = int(features.get('is_new_device', False))
    ip_velocity = min(features.get('ip_velocity', 1), 10)
    customer_age = min(features.get('customer_age_days', 365), 1000) / 1000
    method_risk = {'upi': 0.1, 'card': 0.2, 'wallet': 0.4, 'netbanking': 0.6}.get(features.get('payment_method', 'upi'), 0.3)
    velocity_1h = min(features.get('velocity_1h', 1), 10)
    hist_cb = features.get('historical_chargebacks', 0)
    refund_rate = features.get('refund_rate', 0.0)
    hour = features.get('hour_of_day', 12)
    is_weekend = int(features.get('is_weekend', False))
    is_anomaly = int(features.get('is_anomaly_day', False))
    
    X = np.array([[
        np.log1p(amount), country_risk, is_new_device, ip_velocity,
        customer_age, method_risk, velocity_1h, hist_cb, refund_rate,
        hour / 24, is_weekend, is_anomaly
    ]])
    
    X_scaled = _scaler.transform(X)
    prob = _model.predict_proba(X_scaled)[0][1]
    label = int(prob >= 0.5)
    
    top_features = sorted(
        _model.feature_importances_,
        reverse=True
    )
    
    explanation_parts = []
    if country_risk > 0.4: explanation_parts.append('high-risk country')
    if is_new_device: explanation_parts.append('new device detected')
    if ip_velocity > 5: explanation_parts.append('high IP velocity')
    if hist_cb >= 2: explanation_parts.append('multiple historical chargebacks')
    if refund_rate > 0.2: explanation_parts.append('high refund rate')
    explanation = ', '.join(explanation_parts) if explanation_parts else 'no significant risk signals'
    
    return RiskScore(
        transaction_id=transaction_id,
        score=round(float(prob), 4),
        label=label,
        confidence=round(min(abs(prob - 0.5) * 2, 1.0), 3),
        features={
            'amount': amount,
            'country_risk': country_risk,
            'is_new_device': bool(is_new_device),
            'ip_velocity': ip_velocity
        },
        explanation=f'Risk score {prob:.2f}: {explanation}'
    )

def get_model_metrics() -> ModelMetrics:
    """Get cached model metrics (calculated from held-out test data, never hardcoded)."""
    global _metrics
    if _metrics is None:
        _load_model()
        if _metrics is None:
            _metrics = train_risk_model()
    return _metrics
''',
    "backend/app/engines/recovery_scoring.py": '''"""
Deterministic Recovery Scoring Engine
P(recovery) is calculated from payment features.
Expected Recovery Value = amount * P(recovery)
Never uses LLM for calculation.
"""
from dataclasses import dataclass
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class RecoveryScore:
    payment_attempt_id: str
    transaction_id: str
    amount: float
    failure_reason: str
    retry_count: int
    risk_score: float
    recovery_probability: float
    expected_recovery_value: float
    rank_score: float
    recommendation: str
    is_eligible: bool  # passes basic filters
    exclusion_reason: Optional[str] = None

BASE_RECOVERY_PROBS = {
    'gateway_timeout': 0.72,
    'network_error': 0.68,
    'insufficient_funds': 0.35,
    'card_declined': 0.42,
    'expired_card': 0.15,
    'fraud_block': 0.05,
    'none': 0.50
}

MIN_RECOVERY_PROB = 0.30  # below this threshold, not worth retrying
MAX_RETRY_COUNT = 2       # policy limit
MAX_RISK_SCORE = 0.65     # policy limit

def calculate_recovery_probability(features: dict) -> float:
    """
    Deterministic formula based on failure features.
    Features: failure_reason, retry_count, risk_score, amount, customer_history_score, days_since_failure
    """
    failure_reason = features.get('failure_reason', 'card_declined')
    retry_count = features.get('retry_count', 0)
    risk_score = features.get('risk_score', 0.1)
    amount = float(features.get('amount', 1000))
    customer_history_score = features.get('customer_history_score', 0.5)  # 0-1, higher=better
    days_since_failure = features.get('days_since_failure', 1)
    
    p = BASE_RECOVERY_PROBS.get(failure_reason, 0.4)
    p -= retry_count * 0.18       # each retry reduces probability
    p -= risk_score * 0.30        # high risk reduces probability
    p += customer_history_score * 0.15  # good customer history increases
    if amount > 10_000: p -= 0.08  # large amounts harder to recover
    if days_since_failure > 7: p -= 0.12  # stale failures less recoverable
    if days_since_failure > 30: p -= 0.20
    
    return max(0.0, min(0.95, p))

def score_recovery_candidate(payment: dict) -> RecoveryScore:
    """Score a single failed payment for recovery."""
    amount = float(payment.get('amount', 0))
    retry_count = payment.get('retry_count', payment.get('attempt_number', 1)) - 1
    risk_score = payment.get('risk_score', 0.1)
    failure_reason = payment.get('failure_reason', 'card_declined')
    
    features = {
        'failure_reason': failure_reason,
        'retry_count': retry_count,
        'risk_score': risk_score,
        'amount': amount,
        'customer_history_score': payment.get('customer_history_score', 0.5),
        'days_since_failure': payment.get('days_since_failure', 1)
    }
    
    prob = calculate_recovery_probability(features)
    expected_value = amount * prob
    rank_score = expected_value  # primary ranking by expected value
    
    # Eligibility check
    is_eligible = True
    exclusion_reason = None
    if retry_count >= MAX_RETRY_COUNT:
        is_eligible = False
        exclusion_reason = f'retry_count ({retry_count}) >= max ({MAX_RETRY_COUNT})'
    elif risk_score > MAX_RISK_SCORE:
        is_eligible = False
        exclusion_reason = f'risk_score ({risk_score:.2f}) > threshold ({MAX_RISK_SCORE})'
    elif prob < MIN_RECOVERY_PROB:
        is_eligible = False
        exclusion_reason = f'recovery_probability ({prob:.2f}) < minimum ({MIN_RECOVERY_PROB})'
    elif failure_reason == 'fraud_block':
        is_eligible = False
        exclusion_reason = 'fraud_block failures cannot be retried'
    
    if is_eligible:
        if prob > 0.6:
            recommendation = f'HIGH confidence recovery: schedule retry immediately. Expected: ₹{expected_value:,.0f}'
        else:
            recommendation = f'MEDIUM confidence: schedule retry with customer notification. Expected: ₹{expected_value:,.0f}'
    else:
        recommendation = f'Excluded: {exclusion_reason}'
    
    return RecoveryScore(
        payment_attempt_id=payment.get('id', ''),
        transaction_id=payment.get('transaction_id', ''),
        amount=amount,
        failure_reason=failure_reason,
        retry_count=retry_count,
        risk_score=risk_score,
        recovery_probability=round(prob, 4),
        expected_recovery_value=round(expected_value, 2),
        rank_score=round(rank_score, 2),
        recommendation=recommendation,
        is_eligible=is_eligible,
        exclusion_reason=exclusion_reason
    )

def rank_candidates(payments: list[dict]) -> list[RecoveryScore]:
    """Score and rank all candidates by expected recovery value."""
    scores = [score_recovery_candidate(p) for p in payments]
    return sorted(scores, key=lambda s: s.expected_recovery_value, reverse=True)

def calculate_recovery_metrics(candidates: list[RecoveryScore]) -> dict:
    """Calculate aggregate recovery funnel metrics."""
    total = len(candidates)
    eligible = [c for c in candidates if c.is_eligible]
    risk_blocked = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'risk_score' in c.exclusion_reason]
    retry_blocked = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'retry_count' in c.exclusion_reason]
    low_prob = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'probability' in c.exclusion_reason]
    fraud_blocked = [c for c in candidates if not c.is_eligible and c.exclusion_reason and 'fraud' in c.exclusion_reason]
    
    total_amount = sum(c.amount for c in candidates)
    eligible_amount = sum(c.amount for c in eligible)
    expected_recovery = sum(c.expected_recovery_value for c in eligible)
    
    return {
        'total_detected': total,
        'total_amount': round(total_amount, 2),
        'eligible': len(eligible),
        'eligible_amount': round(eligible_amount, 2),
        'expected_recovery': round(expected_recovery, 2),
        'risk_blocked': len(risk_blocked),
        'retry_blocked': len(retry_blocked),
        'low_probability_blocked': len(low_prob),
        'fraud_blocked': len(fraud_blocked),
        'total_blocked': total - len(eligible),
        'blocked_amount': round(total_amount - eligible_amount, 2)
    }
''',
    "backend/app/engines/cash_forecasting.py": '''"""
Cash Flow Forecasting Engine
Uses simple exponential smoothing with trend.
Never uses LLM for forecasting.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class CashForecast:
    forecast_dates: list[str]
    inflows: list[float]
    outflows: list[float]
    net: list[float]
    confidence_band_low: list[float]
    confidence_band_high: list[float]
    total_expected_inflow: float
    total_expected_outflow: float
    total_expected_net: float
    methodology: str = 'Exponential Smoothing with Trend (Holt\\'s method)'
    data_points_used: int = 0

def _exponential_smoothing(series: list[float], alpha: float = 0.3) -> list[float]:
    """Simple exponential smoothing."""
    if not series:
        return []
    smoothed = [series[0]]
    for i in range(1, len(series)):
        smoothed.append(alpha * series[i] + (1 - alpha) * smoothed[-1])
    return smoothed

def _holts_forecast(series: list[float], horizon: int, alpha: float = 0.3, beta: float = 0.1) -> tuple[list[float], float]:
    """Holt's double exponential smoothing with trend component."""
    if len(series) < 3:
        avg = sum(series) / len(series) if series else 100_000
        return [avg] * horizon, avg * 0.15
    
    # Initialize
    level = series[0]
    trend = series[1] - series[0]
    
    for val in series[1:]:
        prev_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    
    # Compute standard deviation for confidence band
    import statistics
    std = statistics.stdev(series) if len(series) > 1 else abs(level) * 0.1
    
    forecast = [level + i * trend for i in range(1, horizon + 1)]
    return forecast, std

def forecast_cash_from_history(
    daily_inflows: list[float],
    daily_outflows: list[float],
    horizon_days: int = 30
) -> CashForecast:
    """
    Forecast cash flows based on historical data.
    daily_inflows: list of daily inflow amounts (most recent last)
    daily_outflows: list of daily outflow amounts (most recent last)
    """
    today = datetime.utcnow().date()
    
    inflow_forecast, inflow_std = _holts_forecast(daily_inflows, horizon_days)
    outflow_forecast, outflow_std = _holts_forecast(daily_outflows, horizon_days)
    
    forecast_dates = [(today + timedelta(days=i+1)).isoformat() for i in range(horizon_days)]
    net_forecast = [round(i - o, 2) for i, o in zip(inflow_forecast, outflow_forecast)]
    
    confidence_width = 1.645  # 90% confidence interval
    band_low = [round(n - confidence_width * (inflow_std + outflow_std), 2) for n in net_forecast]
    band_high = [round(n + confidence_width * (inflow_std + outflow_std), 2) for n in net_forecast]
    
    return CashForecast(
        forecast_dates=forecast_dates,
        inflows=[round(v, 2) for v in inflow_forecast],
        outflows=[round(v, 2) for v in outflow_forecast],
        net=net_forecast,
        confidence_band_low=band_low,
        confidence_band_high=band_high,
        total_expected_inflow=round(sum(inflow_forecast), 2),
        total_expected_outflow=round(sum(outflow_forecast), 2),
        total_expected_net=round(sum(net_forecast), 2),
        data_points_used=len(daily_inflows)
    )
''',
    "backend/app/engines/growth_simulation.py": '''"""
A/B Campaign Simulation Engine
Monte Carlo simulation — deterministic when seeded.
Never uses LLM for simulation results.
"""
import random
import math
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class SimulationResult:
    campaign_type: str
    target_count: int
    risk_exclusions: int
    control_conversion: float
    treatment_conversion: float
    lift_pct: float
    expected_revenue: float
    expected_roi: float
    confidence_low: float
    confidence_high: float
    p_value: float
    is_significant: bool
    budget: float
    simulations_run: int = 1000

def simulate_campaign(params: dict, historical_data: dict, seed: int = 42) -> SimulationResult:
    """
    Simulate a marketing campaign using Monte Carlo approach.
    params: {campaign_type, target_segment, target_count, budget, duration_days}
    historical_data: {current_conversion, avg_order_value, segment_risk_rate}
    """
    rng = random.Random(seed)
    
    target_count = int(params.get('target_count', 5000))
    budget = float(params.get('budget', 50_000))
    campaign_type = params.get('campaign_type', 'reactivation')
    
    current_conversion = historical_data.get('current_conversion', 0.038)
    avg_order_value = historical_data.get('avg_order_value', 2500)
    segment_risk_rate = historical_data.get('segment_risk_rate', 0.1)
    
    # Exclude high-risk customers
    risk_exclusions = int(target_count * segment_risk_rate)
    effective_count = target_count - risk_exclusions
    
    # Expected lift by campaign type
    lift_estimates = {
        'reactivation': 0.18,   # 18% lift on conversion
        'upsell': 0.12,
        'cross_sell': 0.10,
        'new_customer': 0.22
    }
    expected_lift = lift_estimates.get(campaign_type, 0.15)
    treatment_conversion = current_conversion * (1 + expected_lift)
    
    # Monte Carlo: 1000 simulations
    n_sims = 1000
    revenue_samples = []
    for _ in range(n_sims):
        converted = sum(1 for _ in range(effective_count) if rng.random() < treatment_conversion)
        revenue = converted * avg_order_value * rng.uniform(0.85, 1.15)
        revenue_samples.append(revenue)
    
    revenue_samples.sort()
    expected_revenue = sum(revenue_samples) / n_sims
    conf_low = revenue_samples[int(n_sims * 0.025)]
    conf_high = revenue_samples[int(n_sims * 0.975)]
    
    expected_roi = (expected_revenue - budget) / budget if budget > 0 else 0
    
    # p-value (simplified two-proportion z-test)
    n = effective_count // 2  # control and treatment each get half
    p1 = current_conversion
    p2 = treatment_conversion
    p_pool = (p1 + p2) / 2
    if p_pool > 0 and p_pool < 1 and n > 0:
        se = math.sqrt(p_pool * (1 - p_pool) * (2 / n))
        z = abs(p2 - p1) / (se + 1e-10)
        p_value = 2 * (1 - _normal_cdf(z))  # two-tailed
    else:
        p_value = 1.0
    
    return SimulationResult(
        campaign_type=campaign_type,
        target_count=target_count,
        risk_exclusions=risk_exclusions,
        control_conversion=round(current_conversion, 4),
        treatment_conversion=round(treatment_conversion, 4),
        lift_pct=round(expected_lift * 100, 2),
        expected_revenue=round(expected_revenue, 2),
        expected_roi=round(expected_roi * 100, 2),
        confidence_low=round(conf_low, 2),
        confidence_high=round(conf_high, 2),
        p_value=round(p_value, 4),
        is_significant=p_value < 0.05,
        budget=budget
    )

def _normal_cdf(z: float) -> float:
    """Approximation of normal CDF."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))
''',
    "backend/app/engines/rag_knowledge.py": '''"""
RAG Knowledge Base for Financial Context
Provides financial knowledge to agents for explanation and context.
NEVER used for arithmetic, reconciliation, or fraud scoring.
"""
from dataclasses import dataclass
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class KnowledgeChunk:
    content: str
    source: str
    relevance_score: float

# Embedded knowledge base (no external DB needed for demo)
KNOWLEDGE_BASE = [
    {
        "id": "k001",
        "source": "payment_failure_guide",
        "title": "Payment Failure Recovery Strategies",
        "content": "gateway_timeout failures have 72% recovery rate when retried within 24 hours. network_error failures typically recover within 1-2 retries. card_declined may require customer notification to update payment method. insufficient_funds recovery improves significantly after salary credit dates (1st and 10th of month)."
    },
    {
        "id": "k002", 
        "source": "chargeback_guide",
        "title": "Chargeback Reason Codes and Evidence Requirements",
        "content": "Reason code 4853: Cardholder dispute - item not received. Requires delivery proof, tracking ID, customer communication records. Reason code 4855: Non-receipt of merchandise. Provide shipping confirmation, order logs. Reason code 10.4: Other fraud. Requires IP logs, device fingerprint, order details, customer verification records."
    },
    {
        "id": "k003",
        "source": "reconciliation_guide",
        "title": "Settlement Reconciliation Rules",
        "content": "Settlement discrepancies commonly arise from: (1) Gateway fees (2% standard, 2.5% international), (2) Chargeback holds, (3) Refund deductions, (4) Tax (GST 18% on fees), (5) Timing differences. Settlements typically arrive T+2 business days. Amount within 0.5% is considered matched."
    },
    {
        "id": "k004",
        "source": "fraud_indicators",
        "title": "Fraud Detection Indicators",
        "content": "High-risk signals: Multiple transactions from same IP within 1 hour, new device + high amount + high-risk country, historical chargebacks >= 2, refund rate > 20%, velocity breach (>5 txns/hour). Segment B customers show 4.7% chargeback rate vs 0.8% baseline — investigate for abuse ring."
    },
    {
        "id": "k005",
        "source": "recovery_best_practices",
        "title": "Payment Recovery Best Practices",
        "content": "Retry payments within 24-48 hours for gateway timeouts. Space retries: Day 1, Day 3, Day 7. Send customer notification for card-related failures. Use smart retry — avoid retrying on weekends for B2B. Maximum 2 retry attempts before escalating to manual recovery. Promise-to-pay tracking improves B2B recovery by 35%."
    },
    {
        "id": "k006",
        "source": "cash_forecast_methodology",
        "title": "Cash Forecasting Methodology",
        "content": "Cash forecast uses Holt's double exponential smoothing: captures both level and trend. 30-day forecast with 90% confidence interval. Key inputs: historical inflows (settlement credits), outflows (refunds, fees, chargebacks), settlement schedule. Seasonal adjustments applied for festival periods (Diwali, year-end)."
    },
    {
        "id": "k007",
        "source": "pci_compliance",
        "title": "PCI DSS Compliance Notes",
        "content": "Never store CVV/CVC. Card numbers must be tokenized. PAN data must be encrypted at rest. All payment logs must include masked card numbers only. Fraud data must be retained for 12 months for dispute evidence. DPDP Act compliance required for Indian customer data."
    },
    {
        "id": "k008",
        "source": "segment_analysis",
        "title": "Customer Segment Risk Profiles",
        "content": "Segment A (15% of customers): Premium customers, low risk (0.05 risk score), high AOV. Segment B (20%): Higher chargeback rate (4.7%), possible abuse ring involvement, requires enhanced monitoring. Segment C (40%): Standard customers, baseline metrics. Segment D (25%): Inactive customers with low recent purchase history, good reactivation targets."
    }
]

_chroma_client = None
_collection = None

def _get_collection():
    """Get or create ChromaDB collection. Falls back to in-memory keyword search."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from app.core.config import settings
        _chroma_client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        _collection = _chroma_client.get_or_create_collection('financial_knowledge')
        if _collection.count() == 0:
            _collection.add(
                documents=[k['content'] for k in KNOWLEDGE_BASE],
                metadatas=[{'source': k['source'], 'title': k['title']} for k in KNOWLEDGE_BASE],
                ids=[k['id'] for k in KNOWLEDGE_BASE]
            )
            logger.info('ChromaDB collection seeded with financial knowledge.')
        return _collection
    except Exception as e:
        logger.warning(f'ChromaDB not available ({e}), using in-memory keyword search.')
        return None

def query_knowledge(question: str, n_results: int = 3) -> list[KnowledgeChunk]:
    """Query the knowledge base for relevant context."""
    collection = _get_collection()
    
    if collection is not None:
        try:
            results = collection.query(query_texts=[question], n_results=n_results)
            chunks = []
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                dist = results['distances'][0][i] if results.get('distances') else 0.5
                relevance = max(0, 1 - dist)
                chunks.append(KnowledgeChunk(content=doc, source=meta.get('source', 'unknown'), relevance_score=round(relevance, 3)))
            return chunks
        except Exception as e:
            logger.warning(f'ChromaDB query failed: {e}, falling back to keyword search')
    
    # Fallback: keyword-based search
    question_lower = question.lower()
    keywords = question_lower.split()
    scored = []
    for kb in KNOWLEDGE_BASE:
        content_lower = kb['content'].lower()
        score = sum(1 for kw in keywords if kw in content_lower) / max(len(keywords), 1)
        if score > 0:
            scored.append((score, kb))
    scored.sort(reverse=True)
    return [
        KnowledgeChunk(content=kb['content'], source=kb['source'], relevance_score=round(score, 3))
        for score, kb in scored[:n_results]
    ]
''',
    "backend/seed.py": '''#!/usr/bin/env python3
"""
Seed script: generates all synthetic data and trains the risk ML model.
Usage: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal, init_db
from app.synthetic.generator import generate_all_data
from app.engines.risk_ml import train_risk_model
from app.core.logging import get_logger

logger = get_logger('seed')

def main():
    logger.info('=== Merchant Intelligence OS - Seed Script ===')
    
    # Init tables
    init_db()
    
    # Generate data
    db = SessionLocal()
    try:
        summary = generate_all_data(db)
        logger.info(f'Data generated: {summary}')
    finally:
        db.close()
    
    # Train ML model
    logger.info('Training risk ML model...')
    metrics = train_risk_model()
    logger.info(f'Model trained: Precision={metrics.precision}, Recall={metrics.recall}, AUC={metrics.auc}')
    
    logger.info('=== Seed complete! ===')
    logger.info(f'Demo credentials: demo@merchant.com / demo123')
    
if __name__ == '__main__':
    main()
''',
    "frontend/package.json": """{
  "name": "merchant-os-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "lucide-react": "^0.292.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.18.0",
    "zustand": "^4.4.6"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
""",
    "frontend/vite.config.ts": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
""",
    "frontend/tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
}
""",
    "frontend/postcss.config.js": """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""",
    "frontend/tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
""",
    "frontend/index.html": """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Merchant Intelligence OS</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
    "frontend/src/main.tsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 2 }
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
)
""",
    "frontend/src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body {
  font-family: 'Inter', sans-serif;
  @apply bg-gray-50 text-gray-900;
}
""",
    "frontend/src/App.tsx": """import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';

const AuthGuard = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" />;
  return <>{children}</>;
};

const Dashboard = () => <div>Dashboard</div>;
const Command = () => <div>Command Center</div>;
const Growth = () => <div>Growth</div>;
const Risk = () => <div>Risk</div>;
const Recovery = () => <div>Recovery</div>;
const Finance = () => <div>Finance</div>;
const Transactions = () => <div>Transactions</div>;
const Actions = () => <div>Actions</div>;
const Audit = () => <div>Audit</div>;
const Evaluation = () => <div>Evaluation</div>;
const Settings = () => <div>Settings</div>;
const Login = () => <div>Login Page</div>;

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<AuthGuard><Layout><Dashboard /></Layout></AuthGuard>} />
        <Route path="/command" element={<AuthGuard><Layout><Command /></Layout></AuthGuard>} />
        <Route path="/growth" element={<AuthGuard><Layout><Growth /></Layout></AuthGuard>} />
        <Route path="/risk" element={<AuthGuard><Layout><Risk /></Layout></AuthGuard>} />
        <Route path="/recovery" element={<AuthGuard><Layout><Recovery /></Layout></AuthGuard>} />
        <Route path="/finance" element={<AuthGuard><Layout><Finance /></Layout></AuthGuard>} />
        <Route path="/transactions" element={<AuthGuard><Layout><Transactions /></Layout></AuthGuard>} />
        <Route path="/actions" element={<AuthGuard><Layout><Actions /></Layout></AuthGuard>} />
        <Route path="/audit" element={<AuthGuard><Layout><Audit /></Layout></AuthGuard>} />
        <Route path="/evaluation" element={<AuthGuard><Layout><Evaluation /></Layout></AuthGuard>} />
        <Route path="/settings" element={<AuthGuard><Layout><Settings /></Layout></AuthGuard>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
""",
    "frontend/src/types/index.ts": """export interface User {
  id: string;
  email: string;
  role: string;
}

export interface Metric {
  value: number;
  label: string;
  change: number;
}
""",
    "frontend/src/services/api.ts": """import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
""",
    "frontend/src/services/sse.ts": """export const useWorkflowEvents = (workflowId: string) => {
  // SSE implementation placeholder
};
""",
    "frontend/src/store/auth.ts": """import { create } from 'zustand';

interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  setToken: (token) => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
    set({ token });
  },
}));
""",
    "frontend/src/components/layout/Sidebar.tsx": """import { Link } from 'react-router-dom';

const Sidebar = () => {
  const links = [
    { to: '/', label: 'Dashboard' },
    { to: '/command', label: 'Command' },
    { to: '/growth', label: 'Growth' },
    { to: '/risk', label: 'Risk' },
    { to: '/recovery', label: 'Recovery' },
    { to: '/finance', label: 'Finance' },
    { to: '/transactions', label: 'Transactions' },
    { to: '/actions', label: 'Actions' },
    { to: '/audit', label: 'Audit' },
    { to: '/evaluation', label: 'Evaluation' },
    { to: '/settings', label: 'Settings' },
  ];

  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen p-4">
      <div className="font-bold text-xl mb-8">Merchant OS</div>
      <div className="flex flex-col space-y-2">
        {links.map(link => (
          <Link key={link.to} to={link.to} className="hover:bg-gray-800 p-2 rounded">
            {link.label}
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
""",
    "frontend/src/components/layout/Layout.tsx": """import Sidebar from './Sidebar';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        {children}
      </div>
    </div>
  );
};

export default Layout;
""",
    "frontend/src/components/ui/MetricCard.tsx": """interface MetricCardProps {
  label: string;
  value: string;
  change: number;
}

const MetricCard = ({ label, value, change }: MetricCardProps) => {
  return (
    <div className="p-4 bg-white rounded shadow">
      <div className="text-gray-500 text-sm">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className={`text-sm ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
        {change >= 0 ? '+' : ''}{change}%
      </div>
    </div>
  );
};

export default MetricCard;
""",
    "frontend/src/components/ui/StatusBadge.tsx": """interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error';
  label: string;
}

const StatusBadge = ({ status, label }: StatusBadgeProps) => {
  const colors = {
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[status]}`}>
      {label}
    </span>
  );
};

export default StatusBadge;
"""
}

for rel_path, content in files.items():
    full_path = os.path.join(ROOT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Created {len(files)} files successfully.")
