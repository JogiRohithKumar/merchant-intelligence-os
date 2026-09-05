import React, { useEffect, useState } from 'react';
import { ShieldCheck, Activity, Database, Zap, AlertCircle } from 'lucide-react';
import api from '../../services/api';

export type SystemOperatingState = 'HEALTHY' | 'READY' | 'DEGRADED' | 'OFFLINE' | 'STANDBY' | 'ANALYZING' | 'ROUTING' | 'EXECUTING' | 'COMPLETE' | 'ERROR' | 'GUARDED';

interface SystemStatusIndicatorProps {
  systemState?: SystemOperatingState;
  onRefreshHealth?: () => void;
}

export default function SystemStatusIndicator({
  systemState = 'STANDBY',
  onRefreshHealth
}: SystemStatusIndicatorProps) {
  const [health, setHealth] = useState<{
    database?: string;
    data_mode?: string;
    demo_mode?: boolean;
    automated_execution_enabled?: boolean;
    status?: string;
  }>({
    database: 'connected',
    data_mode: 'SANDBOX',
    demo_mode: true,
    automated_execution_enabled: false,
    status: 'healthy'
  });

  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      // Health is served at /api/health (proxied to backend)
      const res = await api.get('/health');
      if (res.data) setHealth(res.data);
    } catch {
      setHealth(prev => ({ ...prev, database: 'disconnected', status: 'degraded' }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const stateColors: Record<string, { bg: string; text: string; dot: string; border: string }> = {
    HEALTHY: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', border: 'border-emerald-300' },
    READY: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', border: 'border-emerald-300' },
    STANDBY: { bg: 'bg-slate-50', text: 'text-slate-600', dot: 'bg-slate-400', border: 'border-slate-200' },
    GUARDED: { bg: 'bg-slate-100', text: 'text-slate-700', dot: 'bg-slate-500', border: 'border-slate-300' },
    DEGRADED: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500', border: 'border-amber-300' },
    OFFLINE: { bg: 'bg-rose-50', text: 'text-rose-700', dot: 'bg-rose-500', border: 'border-rose-300' },
    ANALYZING: { bg: 'bg-sky-50', text: 'text-sky-700', dot: 'bg-sky-500 animate-pulse', border: 'border-sky-300' },
    ROUTING: { bg: 'bg-indigo-50', text: 'text-indigo-700', dot: 'bg-indigo-500 animate-ping', border: 'border-indigo-300' },
    EXECUTING: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500 animate-spin', border: 'border-amber-300' },
    COMPLETE: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', border: 'border-emerald-300' },
    ERROR: { bg: 'bg-rose-50', text: 'text-rose-700', dot: 'bg-rose-500', border: 'border-rose-300' },
  };

  const st = stateColors[systemState] || stateColors.STANDBY;

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {/* Operating State Badge */}
      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${st.border} ${st.bg} ${st.text} font-mono font-bold text-[11px] shadow-xs`}>
        <span className={`w-2 h-2 rounded-full ${st.dot}`} />
        <span>STATUS: {systemState}</span>
      </div>

      {/* Backend & DB Health */}
      <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100/80 border border-slate-200 text-slate-600 text-[11px] font-mono">
        <span className={`w-1.5 h-1.5 rounded-full ${health.database === 'connected' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
        <span>DB: {health.database === 'connected' ? 'ONLINE' : 'OFFLINE'}</span>
      </div>

      {/* Razorpay Gateway Mode */}
      <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-[11px] font-mono font-medium">
        <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
        <span>RAZORPAY: {health.data_mode || 'SANDBOX'}</span>
      </div>

      {/* Automated Execution Safeguard */}
      <div className={`hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-mono ${
        health.automated_execution_enabled 
          ? 'bg-amber-50 border-amber-300 text-amber-700 font-bold' 
          : 'bg-slate-100 border-slate-200 text-slate-500'
      }`}>
        <Zap className="w-3.5 h-3.5" />
        <span>AUTO-EXEC: {health.automated_execution_enabled ? 'LIVE' : 'GUARDED (OFF)'}</span>
      </div>
    </div>
  );
}
