#!/usr/bin/env python3
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
