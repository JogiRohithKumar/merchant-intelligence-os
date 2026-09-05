from sqlalchemy import create_engine, event
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
