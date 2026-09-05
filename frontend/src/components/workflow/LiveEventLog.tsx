import React from 'react';
import { Terminal, Shield, RefreshCw, Layers, TrendingUp, Brain, ArrowRight, CheckCircle2, AlertTriangle } from 'lucide-react';

interface LiveEventLogProps {
  events: any[];
}

export default function LiveEventLog({ events }: LiveEventLogProps) {
  const getAgentBadge = (agent?: string) => {
    switch ((agent || '').toLowerCase()) {
      case 'finance':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-50 text-sky-700 border border-sky-200">FINANCE</span>;
      case 'risk':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">RISK</span>;
      case 'growth':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">GROWTH</span>;
      case 'recovery':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">RECOVERY</span>;
      default:
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">SUPERVISOR</span>;
    }
  };

  const formatTimestamp = (ts?: string) => {
    if (!ts) return '00:00:00';
    try {
      const d = new Date(ts);
      return d.toTimeString().split(' ')[0];
    } catch {
      return ts;
    }
  };

  return (
    <div className="w-full rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col h-[280px] overflow-hidden">
      {/* Console Header */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
          <Terminal className="w-3.5 h-3.5 text-sky-600" />
          <span>Real-Time Reasoning & Telemetry Stream</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-mono font-bold text-emerald-700">SSE TELEMETRY ACTIVE</span>
        </div>
      </div>

      {/* Terminal Lines Container */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-2 bg-slate-50/40">
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-400 text-xs italic font-sans">
            Awaiting query submission to establish telemetry stream...
          </div>
        ) : (
          events.map((e, idx) => (
            <div key={idx} className="flex items-start gap-2.5 text-slate-700 leading-relaxed hover:bg-white p-1.5 rounded-lg transition-colors border border-transparent hover:border-slate-200">
              <span className="text-[11px] text-slate-400 tabular-nums shrink-0 pt-0.5">
                {formatTimestamp(e.timestamp)}
              </span>
              <span className="shrink-0">
                {getAgentBadge(e.agent)}
              </span>
              <span className="text-slate-800 break-words flex-1 font-sans text-xs">
                {e.message}
              </span>
              {e.event_type === 'approval_required' && (
                <span className="px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded text-[9px] border border-amber-200 font-bold shrink-0">
                  REQUIRES REVIEW
                </span>
              )}
              {e.event_type === 'policy_evaluated' && e.data?.decision === 'ALLOW' && (
                <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded text-[9px] border border-emerald-200 font-bold shrink-0">
                  AUTO-APPROVED
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
