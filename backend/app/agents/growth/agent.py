from sqlalchemy.orm import Session
from app.schemas.state import AgentState, AgentName, Severity
from app.schemas.action import ProposedAction, ActionRiskLevel
from app.schemas.finding import AgentResult
from app.agents.base import BaseAgent
from app.agents.tools.growth_tools import get_conversion_metrics, get_product_conversion_analysis, get_segment_repeat_rate
from app.engines.growth_simulation import simulate_campaign
from app.core.logging import get_logger
import hashlib

logger = get_logger('agent.growth')

SYSTEM_PROMPT = """
You are the Growth Agent of Merchant Intelligence OS.
Your objective is to increase legitimate merchant revenue.

You MUST:
1. Use get_conversion_metrics for all conversion data.
2. Base all recommendations on actual historical data.
3. Use simulate_campaign for projections.
4. Never fabricate metrics or customer data.

You MUST NOT:
- Invent customer behavior metrics
- Claim results without data
"""

class GrowthAgent(BaseAgent):
    def __init__(self, db: Session, merchant_id: str):
        super().__init__(AgentName.GROWTH, db, merchant_id)
    
    async def _run(self, state: AgentState) -> AgentResult:
        findings = []
        evidence = []
        proposed_actions = []
        metrics = {}
        
        # 1. Conversion metrics
        conv = get_conversion_metrics(self.db, self.merchant_id)
        metrics['conversion'] = conv
        
        conv_evidence = self._create_evidence(
            type_='conversion_analysis',
            description=f'Conversion rate: {conv["conversion_rate"]:.2f}% (prev: {conv["previous_conversion_rate"]:.2f}%). AOV: INR {conv["avg_order_value"]:,.0f}.',
            source='growth_tool:get_conversion_metrics'
        )
        evidence.append(conv_evidence)
        
        if conv['change_pct'] < -5:
            findings.append(self._create_finding(
                finding_text=f'Conversion rate declined {conv["change_pct"]:+.1f}% to {conv["conversion_rate"]:.2f}%. AOV: INR {conv["avg_order_value"]:,.0f}. Total successful transactions: {conv["successful_transactions"]}.',
                severity=Severity.MEDIUM,
                confidence=0.82,
                evidence_ids=[conv_evidence.id],
                recommended_action='Analyze product-level conversion. Consider reactivation campaign for dormant customers.',
                metric_label='Conversion Rate',
                metric_prev=conv['previous_conversion_rate'],
                metric_curr=conv['conversion_rate'],
                metric_unit='%'
            ))
        
        # 2. Product analysis
        products = get_product_conversion_analysis(self.db, self.merchant_id)
        anomalous_products = [p for p in products if p['is_anomalous']]
        metrics['product_analysis'] = {
            'total_products': len(products),
            'anomalous_products': len(anomalous_products),
            'low_conversion_products': [p['name'] for p in products if p['status'] == 'low_conversion']
        }
        
        if anomalous_products:
            prod_evidence = self._create_evidence(
                type_='product_conversion',
                description=f'{len(anomalous_products)} products with abnormal conversion rates. Product X: {anomalous_products[0]["conversion_rate"]:.1f}% vs baseline {anomalous_products[0]["baseline_conversion"]:.1f}%.',
                source='growth_tool:get_product_analysis'
            )
            evidence.append(prod_evidence)
            p = anomalous_products[0]
            findings.append(self._create_finding(
                finding_text=f'Product "{p["name"]}" (SKU: {p["sku"]}) conversion dropped to {p["conversion_rate"]:.1f}% from baseline {p["baseline_conversion"]:.1f}% ({p["change_pct"]:+.1f}%). Review pricing and inventory.',
                severity=Severity.MEDIUM,
                confidence=0.85,
                evidence_ids=[prod_evidence.id],
                recommended_action=f'Investigate Product X pricing and inventory. Consider promotional offer.',
                metric_label='Product X Conversion',
                metric_prev=p['baseline_conversion'],
                metric_curr=p['conversion_rate'],
                metric_unit='%'
            ))
        
        # 3. Segment repeat rates
        repeat_rates = get_segment_repeat_rate(self.db, self.merchant_id)
        metrics['repeat_rates'] = repeat_rates
        
        # 4. Campaign simulation for reactivation
        sim_result = simulate_campaign(
            params={'campaign_type': 'reactivation', 'target_count': 5000, 'budget': 75_000},
            historical_data={'current_conversion': conv['conversion_rate'] / 100, 'avg_order_value': conv['avg_order_value'], 'segment_risk_rate': 0.1},
            seed=42
        )
        metrics['campaign_simulation'] = {
            'campaign_type': sim_result.campaign_type,
            'target_count': sim_result.target_count,
            'risk_exclusions': sim_result.risk_exclusions,
            'expected_revenue': sim_result.expected_revenue,
            'expected_roi': sim_result.expected_roi,
            'lift_pct': sim_result.lift_pct,
            'confidence_low': sim_result.confidence_low,
            'confidence_high': sim_result.confidence_high,
            'p_value': sim_result.p_value,
            'is_significant': sim_result.is_significant
        }
        
        # Propose campaign if significant
        if sim_result.is_significant and sim_result.expected_roi > 50:
            sim_evidence = self._create_evidence(
                type_='campaign_simulation',
                description=f'Customer reactivation campaign: {sim_result.target_count} targets, {sim_result.lift_pct}% lift, INR {sim_result.expected_revenue:,.0f} expected revenue, {sim_result.expected_roi}% ROI.',
                source='growth_engine:simulate_campaign',
                amount=sim_result.expected_revenue
            )
            evidence.append(sim_evidence)
            
            idempotency_key = hashlib.sha256(f'{self.merchant_id}:create_campaign:reactivation:{state.workflow_id}'.encode()).hexdigest()
            proposed_actions.append(ProposedAction(
                action_type='create_campaign',
                description=f'Customer reactivation campaign: {sim_result.target_count} customers, INR {sim_result.expected_revenue:,.0f} expected revenue',
                params={
                    'campaign_type': 'reactivation',
                    'target_count': sim_result.target_count,
                    'budget': 75_000,
                    'expected_revenue': sim_result.expected_revenue
                },
                amount_at_risk=75_000,
                expected_outcome=f'INR {sim_result.expected_revenue:,.0f} revenue with {sim_result.lift_pct}% lift (p={sim_result.p_value})',
                evidence_ids=[sim_evidence.id],
                idempotency_key=idempotency_key,
                risk_level=ActionRiskLevel.MEDIUM  # campaigns need approval
            ))
            
            findings.append(self._create_finding(
                finding_text=f'Customer reactivation campaign modeled: {sim_result.target_count} targets, {sim_result.lift_pct}% expected lift, INR {sim_result.expected_revenue:,.0f} revenue (p={sim_result.p_value}). Statistically significant: {sim_result.is_significant}.',
                severity=Severity.LOW,
                confidence=0.79,
                evidence_ids=[sim_evidence.id],
                recommended_action='Approve customer reactivation campaign'
            ))
        
        return AgentResult(
            agent=AgentName.GROWTH,
            status='completed',
            findings=findings,
            evidence=evidence,
            proposed_actions=proposed_actions,
            metrics=metrics
        )
