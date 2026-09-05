from enum import Enum
from pydantic import BaseModel
from app.schemas.state import AgentName

class AgentCapability(str, Enum):
    RECONCILIATION = 'reconciliation'
    CASH_FORECASTING = 'cash_forecasting'
    SETTLEMENT_INVESTIGATION = 'settlement_investigation'
    TAX_MATCHING = 'tax_matching'
    FRAUD_SCORING = 'fraud_scoring'
    ANOMALY_DETECTION = 'anomaly_detection'
    CHARGEBACK_ANALYSIS = 'chargeback_analysis'
    CUSTOMER_RISK_SCORING = 'customer_risk_scoring'
    FAILED_PAYMENT_RECOVERY = 'failed_payment_recovery'
    CHECKOUT_RECOVERY = 'checkout_recovery'
    SUBSCRIPTION_RECOVERY = 'subscription_recovery'
    RECEIVABLES = 'receivables'
    CAMPAIGN_SIMULATION = 'campaign_simulation'
    CUSTOMER_REACTIVATION = 'customer_reactivation'
    UPSELL_RECOMMENDATION = 'upsell_recommendation'
    CONVERSION_ANALYSIS = 'conversion_analysis'
    REVENUE_ANALYSIS = 'revenue_analysis'

class AgentRegistryEntry(BaseModel):
    name: AgentName
    description: str
    capabilities: list[AgentCapability]
    tools: list[str]
    risk_level: str
    requires_approval: bool
    execution_priority: int

class AgentRegistry:
    def __init__(self):
        self._registry: dict[AgentName, AgentRegistryEntry] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        self._registry[AgentName.FINANCE] = AgentRegistryEntry(
            name=AgentName.FINANCE,
            description='Financial reconciliation, settlement analysis, cash forecasting',
            capabilities=[
                AgentCapability.RECONCILIATION,
                AgentCapability.CASH_FORECASTING,
                AgentCapability.SETTLEMENT_INVESTIGATION,
                AgentCapability.TAX_MATCHING,
                AgentCapability.REVENUE_ANALYSIS
            ],
            tools=['get_transactions', 'get_settlements', 'reconcile', 'get_settlement', 'forecast_cash', 'find_exceptions'],
            risk_level='low',
            requires_approval=False,
            execution_priority=1
        )
        self._registry[AgentName.RISK] = AgentRegistryEntry(
            name=AgentName.RISK,
            description='Fraud detection, chargeback analysis, risk scoring',
            capabilities=[
                AgentCapability.FRAUD_SCORING,
                AgentCapability.ANOMALY_DETECTION,
                AgentCapability.CHARGEBACK_ANALYSIS,
                AgentCapability.CUSTOMER_RISK_SCORING
            ],
            tools=['score_risk', 'detect_anomaly', 'get_chargebacks', 'generate_chargeback_evidence', 'get_customer_risk'],
            risk_level='medium',
            requires_approval=False,
            execution_priority=2
        )
        self._registry[AgentName.RECOVERY] = AgentRegistryEntry(
            name=AgentName.RECOVERY,
            description='Failed payment recovery, subscription recovery, receivables',
            capabilities=[
                AgentCapability.FAILED_PAYMENT_RECOVERY,
                AgentCapability.CHECKOUT_RECOVERY,
                AgentCapability.SUBSCRIPTION_RECOVERY,
                AgentCapability.RECEIVABLES
            ],
            tools=['get_failed_payments', 'calculate_recovery_probability', 'schedule_retry', 'create_recovery_task'],
            risk_level='high',
            requires_approval=True,
            execution_priority=3  # runs after risk
        )
        self._registry[AgentName.GROWTH] = AgentRegistryEntry(
            name=AgentName.GROWTH,
            description='Campaign simulation, upsell, customer reactivation, conversion analysis',
            capabilities=[
                AgentCapability.CAMPAIGN_SIMULATION,
                AgentCapability.CUSTOMER_REACTIVATION,
                AgentCapability.UPSELL_RECOMMENDATION,
                AgentCapability.CONVERSION_ANALYSIS
            ],
            tools=['get_catalog', 'get_conversion_metrics', 'simulate_campaign', 'recommend_upsell'],
            risk_level='medium',
            requires_approval=True,  # campaigns need approval
            execution_priority=4
        )
    
    def find_agents_for_capabilities(self, required_capabilities: list[str]) -> list[AgentName]:
        needed = set(required_capabilities)
        matched = []
        for name, entry in self._registry.items():
            agent_caps = {c.value for c in entry.capabilities}
            if needed & agent_caps:
                matched.append(name)
        return sorted(matched, key=lambda n: self._registry[n].execution_priority)
    
    def get_agent(self, name: AgentName) -> AgentRegistryEntry:
        if name not in self._registry:
            raise KeyError(f'Agent {name} not registered')
        return self._registry[name]
    
    def all_agents(self) -> list[AgentRegistryEntry]:
        return sorted(self._registry.values(), key=lambda e: e.execution_priority)
    
    def register(self, entry: AgentRegistryEntry):
        """Register a new agent (extensible)"""
        self._registry[entry.name] = entry

# Singleton
agent_registry = AgentRegistry()
