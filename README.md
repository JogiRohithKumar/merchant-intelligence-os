# Merchant Intelligence OS

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
