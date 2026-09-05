import React from 'react';
import { Shield, Layers, TrendingUp, RefreshCw, FileText, ChevronRight } from 'lucide-react';

interface FindingCardProps {
  finding: {
    id?: string;
    agent: string;
    confidence: number;
    severity: string;
    text: string;
    metric_change?: {
      prev: string;
      current: string;
      delta: number;
    };
    recommended_action?: string;
    evidence_ids?: string[];
  };
  onViewEvidence?: (finding: any) => void;
}

export default function FindingCard({ finding, onViewEvidence }: FindingCardProps) {
  const getAgentTheme = (agent: string) => {
    switch (agent.toLowerCase()) {
      case 'finance':
        return { text: 'text-sky-700', badge: 'bg-sky-50 border-sky-200 text-sky-700', icon: Layers };
      case 'risk':
        return { text: 'text-rose-700', badge: 'bg-rose-50 border-rose-200 text-rose-700', icon: Shield };
      case 'growth':
        return { text: 'text-emerald-700', badge: 'bg-emerald-50 border-emerald-200 text-emerald-700', icon: TrendingUp };
      default:
        return { text: 'text-amber-700', badge: 'bg-amber-50 border-amber-200 text-amber-700', icon: RefreshCw };
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
      case 'high':
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">HIGH SEVERITY</span>;
      case 'medium':
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">MEDIUM SEVERITY</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-50 text-sky-700 border border-sky-200">LOW SEVERITY</span>;
    }
  };

  const theme = getAgentTheme(finding.agent);
  const Icon = theme.icon;

  return (
    <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs hover:border-slate-300 transition-all duration-200 group flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded-lg border ${theme.badge}`}>
              <Icon className="w-3.5 h-3.5" />
            </div>
            <span className={`text-xs font-bold uppercase tracking-tight font-sans ${theme.text}`}>
              {finding.agent}
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              {finding.confidence}% Conf.
            </span>
          </div>
          {getSeverityBadge(finding.severity)}
        </div>

        {/* Text */}
        <p className="text-xs text-slate-700 font-sans leading-relaxed mb-3">
          {finding.text}
        </p>

        {/* Metric Delta Badge if available */}
        {finding.metric_change && (
          <div className="flex items-center gap-3 p-2 rounded-xl bg-slate-50 border border-slate-200/80 text-xs font-mono text-slate-600 mb-3">
            <span>Prior: <strong className="text-slate-800">{finding.metric_change.prev}</strong></span>
            <span>&rarr;</span>
            <span>Current: <strong className="text-rose-600">{finding.metric_change.current}</strong></span>
            <span className="ml-auto text-rose-600 font-bold">
              {finding.metric_change.delta > 0 ? `+${finding.metric_change.delta}%` : `${finding.metric_change.delta}%`}
            </span>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between mt-1">
        <div className="text-[11px] text-slate-500 font-sans truncate max-w-[200px]">
          {finding.recommended_action || 'Actionable resolution proposed'}
        </div>
        {onViewEvidence && (
          <button 
            onClick={() => onViewEvidence(finding)}
            className="flex items-center gap-1 text-xs font-semibold text-sky-600 hover:text-sky-800 group-hover:translate-x-0.5 transition-transform cursor-pointer"
          >
            <span>Evidence</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
