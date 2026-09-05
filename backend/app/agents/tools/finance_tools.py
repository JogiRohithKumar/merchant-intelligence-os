from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.logging import get_logger

logger = get_logger('tools.finance')

def get_transactions(db: Session, merchant_id: str, start_date: datetime = None, end_date: datetime = None, status: str = None, limit: int = 1000) -> list[dict]:
    from app.database.models.transaction import Transaction
    q = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
    if start_date:
        q = q.filter(Transaction.created_at >= start_date)
    if end_date:
        q = q.filter(Transaction.created_at <= end_date)
    if status:
        q = q.filter(Transaction.status == status)
    txns = q.order_by(Transaction.created_at.desc()).limit(limit).all()
    return [{
        'id': t.id, 'amount': float(t.amount), 'status': t.status.value,
        'currency': t.currency, 'gateway': t.gateway, 'payment_method': t.payment_method,
        'gateway_transaction_id': t.gateway_transaction_id, 'order_id': t.order_id,
        'customer_id': t.customer_id, 'created_at': t.created_at.isoformat() if t.created_at else None,
        'risk_score': t.risk_score, 'is_anomaly_day': t.is_anomaly_day
    } for t in txns]

def get_revenue_summary(db: Session, merchant_id: str, days: int = 30) -> dict:
    from app.database.models.transaction import Transaction
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)
    
    def period_revenue(s, e):
        result = db.query(func.sum(Transaction.amount)).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.status == 'success',
            Transaction.created_at >= s,
            Transaction.created_at <= e
        ).scalar()
        return float(result or 0)
    
    current_rev = period_revenue(start_date, end_date)
    prev_rev = period_revenue(prev_start, start_date)
    change_pct = ((current_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
    
    failed = db.query(func.count(Transaction.id), func.sum(Transaction.amount)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == 'failed',
        Transaction.created_at >= start_date
    ).first()
    
    return {
        'current_revenue': round(current_rev, 2),
        'previous_revenue': round(prev_rev, 2),
        'change_pct': round(change_pct, 2),
        'failed_count': failed[0] or 0,
        'failed_amount': round(float(failed[1] or 0), 2),
        'period_days': days,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    }

def get_settlements(db: Session, merchant_id: str, start_date: datetime = None, end_date: datetime = None) -> list[dict]:
    from app.database.models.settlement import Settlement
    q = db.query(Settlement).filter(Settlement.merchant_id == merchant_id)
    if start_date:
        q = q.filter(Settlement.settlement_date >= start_date)
    if end_date:
        q = q.filter(Settlement.settlement_date <= end_date)
    results = q.order_by(Settlement.settlement_date.desc()).limit(100).all()
    return [{
        'id': s.id, 'settlement_ref': s.settlement_ref, 'gateway': s.gateway,
        'net_amount': float(s.net_amount), 'expected_amount': float(s.expected_amount or 0),
        'discrepancy': float(s.discrepancy or 0), 'status': s.status.value,
        'fees': float(s.fees), 'tax': float(s.tax),
        'refunds_total': float(s.refunds_total), 'chargebacks_total': float(s.chargebacks_total),
        'has_mismatch': s.has_mismatch,
        'settlement_date': s.settlement_date.isoformat() if s.settlement_date else None
    } for s in results]

def get_settlement_detail(db: Session, merchant_id: str, settlement_id: str) -> dict:
    from app.database.models.settlement import Settlement
    s = db.query(Settlement).filter(Settlement.id == settlement_id, Settlement.merchant_id == merchant_id).first()
    if not s:
        return {}
    return {
        'id': s.id, 'settlement_ref': s.settlement_ref, 'gateway': s.gateway,
        'period_start': s.period_start.isoformat() if s.period_start else None,
        'period_end': s.period_end.isoformat() if s.period_end else None,
        'settlement_date': s.settlement_date.isoformat() if s.settlement_date else None,
        'gross_amount': float(s.gross_amount), 'fees': float(s.fees), 'tax': float(s.tax),
        'refunds_total': float(s.refunds_total), 'chargebacks_total': float(s.chargebacks_total),
        'net_amount': float(s.net_amount), 'expected_amount': float(s.expected_amount or 0),
        'discrepancy': float(s.discrepancy or 0), 'status': s.status.value, 'has_mismatch': s.has_mismatch,
        'breakdown': {
            'fees': float(s.fees), 'tax': float(s.tax),
            'refunds': float(s.refunds_total), 'chargebacks': float(s.chargebacks_total),
            'unresolved': float(s.discrepancy or 0)
        }
    }

def find_settlement_exceptions(db: Session, merchant_id: str) -> list[dict]:
    from app.database.models.settlement import Settlement
    mismatched = db.query(Settlement).filter(
        Settlement.merchant_id == merchant_id,
        Settlement.has_mismatch == True
    ).order_by(Settlement.settlement_date.desc()).limit(50).all()
    return [{
        'id': s.id, 'settlement_ref': s.settlement_ref,
        'expected': float(s.expected_amount or 0), 'actual': float(s.net_amount),
        'discrepancy': float(s.discrepancy or 0),
        'date': s.settlement_date.isoformat() if s.settlement_date else None
    } for s in mismatched]

def get_daily_cashflow(db: Session, merchant_id: str, days: int = 60) -> tuple[list[float], list[float]]:
    """Returns (daily_inflows, daily_outflows) for forecasting."""
    from app.database.models.settlement import Settlement
    from datetime import date
    
    settlements = db.query(Settlement).filter(
        Settlement.merchant_id == merchant_id
    ).order_by(Settlement.settlement_date).limit(days).all()
    
    daily_inflows = [float(s.net_amount) for s in settlements]
    daily_outflows = [float(s.fees) + float(s.refunds_total) + float(s.chargebacks_total) for s in settlements]
    return daily_inflows or [100_000] * 30, daily_outflows or [15_000] * 30
