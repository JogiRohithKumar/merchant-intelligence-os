"""
A/B Campaign Simulation Engine
Monte Carlo simulation — deterministic when seeded.
Never uses LLM for simulation results.
"""
import random
import math
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class SimulationResult:
    campaign_type: str
    target_count: int
    risk_exclusions: int
    control_conversion: float
    treatment_conversion: float
    lift_pct: float
    expected_revenue: float
    expected_roi: float
    confidence_low: float
    confidence_high: float
    p_value: float
    is_significant: bool
    budget: float
    simulations_run: int = 1000

def simulate_campaign(params: dict, historical_data: dict, seed: int = 42) -> SimulationResult:
    """
    Simulate a marketing campaign using Monte Carlo approach.
    params: {campaign_type, target_segment, target_count, budget, duration_days}
    historical_data: {current_conversion, avg_order_value, segment_risk_rate}
    """
    rng = random.Random(seed)
    
    target_count = int(params.get('target_count', 5000))
    budget = float(params.get('budget', 50_000))
    campaign_type = params.get('campaign_type', 'reactivation')
    
    current_conversion = historical_data.get('current_conversion', 0.038)
    avg_order_value = historical_data.get('avg_order_value', 2500)
    segment_risk_rate = historical_data.get('segment_risk_rate', 0.1)
    
    # Exclude high-risk customers
    risk_exclusions = int(target_count * segment_risk_rate)
    effective_count = target_count - risk_exclusions
    
    # Expected lift by campaign type
    lift_estimates = {
        'reactivation': 0.18,   # 18% lift on conversion
        'upsell': 0.12,
        'cross_sell': 0.10,
        'new_customer': 0.22
    }
    expected_lift = lift_estimates.get(campaign_type, 0.15)
    treatment_conversion = current_conversion * (1 + expected_lift)
    
    # Monte Carlo: 1000 simulations
    n_sims = 1000
    revenue_samples = []
    for _ in range(n_sims):
        converted = sum(1 for _ in range(effective_count) if rng.random() < treatment_conversion)
        revenue = converted * avg_order_value * rng.uniform(0.85, 1.15)
        revenue_samples.append(revenue)
    
    revenue_samples.sort()
    expected_revenue = sum(revenue_samples) / n_sims
    conf_low = revenue_samples[int(n_sims * 0.025)]
    conf_high = revenue_samples[int(n_sims * 0.975)]
    
    expected_roi = (expected_revenue - budget) / budget if budget > 0 else 0
    
    # p-value (simplified two-proportion z-test)
    n = effective_count // 2  # control and treatment each get half
    p1 = current_conversion
    p2 = treatment_conversion
    p_pool = (p1 + p2) / 2
    if p_pool > 0 and p_pool < 1 and n > 0:
        se = math.sqrt(p_pool * (1 - p_pool) * (2 / n))
        z = abs(p2 - p1) / (se + 1e-10)
        p_value = 2 * (1 - _normal_cdf(z))  # two-tailed
    else:
        p_value = 1.0
    
    return SimulationResult(
        campaign_type=campaign_type,
        target_count=target_count,
        risk_exclusions=risk_exclusions,
        control_conversion=round(current_conversion, 4),
        treatment_conversion=round(treatment_conversion, 4),
        lift_pct=round(expected_lift * 100, 2),
        expected_revenue=round(expected_revenue, 2),
        expected_roi=round(expected_roi * 100, 2),
        confidence_low=round(conf_low, 2),
        confidence_high=round(conf_high, 2),
        p_value=round(p_value, 4),
        is_significant=p_value < 0.05,
        budget=budget
    )

def _normal_cdf(z: float) -> float:
    """Approximation of normal CDF."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))
