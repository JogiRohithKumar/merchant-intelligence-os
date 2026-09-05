from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone
from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models.transaction import Transaction, TransactionStatus
from app.database.models.chargeback import Chargeback
from app.database.models.settlement import Settlement
from app.agents.tools.finance_tools import get_daily_cashflow
from app.engines.cash_forecasting import forecast_cash_from_history

router = APIRouter()

@router.get('/merchant/dashboard')
def get_dashboard_metrics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # If user has not yet created or connected to a merchant, return clean zero state
    if not user.merchant_id:
        return {
            'has_merchant': False,
            'merchant_name': None,
            'current_revenue': 0.0,
            'revenue_change_pct': 0.0,
            'recoverable_revenue': 0.0,
            'risk_exposure': 0.0,
            'settlement_exceptions': 0.0,
            'conversion_rate': 0.0,
            'cash_forecast_30d': 0.0,
            'total_transactions': 0,
            'daily_chart': [],
            'ai_insights': []
        }

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)
    
    # Current period revenue (last 30d) strictly for user.merchant_id
    current_revenue = db.query(func.sum(Transaction.amount)).filter(
        and_(
            Transaction.merchant_id == user.merchant_id,
            Transaction.status.in_([TransactionStatus.success, 'success']),
            Transaction.created_at >= thirty_days_ago
        )
    ).scalar() or 0
    
    # Previous period revenue (30d to 60d ago)
    previous_revenue = db.query(func.sum(Transaction.amount)).filter(
        and_(
            Transaction.merchant_id == user.merchant_id,
            Transaction.status.in_([TransactionStatus.success, 'success']),
            Transaction.created_at >= sixty_days_ago,
            Transaction.created_at < thirty_days_ago
        )
    ).scalar() or 0
    
    revenue_change_pct = 0
    if previous_revenue > 0:
        revenue_change_pct = ((current_revenue - previous_revenue) / previous_revenue) * 100
        
    # Recoverable revenue (failed transactions in last 30d)
    recoverable_revenue = db.query(func.sum(Transaction.amount)).filter(
        and_(
            Transaction.merchant_id == user.merchant_id,
            Transaction.status.in_([TransactionStatus.failed, 'failed']),
            Transaction.created_at >= thirty_days_ago
        )
    ).scalar() or 0
    
    # Risk exposure (chargebacks in last 30d)
    risk_exposure = db.query(func.sum(Chargeback.amount)).filter(
        and_(
            Chargeback.merchant_id == user.merchant_id,
            Chargeback.created_at >= thirty_days_ago
        )
    ).scalar() or 0
    
    # Settlement exceptions (real discrepancy sum from settlements)
    settlement_exceptions = db.query(func.sum(func.abs(Settlement.discrepancy))).filter(
        and_(
            Settlement.merchant_id == user.merchant_id,
            Settlement.discrepancy != 0
        )
    ).scalar() or 0
    
    # Total and successful transactions
    total_tx = db.query(func.count(Transaction.id)).filter(
        Transaction.merchant_id == user.merchant_id
    ).scalar() or 0
    
    success_tx = db.query(func.count(Transaction.id)).filter(
        and_(
            Transaction.merchant_id == user.merchant_id,
            Transaction.status.in_([TransactionStatus.success, 'success'])
        )
    ).scalar() or 0
    
    conversion_rate = (success_tx / total_tx * 100) if total_tx > 0 else 0
    
    # Real statistical cash forecasting (Holt's double exponential smoothing)
    cash_forecast_30d = 0.0
    if total_tx > 0:
        try:
            inflows, outflows = get_daily_cashflow(db, user.merchant_id, days=60)
            forecast = forecast_cash_from_history(inflows, outflows, horizon_days=30)
            cash_forecast_30d = float(forecast.total_expected_net)
        except Exception:
            cash_forecast_30d = float(current_revenue)
    
    # Generate daily volume chart series strictly from actual transactions in DB
    daily_chart = []
    for i in range(30):
        day_start = now - timedelta(days=29 - i)
        day_end = day_start + timedelta(days=1)
        day_rev = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.merchant_id == user.merchant_id,
                Transaction.status.in_([TransactionStatus.success, 'success']),
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end
            )
        ).scalar() or 0
        daily_chart.append({
            'name': f"Day {i + 1}",
            'revenue': float(day_rev)
        })

    # Autonomous signal feed derived strictly from actual database events
    insights = []
    if settlement_exceptions > 0:
        insights.append({
            'type': 'finance',
            'severity': 'high',
            'title': f'Settlement Mismatch of ₹{float(settlement_exceptions):,.0f}',
            'message': f'Bank settlement reconciliation exception flagged: INR {float(settlement_exceptions):,.0f} discrepancy.'
        })
    if recoverable_revenue > 0:
        insights.append({
            'type': 'recovery',
            'severity': 'medium',
            'title': f'Recoverable Revenue: ₹{float(recoverable_revenue):,.0f}',
            'message': f'Payment degradation signal: INR {float(recoverable_revenue):,.0f} in failed transactions eligible for recovery.'
        })
    if risk_exposure > 0:
        insights.append({
            'type': 'risk',
            'severity': 'high',
            'title': f'Risk Exposure: ₹{float(risk_exposure):,.0f}',
            'message': f'Fraud dispute activity: INR {float(risk_exposure):,.0f} in chargebacks recorded.'
        })

    merchant_name = user.merchant.name if user.merchant else "Your Organization"

    return {
        'has_merchant': True,
        'merchant_name': merchant_name,
        'current_revenue': float(current_revenue),
        'revenue_change_pct': float(revenue_change_pct),
        'recoverable_revenue': float(recoverable_revenue),
        'risk_exposure': float(risk_exposure),
        'settlement_exceptions': float(settlement_exceptions),
        'conversion_rate': float(conversion_rate),
        'cash_forecast_30d': round(cash_forecast_30d, 2),
        'total_transactions': int(total_tx),
        'daily_chart': daily_chart,
        'ai_insights': insights
    }
