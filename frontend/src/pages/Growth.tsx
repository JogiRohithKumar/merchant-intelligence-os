import React, { useState } from 'react';
import TopNav from '../components/layout/TopNav';
import { TrendingUp, Play, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { formatINR } from '../utils/format';
import api from '../services/api';

export default function Growth() {
  const [params, setParams] = useState({
    campaign_type: 'reactivation',
    target_count: 5000,
    budget: 50000,
  });
  const [simulation, setSimulation] = useState<any>(null);
  const [productAnomalies, setProductAnomalies] = useState<any[]>([]);
  const [running, setRunning] = useState(false);

  React.useEffect(() => {
    api.get('/v1/growth/products/analysis')
      .then(res => {
        if (Array.isArray(res.data)) {
          setProductAnomalies(res.data);
        }
      })
      .catch(() => null);
  }, []);

  const handleSimulate = async () => {
    setRunning(true);
    try {
      const res = await api.post('/v1/growth/campaigns/simulate', params);
      if (res.data) setSimulation(res.data);
    } catch {
      // Keep state
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800">
      <TopNav pageTitle="Growth Specialist Console — Monte Carlo Simulation Engine" />
      <div className="p-6 flex-1 overflow-y-auto space-y-6">

        {/* Catalog Performance Signal */}
        {productAnomalies.length > 0 ? (
          <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 flex items-center justify-between shadow-sm">
            <div className="space-y-0.5">
              <div className="text-[10px] font-mono text-emerald-800 font-bold uppercase">
                CATALOG PERFORMANCE SIGNAL
              </div>
              <div className="text-xs font-bold text-emerald-950">
                {productAnomalies[0].product_name || 'Product'} (SKU: {productAnomalies[0].sku || productAnomalies[0].product_id}) Conversion Anomaly
              </div>
              <p className="text-[11px] text-emerald-700 font-sans">
                Conversion at {((productAnomalies[0].conversion_rate || 0) * 100).toFixed(1)}% against catalog baseline.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-white text-emerald-800 border border-emerald-200 shadow-sm">
              ISOLATED BY GROWTH AGENT
            </span>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-[10px] font-mono text-slate-500 font-bold uppercase">
                CATALOG PERFORMANCE MONITOR
              </div>
              <div className="text-xs font-bold text-slate-800">
                No Catalog Conversion Anomalies Detected
              </div>
              <p className="text-[11px] text-slate-500 font-sans">
                Catalog funnels are stable. Run a Monte Carlo experiment below to project uplift from new marketing initiatives.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-white text-slate-600 border border-slate-200">
              EQUILIBRIUM
            </span>
          </div>
        )}

        {/* Simulation Controls & Results */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 border-b border-slate-100 pb-3">
              MONTE CARLO EXPERIMENT PARAMETERS
            </h3>

            <div className="space-y-3.5 text-xs font-mono">
              <div>
                <label className="text-slate-500 block mb-1 font-medium">CAMPAIGN TYPE</label>
                <select 
                  value={params.campaign_type}
                  onChange={e => setParams({ ...params, campaign_type: e.target.value })}
                  className="w-full p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                >
                  <option value="reactivation">Customer Reactivation</option>
                  <option value="upsell">High-LTV Upsell</option>
                  <option value="cross_sell">Cross-Sell Basket</option>
                </select>
              </div>

              <div>
                <label className="text-slate-500 block mb-1 font-medium">TARGET AUDIENCE SIZE</label>
                <input 
                  type="number"
                  value={params.target_count}
                  onChange={e => setParams({ ...params, target_count: Number(e.target.value) })}
                  className="w-full p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-500 block mb-1 font-medium">BUDGET ALLOCATION (INR)</label>
                <input 
                  type="number"
                  value={params.budget}
                  onChange={e => setParams({ ...params, budget: Number(e.target.value) })}
                  className="w-full p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
                <span className="text-[10px] text-slate-400 mt-1 block">
                  Policy Auto-Approval limit: ₹50,000 INR
                </span>
              </div>

              <button
                onClick={handleSimulate}
                disabled={running}
                className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-mono text-xs font-semibold tracking-wider flex items-center justify-center gap-2 mt-4 transition-all cursor-pointer shadow-sm shadow-emerald-200"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>{running ? 'RUNNING 1000 ITERATIONS...' : 'RUN MONTE CARLO SIMULATION'}</span>
              </button>
            </div>
          </div>

          {/* Monte Carlo Results Display */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                STATISTICAL OUTCOMES & LIFT CURVE
              </h3>
              <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-bold">
                {simulation ? 'SIMULATED PREDICTION' : 'AWAITING SIMULATION'}
              </span>
            </div>

            {simulation ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500">EXPECTED REVENUE</span>
                    <div className="text-xl font-mono font-bold text-emerald-700">
                      {formatINR(simulation.expected_revenue || 0)}
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">Gross Return</span>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500">ESTIMATED ROI</span>
                    <div className="text-xl font-mono font-bold text-sky-600">
                      {(simulation.expected_roi || 0).toFixed(0)}%
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">Net of Budget</span>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500">P-VALUE SIGNIFICANCE</span>
                    <div className="text-xl font-mono font-bold text-indigo-600">
                      {simulation.p_value}
                    </div>
                    <span className="text-[10px] font-mono text-emerald-600 font-bold">
                      {simulation.is_significant ? 'Statistically Significant' : 'Insufficient Signal'}
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs font-mono">
                  <div className="text-slate-800 font-bold">Conversion Rate Comparison:</div>
                  <div className="flex items-center gap-4 text-slate-600">
                    <span>Control Group: <strong className="text-slate-900">{((simulation.control_conversion || 0) * 100).toFixed(1)}%</strong></span>
                    <span>&rarr;</span>
                    <span>Simulated Treatment: <strong className="text-emerald-700 font-bold">{((simulation.treatment_conversion || 0) * 100).toFixed(1)}%</strong></span>
                    <span className="ml-auto text-emerald-700 font-bold">+{simulation.lift_pct}% Lift</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-xs font-mono text-amber-900 leading-relaxed">
                  <strong>Risk Exclusions Applied:</strong> Filtered {simulation.risk_exclusions || 0} users exhibiting elevated risk scores from campaign dispatch to prevent chargebacks.
                </div>
              </>
            ) : (
              <div className="py-16 text-center text-xs font-mono text-slate-400">
                Configure experiment parameters on the left and click "RUN MONTE CARLO SIMULATION" to execute 1,000 synthetic trials.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
