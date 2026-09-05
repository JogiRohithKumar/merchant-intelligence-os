import time
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.schemas.state import AgentState, AgentName, Severity
from app.schemas.finding import AgentResult
from app.agents.base import BaseAgent
from app.agents.tools.finance_tools import (
    get_revenue_summary, get_settlements, get_settlement_detail,
    find_settlement_exceptions, get_daily_cashflow
)
from app.engines.reconciliation import reconcile_batch
from app.engines.cash_forecasting import forecast_cash_from_history
from app.core.logging import get_logger

logger = get_logger('agent.finance')

SYSTEM_PROMPT = """
You are the Finance Agent of Merchant Intelligence OS.
Your objective is to provide financial control and visibility.

You MUST:
1. Use only tool results for all financial data - never invent numbers.
2. Perform NO arithmetic yourself - use the reconciliation and forecasting engines.
3. Return structured findings with evidence IDs.
4. Report discrepancies with exact amounts from the data.
5. Flag settlement mismatches as high severity.
6. Report BOTH matched and unmatched items.
7. Include confidence based on data completeness.

You MUST NOT:
- Calculate reconciliation results yourself
- Invent settlement amounts or revenue figures
- Claim analysis without tool calls
"""

class FinanceAgent(BaseAgent):
    def __init__(self, db: Session, merchant_id: str):
        super().__init__(AgentName.FINANCE, db, merchant_id)
    
    async def _run(self, state: AgentState) -> AgentResult:
        findings = []
        evidence = []
        metrics = {}
        
        # 1. Revenue Analysis
        revenue_summary = get_revenue_summary(self.db, self.merchant_id, days=30)
        metrics['revenue'] = revenue_summary
        
        change_pct = revenue_summary['change_pct']
        rev_evidence = self._create_evidence(
            type_='revenue_summary',
            description=f'Revenue analysis: current INR {revenue_summary["current_revenue"]:,.2f} vs previous INR {revenue_summary["previous_revenue"]:,.2f}',
            source='finance_tool:get_revenue_summary',
            amount=revenue_summary['current_revenue']
        )
        evidence.append(rev_evidence)
        
        severity = Severity.HIGH if change_pct < -15 else (Severity.MEDIUM if change_pct < -5 else Severity.LOW)
        findings.append(self._create_finding(
            finding_text=f'Revenue changed {change_pct:+.1f}% in last 30 days. Current: INR {revenue_summary["current_revenue"]:,.0f}. Failed transactions: {revenue_summary["failed_count"]} worth INR {revenue_summary["failed_amount"]:,.0f}.',
            severity=severity,
            confidence=0.95,
            evidence_ids=[rev_evidence.id],
            recommended_action='Investigate failed transactions and payment degradation' if change_pct < -10 else None,
            metric_label='Revenue Change',
            metric_prev=revenue_summary['previous_revenue'],
            metric_curr=revenue_summary['current_revenue'],
            metric_unit='INR'
        ))
        
        # 2. Settlement Exceptions
        exceptions = find_settlement_exceptions(self.db, self.merchant_id)
        if exceptions:
            total_discrepancy = sum(abs(e['discrepancy']) for e in exceptions)
            exc_evidence = self._create_evidence(
                type_='settlement_exception',
                description=f'{len(exceptions)} settlement mismatches found. Total discrepancy: INR {total_discrepancy:,.0f}',
                source='finance_tool:find_exceptions',
                amount=total_discrepancy
            )
            evidence.append(exc_evidence)
            metrics['settlement_exceptions'] = {'count': len(exceptions), 'total_discrepancy': total_discrepancy, 'examples': exceptions[:3]}
            findings.append(self._create_finding(
                finding_text=f'{len(exceptions)} settlement discrepancies found totaling INR {total_discrepancy:,.0f}. Largest: INR {max(abs(e["discrepancy"]) for e in exceptions):,.0f}.',
                severity=Severity.HIGH,
                confidence=0.98,
                evidence_ids=[exc_evidence.id],
                recommended_action='Investigate settlement mismatches with gateway',
                metric_label='Settlement Discrepancy',
                metric_curr=total_discrepancy,
                metric_unit='INR'
            ))
        
        # 3. Cash Forecast
        inflows, outflows = get_daily_cashflow(self.db, self.merchant_id, days=60)
        forecast = forecast_cash_from_history(inflows, outflows, horizon_days=30)
        metrics['cash_forecast'] = {
            'total_expected_inflow': forecast.total_expected_inflow,
            'total_expected_outflow': forecast.total_expected_outflow,
            'total_expected_net': forecast.total_expected_net,
            'methodology': forecast.methodology
        }
        forecast_evidence = self._create_evidence(
            type_='cash_forecast',
            description=f'30-day cash forecast. Expected net: INR {forecast.total_expected_net:,.0f}',
            source='finance_engine:cash_forecasting',
            amount=forecast.total_expected_net
        )
        evidence.append(forecast_evidence)
        
        # 4. Settlement summary
        settlements = get_settlements(self.db, self.merchant_id)
        if settlements:
            latest = settlements[0]
            metrics['latest_settlement'] = latest
        
        return AgentResult(
            agent=AgentName.FINANCE,
            status='completed',
            findings=findings,
            evidence=evidence,
            metrics=metrics
        )
