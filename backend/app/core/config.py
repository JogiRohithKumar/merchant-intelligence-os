from pydantic_settings import BaseSettings, SettingsConfigDict
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
    DATA_MODE: str = 'SANDBOX'  # 'LIVE', 'SANDBOX', 'DEMO'
    AUTOMATED_EXECUTION_ENABLED: bool = False  # Default MUST be False for safety
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    LOG_LEVEL: str = 'INFO'
    MAX_RETRY_COUNT: int = 2
    MAX_AUTO_RETRY_AMOUNT_INR: float = 10000.0
    MAX_RISK_SCORE_AUTO: float = 0.65
    MAX_CAMPAIGN_AUTO_BUDGET_INR: float = 50000.0
    
    # Firebase configuration
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    @property
    def is_demo_mode(self) -> bool:
        return self.DEMO_MODE
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == 'production'

    @property
    def is_live_execution_permitted(self) -> bool:
        """
        LIVE execution safety gate:
        Requires DATA_MODE == 'LIVE' AND DEMO_MODE == False AND AUTOMATED_EXECUTION_ENABLED == True
        AND valid non-empty Razorpay credentials.
        """
        return (
            self.DATA_MODE.upper() == 'LIVE'
            and not self.DEMO_MODE
            and self.AUTOMATED_EXECUTION_ENABLED is True
            and bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)
        )

    def get_missing_credentials(self) -> list[str]:
        """Reports missing credentials without ever printing secret values."""
        missing = []
        if not self.RAZORPAY_KEY_ID:
            missing.append('RAZORPAY_KEY_ID')
        if not self.RAZORPAY_KEY_SECRET:
            missing.append('RAZORPAY_KEY_SECRET')
        if not self.RAZORPAY_WEBHOOK_SECRET:
            missing.append('RAZORPAY_WEBHOOK_SECRET')
        return missing
    
    @property
    def database_url_sync(self) -> str:
        # For Alembic compatibility
        url = self.DATABASE_URL
        if 'postgresql+asyncpg' in url:
            return url.replace('postgresql+asyncpg', 'postgresql')
        return url

settings = Settings()

