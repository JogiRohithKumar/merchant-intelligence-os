"""
Cash Flow Forecasting Engine
Uses simple exponential smoothing with trend.
Never uses LLM for forecasting.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class CashForecast:
    forecast_dates: list[str]
    inflows: list[float]
    outflows: list[float]
    net: list[float]
    confidence_band_low: list[float]
    confidence_band_high: list[float]
    total_expected_inflow: float
    total_expected_outflow: float
    total_expected_net: float
    methodology: str = 'Exponential Smoothing with Trend (Holt\'s method)'
    data_points_used: int = 0

def _exponential_smoothing(series: list[float], alpha: float = 0.3) -> list[float]:
    """Simple exponential smoothing."""
    if not series:
        return []
    smoothed = [series[0]]
    for i in range(1, len(series)):
        smoothed.append(alpha * series[i] + (1 - alpha) * smoothed[-1])
    return smoothed

def _holts_forecast(series: list[float], horizon: int, alpha: float = 0.3, beta: float = 0.1) -> tuple[list[float], float]:
    """Holt's double exponential smoothing with trend component."""
    if len(series) < 3:
        avg = sum(series) / len(series) if series else 100_000
        return [avg] * horizon, avg * 0.15
    
    # Initialize
    level = series[0]
    trend = series[1] - series[0]
    
    for val in series[1:]:
        prev_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    
    # Compute standard deviation for confidence band
    import statistics
    std = statistics.stdev(series) if len(series) > 1 else abs(level) * 0.1
    
    forecast = [level + i * trend for i in range(1, horizon + 1)]
    return forecast, std

def forecast_cash_from_history(
    daily_inflows: list[float],
    daily_outflows: list[float],
    horizon_days: int = 30
) -> CashForecast:
    """
    Forecast cash flows based on historical data.
    daily_inflows: list of daily inflow amounts (most recent last)
    daily_outflows: list of daily outflow amounts (most recent last)
    """
    today = datetime.utcnow().date()
    
    inflow_forecast, inflow_std = _holts_forecast(daily_inflows, horizon_days)
    outflow_forecast, outflow_std = _holts_forecast(daily_outflows, horizon_days)
    
    forecast_dates = [(today + timedelta(days=i+1)).isoformat() for i in range(horizon_days)]
    net_forecast = [round(i - o, 2) for i, o in zip(inflow_forecast, outflow_forecast)]
    
    confidence_width = 1.645  # 90% confidence interval
    band_low = [round(n - confidence_width * (inflow_std + outflow_std), 2) for n in net_forecast]
    band_high = [round(n + confidence_width * (inflow_std + outflow_std), 2) for n in net_forecast]
    
    return CashForecast(
        forecast_dates=forecast_dates,
        inflows=[round(v, 2) for v in inflow_forecast],
        outflows=[round(v, 2) for v in outflow_forecast],
        net=net_forecast,
        confidence_band_low=band_low,
        confidence_band_high=band_high,
        total_expected_inflow=round(sum(inflow_forecast), 2),
        total_expected_outflow=round(sum(outflow_forecast), 2),
        total_expected_net=round(sum(net_forecast), 2),
        data_points_used=len(daily_inflows)
    )
