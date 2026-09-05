import React, { useEffect, useState } from 'react';
import TopNav from '../components/layout/TopNav';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatINR } from '../utils/format';
import { Brain, Shield, AlertTriangle, Layers, ArrowUpRight, ArrowDownRight, RefreshCw, Zap, TrendingUp, PlusCircle, Link as LinkIcon } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuthStore } from '../store/auth';

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [recentWorkflows, setRecentWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const user = useAuthStore(state => state.user);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.get('/v1/merchant/dashboard').catch(() => null),
      api.get('/v1/workflows?limit=4').catch(() => null)
    ]).then(([dashRes, wfRes]) => {
      if (dashRes?.data) {
        setMetrics(dashRes.data);
        // If brand new user without merchant, redirect to web onboarding
        if (dashRes.data.has_merchant === false) {
          navigate('/onboarding');
          return;
        }
      }
      if (wfRes?.data) setRecentWorkflows(wfRes.data);
      setLoading(false);
    });
  }, [navigate]);

  if (loading) {
    return (
      <div className="flex flex-col h-full bg-slate-50/50 text-slate-800">
        <TopNav pageTitle="Operational Telemetry & Business Pulse" />
        <div className="p-8 flex items-center justify-center flex-1">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
            <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
            <span>Loading merchant operational telemetry...</span>
          </div>
        </div>
      </div>
    );
  }

  // Pure Zero-Data Experience for freshly created merchants with 0 transactions
  const isZeroData = !metrics || metrics.total_transactions === 0;

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800">
      <TopNav pageTitle="Operational Telemetry & Business Pulse" />
      <div className="p-6 flex-1 overflow-y-auto space-y-6">
        
        {/* Organization Banner with Dynamic Data Mode */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-sky-50 via-indigo-50 to-white border border-slate-200/80 shadow-sm relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1.5 z-10">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 border border-indigo-200 font-bold uppercase">
                {isZeroData ? 'AWAITING TELEMETRY' : 'AUTONOMOUS INTELLIGENCE ACTIVE'}
              </span>
              <span className="text-xs font-mono text-slate-700 font-bold uppercase">
                {metrics?.merchant_name || 'MERCHANT ORGANIZATION'}
              </span>
            </div>
            <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
              {isZeroData 
                ? 'Your Dedicated Merchant Environment is Ready' 
                : `Monitoring ${metrics?.total_transactions?.toLocaleString() || 0} Transactions Across 4 Financial Domains`}
            </h2>
            <p className="text-xs text-slate-600 font-normal max-w-2xl leading-relaxed">
              {isZeroData
                ? 'No financial transactions have been received yet for this merchant. Connect your payment provider or stream webhooks to activate autonomous multi-agent analysis.'
                : 'Real-time telemetry and deterministic financial engines are analyzing your ledger for revenue leaks, fraud, recovery opportunities, and settlement exceptions.'}
            </p>
          </div>
          <div className="z-10 shrink-0 flex items-center gap-2">
            {isZeroData ? (
              <Link 
                to="/onboarding"
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-mono text-xs font-semibold tracking-wider flex items-center gap-2 shadow-sm shadow-indigo-300 transition-all cursor-pointer"
              >
                <LinkIcon className="w-3.5 h-3.5" />
                <span>CONNECT RAZORPAY</span>
              </Link>
            ) : (
              <Link 
                to="/command"
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-mono text-xs font-semibold tracking-wider flex items-center gap-2 shadow-sm shadow-indigo-300 transition-all cursor-pointer"
              >
                <Brain className="w-4 h-4 text-sky-200" />
                <span>LAUNCH AI ASSISTANT</span>
              </Link>
            )}
          </div>
        </div>

        {/* Primary Financial KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPITerminalCard 
            title="TOTAL REVENUE (30D)"
            value={formatINR(metrics?.current_revenue || 0)}
            delta={isZeroData ? "0.0%" : `${metrics?.revenue_change_pct >= 0 ? '+' : ''}${metrics?.revenue_change_pct?.toFixed(1)}%`}
            isPositive={metrics?.revenue_change_pct >= 0}
            sub={isZeroData ? "No transaction history" : "vs prior period"}
            status={isZeroData ? "AWAITING DATA" : "ACTIVE"}
            statusColor={isZeroData ? "slate" : (metrics?.revenue_change_pct < 0 ? "rose" : "emerald")}
          />
          <KPITerminalCard 
            title="POTENTIALLY RECOVERABLE"
            value={formatINR(metrics?.recoverable_revenue || 0)}
            delta={isZeroData ? "0" : "Eligible"}
            isPositive={true}
            sub={isZeroData ? "No failed payments" : "P(recovery) >= 0.60"}
            status={isZeroData ? "ZERO FAILURES" : "OPPORTUNITY"}
            statusColor={isZeroData ? "slate" : "amber"}
          />
          <KPITerminalCard 
            title="RISK EXPOSURE"
            value={formatINR(metrics?.risk_exposure || 0)}
            delta={isZeroData ? "₹0" : "Chargebacks"}
            isPositive={false}
            sub={isZeroData ? "No chargebacks logged" : "Disputed volume"}
            status={isZeroData ? "CLEAN" : "ML DETECTED"}
            statusColor={isZeroData ? "emerald" : "rose"}
          />
          <KPITerminalCard 
            title="SETTLEMENT EXCEPTIONS"
            value={formatINR(metrics?.settlement_exceptions || 0)}
            delta={isZeroData ? "None" : "Discrepancy"}
            isPositive={false}
            sub={isZeroData ? "No payout shortfall" : "Reconciliation needed"}
            status={isZeroData ? "BALANCED" : "RECON NEEDED"}
            statusColor={isZeroData ? "slate" : "cyan"}
          />
        </div>

        {/* Two-Column Telemetry Surface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chart Area */}
          <div className="lg:col-span-2 space-y-6">
            <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                    REVENUE PULSE & SETTLEMENT VELOCITY (30 DAYS)
                  </h3>
                  <p className="text-[11px] text-slate-500 font-sans">
                    {isZeroData ? 'Chart displays daily net captured volume once transactions enter the ledger' : 'Shaded area indicates net daily captured volume in INR'}
                  </p>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 font-medium">
                  WINDOW: 30 DAYS
                </span>
              </div>
              <div className="h-64 w-full">
                {isZeroData ? (
                  <div className="h-full flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50 p-6 text-center">
                    <TrendingUp className="w-8 h-8 text-slate-300 mb-2" />
                    <span className="text-xs font-mono text-slate-600 font-semibold">No Transaction Telemetry Available</span>
                    <span className="text-[11px] text-slate-400 max-w-sm mt-1">
                      As soon as webhooks or payments arrive, your daily financial velocity curve will render automatically.
                    </span>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={metrics?.daily_chart || []}>
                      <defs>
                        <linearGradient id="dashRev" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366F1" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                      <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} stroke="#E2E8F0" />
                      <YAxis 
                        tickFormatter={(val) => `₹${(val/1000).toFixed(0)}k`} 
                        tick={{ fontSize: 10, fill: '#64748B' }} 
                        axisLine={false} 
                        tickLine={false} 
                        stroke="#E2E8F0" 
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '10px', fontSize: '11px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        formatter={(val: number) => [formatINR(val), 'Volume']} 
                      />
                      <Area type="monotone" dataKey="revenue" stroke="#4F46E5" strokeWidth={2} fillOpacity={1} fill="url(#dashRev)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Active Workflow Sessions */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm">
              <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                  RECENT MULTI-AGENT WORKFLOWS
                </h3>
                <Link to="/command" className="text-xs font-mono font-semibold text-indigo-600 hover:text-indigo-700">
                  Launch New Session &rarr;
                </Link>
              </div>
              <div className="divide-y divide-slate-100">
                {recentWorkflows.length > 0 ? (
                  recentWorkflows.map(w => (
                    <div key={w.id} className="py-3 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-100">
                          <Brain className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900">{w.user_query}</div>
                          <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                            ID: {w.id.slice(0, 12)}... • Intent: {w.intent || 'revenue_investigation'}
                          </div>
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        w.status === 'completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      }`}>
                        {w.status.toUpperCase()}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="py-6 text-center text-xs font-mono text-slate-400">
                    No recent workflows recorded for this merchant. Execute an operational query in the AI Command Center.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Autonomous Signals */}
          <div className="space-y-4">
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                    AUTONOMOUS SIGNALS
                  </h3>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                  MERCHANT TELEMETRY
                </span>
              </div>

              {metrics?.ai_insights && metrics.ai_insights.length > 0 ? (
                metrics.ai_insights.map((insight: any, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-indigo-700 uppercase">
                        {insight.type} SPECIALIST
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">LIVE</span>
                    </div>
                    <div className="text-xs font-bold text-slate-900">{insight.title || 'Signal Detected'}</div>
                    <p className="text-[11px] text-slate-600 font-sans leading-relaxed">{insight.message}</p>
                  </div>
                ))
              ) : (
                <div className="p-6 text-center text-xs font-mono text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  No anomalous financial signals detected for this merchant. Ledger is balanced and clean.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

function KPITerminalCard({ title, value, delta, isPositive, sub, status, statusColor }: any) {
  const colorMap: Record<string, string> = {
    rose: 'text-rose-700 border-rose-200 bg-rose-50',
    amber: 'text-amber-700 border-amber-200 bg-amber-50',
    cyan: 'text-sky-700 border-sky-200 bg-sky-50',
    emerald: 'text-emerald-700 border-emerald-200 bg-emerald-50',
    slate: 'text-slate-600 border-slate-200 bg-slate-100',
  };

  return (
    <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-2.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-slate-500 font-bold uppercase tracking-wider">{title}</span>
        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border font-semibold ${colorMap[statusColor] || colorMap.slate}`}>
          {status}
        </span>
      </div>
      <div className="text-xl font-mono font-bold text-slate-900 tabular-nums">
        {value}
      </div>
      <div className="flex items-center justify-between text-[11px] font-mono border-t border-slate-100 pt-2 text-slate-500">
        <span className={isPositive ? 'text-emerald-600 font-bold' : 'text-rose-600 font-bold'}>
          {delta}
        </span>
        <span className="truncate">{sub}</span>
      </div>
    </div>
  );
}
