from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.auth import get_current_user
from app.agents.tools.finance_tools import get_settlements, find_settlement_exceptions, get_daily_cashflow
from app.engines.cash_forecasting import forecast_cash_from_history
from app.engines.rag_knowledge import query_knowledge

router = APIRouter()

class SettlementQARequest(BaseModel):
    question: str

@router.get('/finance/settlements')
def get_finance_settlements(skip: int = 0, limit: int = 30, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_settlements(db, current_user.merchant_id)[skip:skip+limit]

@router.get('/finance/exceptions')
def get_finance_exceptions(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return find_settlement_exceptions(db, current_user.merchant_id)

@router.get('/finance/forecast')
def get_cash_forecast(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    inflows, outflows = get_daily_cashflow(db, current_user.merchant_id)
    forecast = forecast_cash_from_history(inflows, outflows)
    return {
        'forecast_dates': forecast.forecast_dates,
        'inflows': forecast.inflows,
        'outflows': forecast.outflows,
        'net': forecast.net,
        'confidence_band_low': forecast.confidence_band_low,
        'confidence_band_high': forecast.confidence_band_high,
        'total_expected_inflow': forecast.total_expected_inflow,
        'total_expected_outflow': forecast.total_expected_outflow,
        'total_expected_net': forecast.total_expected_net,
        'methodology': forecast.methodology
    }

@router.post('/finance/settlements/qa')
def settlement_qa(req: SettlementQARequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    settlements = get_settlements(db, current_user.merchant_id)
    exceptions = find_settlement_exceptions(db, current_user.merchant_id)
    knowledge = query_knowledge(req.question, n_results=2)
    latest = settlements[0] if settlements else {}
    context = {
        'latest_settlement': latest,
        'exceptions': exceptions[:3],
        'knowledge': [k.content for k in knowledge]
    }
    answer = "Based on your financial data: "
    if exceptions:
        answer += f"Identified {len(exceptions)} settlement discrepancies totaling INR {sum(abs(e['discrepancy']) for e in exceptions):,.0f}. "
    if latest:
        answer += f"The latest settlement (ref: {latest.get('settlement_ref', 'N/A')}) settled INR {latest.get('net_amount', 0):,.0f} against an expected INR {latest.get('expected_amount', 0):,.0f}. "
        if latest.get('discrepancy', 0) > 0:
            answer += f"Discrepancy is INR {latest['discrepancy']:,.0f}, typically attributed to gateway processing fees, refund holdbacks, or chargeback fees."
    return {'question': req.question, 'answer': answer, 'context': context}
