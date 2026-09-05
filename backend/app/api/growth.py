from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database.session import get_db
from app.api.auth import get_current_user
from app.agents.tools.growth_tools import get_conversion_metrics, get_product_conversion_analysis
from app.engines.growth_simulation import simulate_campaign

router = APIRouter()

@router.get('/growth/metrics')
def get_metrics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not user.merchant_id:
        return {
            'conversion_rate': 0.0,
            'drop_off_rate': 0.0,
            'avg_order_value': 0.0,
            'total_transactions': 0,
            'successful_transactions': 0
        }
    
    conv = get_conversion_metrics(db, user.merchant_id)
    conversion_rate = conv.get('conversion_rate', 0.0)
    drop_off_rate = max(0.0, round(100.0 - conversion_rate, 2)) if conv.get('total_transactions', 0) > 0 else 0.0
    
    return {
        'conversion_rate': conversion_rate,
        'drop_off_rate': drop_off_rate,
        'avg_order_value': conv.get('avg_order_value', 0.0),
        'total_transactions': conv.get('total_transactions', 0),
        'successful_transactions': conv.get('successful_transactions', 0),
        'change_pct': conv.get('change_pct', 0.0)
    }

@router.get('/growth/products/analysis')
def product_analysis(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not user.merchant_id:
        return []
    return get_product_conversion_analysis(db, user.merchant_id)

@router.post('/growth/campaigns/simulate')
def simulate_campaign_endpoint(
    params: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if not user.merchant_id:
        return {
            'expected_uplift': 0.0,
            'estimated_revenue': 0.0,
            'expected_revenue': 0.0,
            'expected_roi': 0.0,
            'p_value': 1.0,
            'is_significant': False,
            'message': 'Insufficient merchant data for campaign simulation.'
        }
    
    conv = get_conversion_metrics(db, user.merchant_id)
    p = params or {'campaign_type': 'reactivation', 'target_count': 5000, 'budget': 50000}
    
    current_conv = conv.get('conversion_rate', 0.0) / 100.0
    aov = conv.get('avg_order_value', 0.0)
    
    if current_conv <= 0:
        current_conv = 0.02
        aov = 2000.0

    sim_res = simulate_campaign(
        params=p,
        historical_data={
            'current_conversion': current_conv,
            'avg_order_value': aov or 2000.0,
            'segment_risk_rate': 0.05
        }
    )
    
    return {
        'campaign_type': sim_res.campaign_type,
        'target_count': sim_res.target_count,
        'risk_exclusions': sim_res.risk_exclusions,
        'control_conversion': sim_res.control_conversion,
        'treatment_conversion': sim_res.treatment_conversion,
        'lift_pct': sim_res.lift_pct,
        'expected_revenue': sim_res.expected_revenue,
        'expected_roi': sim_res.expected_roi,
        'p_value': sim_res.p_value,
        'is_significant': sim_res.is_significant,
        'budget': sim_res.budget
    }
