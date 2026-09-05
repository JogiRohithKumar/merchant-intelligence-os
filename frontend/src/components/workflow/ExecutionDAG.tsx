import React from 'react';
import { Brain, Shield, TrendingUp, RefreshCw, Layers, CheckCircle2, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { formatINR } from '../../utils/format';

interface ExecutionDAGProps {
  events: any[];
  findings?: any[];
  actions?: any[];
  activeAgent?: string;
}

export default function ExecutionDAG({ events, findings = [], actions = [], activeAgent }: ExecutionDAGProps) {
  // Derive status for each agent
  const getAgentState = (name: string) => {
    const agentEvents = events.filter(e => (e.agent || '').toLowerCase() === name.toLowerCase());
    if (agentEvents.length === 0) return { status: 'waiting', lastMessage: 'Standby' };
    
    const isCompleted = agentEvents.some(e => e.event_type === 'agent_completed') || 
                        events.some(e => e.event_type === 'workflow_completed');
    if (isCompleted) {
      const completionEvent = agentEvents.find(e => e.event_type === 'agent_completed');
      return { status: 'completed', lastMessage: completionEvent?.message || 'Execution Complete' };
    }
    
    const hasError = agentEvents.some(e => e.event_type === 'workflow_failed');
    if (hasError) return { status: 'failed', lastMessage: 'Execution Interrupted' };

    const lastEvent = agentEvents[agentEvents.length - 1];
    return { status: 'running', lastMessage: lastEvent?.message || 'Analyzing Telemetry...' };
  };

  const supervisorState = getAgentState('supervisor');
  const financeState = getAgentState('finance');
  const riskState = getAgentState('risk');
  const growthState = getAgentState('growth');
  const recoveryState = getAgentState('recovery');

  // Policy & Execution counts
  const approvedActions = actions.filter(a => a.status === 'APPROVED').length;
  const pendingActions = actions.filter(a => a.status === 'PENDING_APPROVAL').length;
  const policyEvaluated = events.some(e => e.event_type === 'policy_evaluated' || e.event_type === 'approval_required');

  return (
    <div className="relative w-full rounded-2xl bg-white p-6 overflow-hidden border border-slate-200/90 shadow-xs">
      {/* Subtle Background Grid Pattern */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-25" 
        style={{ 
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(14, 165, 233, 0.4) 1px, transparent 0)', 
          backgroundSize: '24px 24px' 
        }} 
      />

      {/* SVG Connecting Flow Lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" aria-hidden="true">
        <defs>
          <linearGradient id="activeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#6366F1" />
            <stop offset="100%" stopColor="#0284C7" />
          </linearGradient>
        </defs>
        
        {/* Supervisor to Specialists */}
        <path 
          d="M 50% 90 L 22% 165" 
          stroke={financeState.status === 'running' ? 'url(#activeGrad)' : financeState.status === 'completed' ? '#CBD5E1' : '#E2E8F0'} 
          strokeWidth="2" 
          fill="none" 
          className={financeState.status === 'running' ? 'flow-line-active' : ''} 
        />
        <path 
          d="M 50% 90 L 50% 165" 
          stroke={riskState.status === 'running' ? 'url(#activeGrad)' : riskState.status === 'completed' ? '#CBD5E1' : '#E2E8F0'} 
          strokeWidth="2" 
          fill="none" 
          className={riskState.status === 'running' ? 'flow-line-active' : ''} 
        />
        <path 
          d="M 50% 90 L 78% 165" 
          stroke={growthState.status === 'running' ? 'url(#activeGrad)' : growthState.status === 'completed' ? '#CBD5E1' : '#E2E8F0'} 
          strokeWidth="2" 
          fill="none" 
          className={growthState.status === 'running' ? 'flow-line-active' : ''} 
        />

        {/* Specialists converge into Recovery Engine */}
        <path 
          d="M 22% 265 L 50% 320" 
          stroke={recoveryState.status === 'running' ? '#059669' : recoveryState.status === 'completed' ? '#CBD5E1' : '#E2E8F0'} 
          strokeWidth="2" 
          fill="none" 
          className={recoveryState.status === 'running' ? 'flow-line-active' : ''} 
        />
        <path 
          d="M 50% 265 L 50% 320" 
          stroke={recoveryState.status === 'running' ? '#059669' : recoveryState.status === 'completed' ? '#CBD5E1' : '#E2E8F0'} 
          strokeWidth="2" 
          fill="none" 
          className={recoveryState.status === 'running' ? 'flow-line-active' : ''} 
        />
        <path 
          d="M 78% 265 L 50% 320" 
          stroke={recoveryState.status === 'running' ? '#059669' : recoveryState.status === 'completed' ? '#CBD5E1' : '#E2E8F0'} 
          strokeWidth="2" 
          fill="none" 
          className={recoveryState.status === 'running' ? 'flow-line-active' : ''} 
        />

        {/* Recovery to Policy Engine */}
        <path 
          d="M 50% 410 L 50% 460" 
          stroke={policyEvaluated ? '#D97706' : '#E2E8F0'} 
          strokeWidth="2" 
          fill="none" 
          className={policyEvaluated && recoveryState.status === 'completed' ? 'flow-line-active' : ''} 
        />
      </svg>

      <div className="relative z-10 flex flex-col items-center gap-7">
        {/* 1. SUPERVISOR CORE */}
        <div className="relative flex flex-col items-center">
          <div className={`p-4 rounded-2xl border transition-all duration-300 flex items-center gap-3.5 bg-white ${
            supervisorState.status === 'running' 
              ? 'border-indigo-400 shadow-md shadow-indigo-100 ring-2 ring-indigo-50' 
              : supervisorState.status === 'completed'
              ? 'border-indigo-200 shadow-2xs'
              : 'border-slate-200 opacity-90'
          }`}>
            <div className="relative p-2.5 rounded-xl bg-gradient-to-tr from-indigo-500 to-sky-500 text-white shadow-xs">
              <Brain className="w-5 h-5" />
              {supervisorState.status === 'running' && (
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
                </span>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold tracking-tight uppercase text-indigo-900 font-sans">SUPERVISOR ORCHESTRATOR</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                  supervisorState.status === 'running' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-100 text-slate-600'
                }`}>
                  {supervisorState.status.toUpperCase()}
                </span>
              </div>
              <div className="text-xs text-slate-600 font-normal mt-0.5 max-w-xs truncate">
                {supervisorState.lastMessage}
              </div>
            </div>
          </div>
        </div>

        {/* 2. SPECIALIST LAYER (PARALLEL) */}
        <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          {/* Finance Node */}
          <AgentNode 
            name="FINANCE SPECIALIST"
            icon={Layers}
            color="cyan"
            state={financeState}
            signals={["Reconciliation", "Cash Forecasting", "Settlements"]}
            findingsCount={findings.filter(f => (f.agent || '').toLowerCase() === 'finance').length}
          />

          {/* Risk Node */}
          <AgentNode 
            name="RISK SPECIALIST"
            icon={Shield}
            color="rose"
            state={riskState}
            signals={["RF Model (AUC 0.996)", "Chargebacks", "Fraud Rings"]}
            findingsCount={findings.filter(f => (f.agent || '').toLowerCase() === 'risk').length}
          />

          {/* Growth Node */}
          <AgentNode 
            name="GROWTH SPECIALIST"
            icon={TrendingUp}
            color="emerald"
            state={growthState}
            signals={["Conversion Funnel", "Product Drops", "A/B Simulation"]}
            findingsCount={findings.filter(f => (f.agent || '').toLowerCase() === 'growth').length}
          />
        </div>

        {/* 3. RECOVERY ENGINE (DEPENDENT / SEQUENTIAL) */}
        <div className="w-full max-w-md pt-1">
          <div className={`p-4 rounded-xl border transition-all duration-300 flex items-center justify-between bg-white ${
            recoveryState.status === 'running'
              ? 'border-amber-400 shadow-md shadow-amber-50 ring-2 ring-amber-50'
              : recoveryState.status === 'completed'
              ? 'border-amber-200 shadow-2xs'
              : 'border-slate-200 opacity-90'
          }`}>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-50 text-amber-600 border border-amber-200">
                <RefreshCw className={`w-4 h-4 ${recoveryState.status === 'running' ? 'animate-spin' : ''}`} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold tracking-tight uppercase text-amber-900">RECOVERY ENGINE</span>
                  <span className="text-[10px] font-mono px-2 py-0.2 bg-amber-50 text-amber-700 rounded border border-amber-200 font-semibold">
                    P(RECOVERY) SCORER
                  </span>
                </div>
                <div className="text-xs text-slate-600 font-normal mt-0.5">
                  {recoveryState.status === 'completed' 
                    ? `Scored candidates & proposed ${actions.length} retries`
                    : recoveryState.lastMessage}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs font-mono font-bold text-amber-700">
                {actions.length > 0 ? `${actions.length} ACTIONS` : 'STANDBY'}
              </div>
            </div>
          </div>
        </div>

        {/* 4. POLICY ENGINE & EXECUTION CHECKPOINT */}
        <div className="w-full max-w-md flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200/90 shadow-2xs">
          <div className="p-2 rounded-lg bg-sky-100 text-sky-700">
            <Shield className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold tracking-tight text-slate-900">DETERMINISTIC POLICY CHECKPOINT</span>
              <span className="text-[10px] font-mono text-slate-400 font-semibold">HARD GUARDS</span>
            </div>
            <div className="flex items-center gap-4 mt-1 text-xs text-slate-500 font-sans">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Auto-Eligible: <strong className="text-slate-800 font-mono">{approvedActions}</strong>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                Human Review: <strong className="text-slate-800 font-mono">{pendingActions}</strong>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Reusable Agent Node Component
function AgentNode({ name, icon: Icon, color, state, signals, findingsCount }: any) {
  const colorMap: Record<string, { border: string; activeBorder: string; text: string; bg: string; badge: string }> = {
    cyan: {
      border: 'border-slate-200 hover:border-sky-200',
      activeBorder: 'border-sky-400 ring-2 ring-sky-50 shadow-md shadow-sky-50',
      text: 'text-sky-700',
      bg: 'bg-sky-50 text-sky-600 border-sky-200',
      badge: 'text-sky-700 bg-sky-50'
    },
    rose: {
      border: 'border-slate-200 hover:border-rose-200',
      activeBorder: 'border-rose-400 ring-2 ring-rose-50 shadow-md shadow-rose-50',
      text: 'text-rose-700',
      bg: 'bg-rose-50 text-rose-600 border-rose-200',
      badge: 'text-rose-700 bg-rose-50'
    },
    emerald: {
      border: 'border-slate-200 hover:border-emerald-200',
      activeBorder: 'border-emerald-400 ring-2 ring-emerald-50 shadow-md shadow-emerald-50',
      text: 'text-emerald-700',
      bg: 'bg-emerald-50 text-emerald-600 border-emerald-200',
      badge: 'text-emerald-700 bg-emerald-50'
    }
  };

  const scheme = colorMap[color];
  const isRunning = state.status === 'running';
  const isCompleted = state.status === 'completed';

  return (
    <div className={`p-4 rounded-xl border transition-all duration-300 bg-white ${
      isRunning 
        ? `${scheme.activeBorder}` 
        : isCompleted 
        ? `border-slate-200 shadow-2xs`
        : `border-slate-200/80 opacity-90`
    }`}>
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg border ${scheme.bg}`}>
            <Icon className="w-3.5 h-3.5" />
          </div>
          <span className={`text-xs font-bold tracking-tight font-sans ${scheme.text}`}>{name}</span>
        </div>
        <div>
          {isRunning ? (
            <Loader2 className="w-4 h-4 animate-spin text-sky-600" />
          ) : isCompleted ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-slate-300 inline-block" />
          )}
        </div>
      </div>

      <div className="text-xs text-slate-600 min-h-[32px] font-sans line-clamp-2">
        {state.lastMessage}
      </div>

      <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span>Signals: {signals.length}</span>
        <span className="text-slate-700 font-bold">{findingsCount > 0 ? `${findingsCount} Findings` : 'Scanning'}</span>
      </div>
    </div>
  );
}
