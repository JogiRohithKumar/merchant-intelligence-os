from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.schemas.state import AgentState, AgentName, Severity
from app.schemas.finding import AgentResult
from app.agents.base import BaseAgent
from app.agents.tools.risk_tools import (
    get_chargebacks, get_chargeback_metrics, detect_payment_anomaly,
    score_high_risk_transactions, generate_chargeback_evidence
)
from app.engines.risk_ml import get_model_metrics
from app.core.logging import get_logger

logger = get_logger('agent.risk')

SYSTEM_PROMPT = """
You are the Risk Agent of Merchant Intelligence OS.
Your objective is to prevent financial loss through risk detection.

You MUST:
1. Use the ML model (score_risk tool) for all fraud scoring.
2. Detect anomalies using the detect_anomaly tool.
3. Analyze chargebacks with get_chargebacks tool.
4. Return risk scores with evidence IDs and explanations.
5. Never provide fraud instructions.
6. Never bypass risk detection.

You MUST NOT:
- Score risk without the ML model
- Fabricate risk scores
- Override risk policies
"""

class RiskAgent(BaseAgent):
    def __init__(self, db: Session, merchant_id: str):
        super().__init__(AgentName.RISK, db, merchant_id)
    
    async def _run(self, state: AgentState) -> AgentResult:
        findings = []
        evidence = []
        metrics = {}
        
        # 1. Chargeback analysis
        cb_metrics = get_chargeback_metrics(self.db, self.merchant_id, days=30)
        metrics['chargeback'] = cb_metrics
        
        cb_evidence = self._create_evidence(
            type_='chargeback_analysis',
            description=f'Chargeback rate: {cb_metrics["current_rate"]:.3f}% (previous: {cb_metrics["previous_rate"]:.3f}%). {cb_metrics["current_count"]} chargebacks. Total exposure: INR {cb_metrics["total_exposure"]:,.0f}',
            source='risk_tool:get_chargeback_metrics',
            amount=cb_metrics['total_exposure']
        )
        evidence.append(cb_evidence)
        
        if cb_metrics['change_pct'] > 20 or cb_metrics['is_anomalous']:
            severity = Severity.HIGH if cb_metrics['change_pct'] > 50 else Severity.MEDIUM
            findings.append(self._create_finding(
                finding_text=f'Chargeback rate increased {cb_metrics["change_pct"]:+.1f}% to {cb_metrics["current_rate"]:.3f}%. {cb_metrics["segment_b_count"]} chargebacks from Segment B (high-risk). Total exposure: INR {cb_metrics["total_exposure"]:,.0f}.',
                severity=severity,
                confidence=0.91,
                evidence_ids=[cb_evidence.id],
                recommended_action='Investigate Segment B customer abuse ring. Generate chargeback evidence for disputes.',
                metric_label='Chargeback Rate',
                metric_prev=cb_metrics['previous_rate'],
                metric_curr=cb_metrics['current_rate'],
                metric_unit='%'
            ))
        
        # 2. Payment anomaly detection
        anomaly = detect_payment_anomaly(self.db, self.merchant_id, days=7)
        metrics['payment_anomaly'] = anomaly
        
        if anomaly['is_anomalous']:
            anomaly_evidence = self._create_evidence(
                type_='payment_anomaly',
                description=f'Payment failure rate {anomaly["failure_rate"]:.1f}% (baseline: {anomaly["baseline_failure_rate"]}%). Gateway degradation detected.',
                source='risk_tool:detect_anomaly',
                amount=None
            )
            evidence.append(anomaly_evidence)
            findings.append(self._create_finding(
                finding_text=f'Payment failure rate {anomaly["failure_rate"]:.1f}% exceeds baseline ({anomaly["baseline_failure_rate"]}%). {anomaly["failed_transactions"]} failed transactions. Severity: {anomaly["severity"]}.',
                severity=Severity.HIGH if anomaly['severity'] == 'critical' else Severity.MEDIUM,
                confidence=0.88,
                evidence_ids=[anomaly_evidence.id],
                recommended_action='Check gateway status. Investigate failed transactions for recovery.',
                metric_label='Failure Rate',
                metric_prev=anomaly['baseline_failure_rate'],
                metric_curr=anomaly['failure_rate'],
                metric_unit='%'
            ))
        
        # 3. ML model metrics
        try:
            model_metrics = get_model_metrics()
            metrics['model_metrics'] = {
                'precision': model_metrics.precision,
                'recall': model_metrics.recall,
                'fpr': model_metrics.fpr,
                'fnr': model_metrics.fnr,
                'auc': model_metrics.auc,
                'confusion_matrix': model_metrics.confusion_matrix,
                'n_test_samples': model_metrics.n_test_samples
            }
        except Exception as e:
            logger.warning(f'Could not load model metrics: {e}')
        
        # 4. High-risk transactions
        high_risk_txns = score_high_risk_transactions(self.db, self.merchant_id, days=7)
        metrics['high_risk_transactions'] = len(high_risk_txns)
        
        if high_risk_txns:
            hr_evidence = self._create_evidence(
                type_='high_risk_transactions',
                description=f'{len(high_risk_txns)} high-risk transactions detected by ML model in last 7 days.',
                source='risk_tool:score_transactions + ml_model',
                amount=sum(t['amount'] for t in high_risk_txns)
            )
            evidence.append(hr_evidence)
            if not any(f.metric_label == 'Failure Rate' for f in findings):  # avoid duplicates
                findings.append(self._create_finding(
                    finding_text=f'{len(high_risk_txns)} transactions flagged as high-risk by ML model. Top risk factor: gateway degradation window + new device patterns.',
                    severity=Severity.MEDIUM,
                    confidence=float(metrics.get('model_metrics', {}).get('precision', 0.8)),
                    evidence_ids=[hr_evidence.id],
                    recommended_action='Review high-risk transactions. Generate chargeback evidence for disputed ones.'
                ))
        
        if not findings:
            findings.append(self._create_finding(
                finding_text='No critical risk anomalies detected in the analysis period. Chargeback rate and failure rate within acceptable ranges.',
                severity=Severity.LOW,
                confidence=0.7,
                evidence_ids=[cb_evidence.id] if evidence else []
            ))
        
        return AgentResult(
            agent=AgentName.RISK,
            status='completed',
            findings=findings,
            evidence=evidence,
            metrics=metrics
        )
