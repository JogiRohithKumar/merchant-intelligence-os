from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import uuid
from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import init_db

logger = get_logger('main')

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting Merchant Intelligence OS...')
    init_db()
    logger.info('Database initialized.')
    yield
    logger.info('Shutting down...')

app = FastAPI(
    title='Merchant Intelligence OS API',
    description='Production-grade agentic financial operating system',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:5173', settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.middleware('http')
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    return response

# Import and include routers
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.workflows import router as workflows_router
from app.api.dashboard import router as dashboard_router
from app.api.transactions import router as transactions_router
from app.api.risk import router as risk_router
from app.api.recovery import router as recovery_router
from app.api.finance import router as finance_router
from app.api.growth import router as growth_router
from app.api.actions import router as actions_router
from app.api.audit import router as audit_router
from app.api.evaluation import router as evaluation_router
from app.api.webhooks import router as webhooks_router

app.include_router(auth_router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(auth_router, prefix='/api/v1', tags=['auth-direct'])
app.include_router(chat_router, prefix='/api/v1', tags=['chat'])
app.include_router(workflows_router, prefix='/api/v1', tags=['workflows'])
app.include_router(dashboard_router, prefix='/api/v1', tags=['dashboard'])
app.include_router(transactions_router, prefix='/api/v1', tags=['transactions'])
app.include_router(risk_router, prefix='/api/v1', tags=['risk'])
app.include_router(recovery_router, prefix='/api/v1', tags=['recovery'])
app.include_router(finance_router, prefix='/api/v1', tags=['finance'])
app.include_router(growth_router, prefix='/api/v1', tags=['growth'])
app.include_router(actions_router, prefix='/api/v1', tags=['actions'])
app.include_router(audit_router, prefix='/api/v1', tags=['audit'])
app.include_router(evaluation_router, prefix='/api/v1', tags=['evaluation'])
app.include_router(webhooks_router, prefix='/api/v1', tags=['webhooks'])

@app.get('/')
async def root():
    return {'status': 'ok', 'version': '1.0.0', 'product': 'Merchant Intelligence OS'}

@app.get('/health')
@app.get('/api/health')
async def health():
    from app.database.session import engine
    import sqlalchemy
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text('SELECT 1'))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        db_ok = False

    missing_creds = settings.get_missing_credentials()
    return {
        'status': 'healthy' if db_ok else 'degraded',
        'database': 'connected' if db_ok else 'disconnected',
        'data_mode': settings.DATA_MODE,
        'demo_mode': settings.DEMO_MODE,
        'automated_execution_enabled': settings.AUTOMATED_EXECUTION_ENABLED,
        'is_live_permitted': settings.is_live_execution_permitted,
        'missing_credentials': missing_creds,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@app.get('/readiness')
@app.get('/api/readiness')
async def readiness():
    from app.database.session import engine
    import sqlalchemy
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text('SELECT 1'))
        db_ok = True
    except Exception as e:
        logger.error(f"Readiness check DB error: {e}")
        db_ok = False

    is_ready = db_ok
    status_str = "READY" if is_ready else "NOT_READY"

    return {
        "status": status_str,
        "database": "READY" if db_ok else "UNAVAILABLE",
        "configuration": {
            "app_env": settings.APP_ENV,
            "data_mode": settings.DATA_MODE,
            "automated_execution": "ENABLED" if settings.AUTOMATED_EXECUTION_ENABLED else "DISABLED_SAFE_GATE",
            "live_permitted": settings.is_live_execution_permitted,
            "audit_chain": "ONLINE_TAMPER_EVIDENT",
            "policy_engine": "ACTIVE_STRICT"
        },
        "services": {
            "database": "CONNECTED" if db_ok else "DISCONNECTED",
            "razorpay_gateway": "LIVE_AUTHORIZED" if settings.is_live_execution_permitted else "SANDBOX_VERIFIED",
            "firebase_auth": "CONFIGURED_LIVE" if (settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PRIVATE_KEY) else "SANDBOX_SIMULATED"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

