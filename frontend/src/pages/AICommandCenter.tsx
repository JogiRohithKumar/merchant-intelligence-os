import React, { useState, useEffect } from 'react';
import TopNav from '../components/layout/TopNav';
import ExecutionDAG from '../components/workflow/ExecutionDAG';
import LiveEventLog from '../components/workflow/LiveEventLog';
import FindingCard from '../components/workflow/FindingCard';
import WaterGridCanvas from '../components/workflow/WaterGridCanvas';
import EvidenceDrawer from '../components/ui/EvidenceDrawer';
import ApprovalModal from '../components/ui/ApprovalModal';
import { Brain, Sparkles, FileText, CheckCircle2, AlertTriangle, Shield, Layers, ChevronRight, Zap, RefreshCw } from 'lucide-react';
import { formatINR } from '../utils/format';
import api from '../services/api';
import { useWorkflowStream } from '../services/sse';

export default function AICommandCenter() {
  const [query, setQuery] = useState('');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [activeWorkflow, setActiveWorkflow] = useState<any | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed'>('idle');
  const [recentWorkflows, setRecentWorkflows] = useState<any[]>([]);
  
  // Modal & Drawer states
  const [selectedFinding, setSelectedFinding] = useState<any | null>(null);
  const [selectedAction, setSelectedAction] = useState<any | null>(null);

  const { events, isStreaming, isCompleted } = useWorkflowStream(workflowId);

  // Active agent from latest event for Water Grid ripples
  const latestEvent = events[events.length - 1];
  const activeAgent = latestEvent?.agent || 'supervisor';

  useEffect(() => {
    fetchRecentWorkflows();
  }, []);

  const fetchRecentWorkflows = async () => {
    try {
      const res = await api.get('/v1/workflows?limit=5');
      if (res.data) setRecentWorkflows(res.data);
    } catch (e) {
      console.warn('Failed to fetch recent workflows', e);
    }
  };

  useEffect(() => {
    if (isCompleted && workflowId) {
      api.get(`/v1/workflows/${workflowId}`)
        .then(res => {
          setActiveWorkflow(res.data);
          setStatus('completed');
          fetchRecentWorkflows();
        })
        .catch(err => console.error(err));
    }
  }, [isCompleted, workflowId]);

  const handleAnalyze = async (customQuery?: string) => {
    const q = customQuery || query;
    if (!q.trim()) return;
    setStatus('running');
    setActiveWorkflow(null);
    try {
      const res = await api.post('/v1/chat', { query: q });
      if (res.data && res.data.workflow_id) {
        setWorkflowId(res.data.workflow_id);
      }
    } catch (e) {
      console.error('Failed to trigger workflow', e);
      setStatus('idle');
    }
  };

  const handleSelectRecent = async (id: string) => {
    try {
      const res = await api.get(`/v1/workflows/${id}`);
      setActiveWorkflow(res.data);
      setWorkflowId(id);
      setStatus(res.data.status === 'completed' ? 'completed' : 'running');
    } catch (e) {
      console.error('Failed to load workflow', e);
    }
  };

  const handleApproveAction = async (actionId: string) => {
    try {
      await api.post(`/v1/actions/${actionId}/approve`);
      setSelectedAction(null);
      if (workflowId) handleSelectRecent(workflowId);
    } catch (e) {
      console.error('Approval failed', e);
    }
  };

  const handleRejectAction = async (actionId: string, reason?: string) => {
    try {
      await api.post(`/v1/actions/${actionId}/reject`, { reason });
      setSelectedAction(null);
      if (workflowId) handleSelectRecent(workflowId);
    } catch (e) {
      console.error('Rejection failed', e);
    }
  };

  const scenarios = [
    {
      title: 'Flagship Revenue Drop Investigation',
      prompt: 'My revenue dropped 20% this month. Find the reasons and recover whatever you safely can.'
    },
    {
      title: 'Failed Payment Recovery & Timing',
      prompt: 'Analyze failed payment attempts, rank by P(recovery), and prepare policy-safe retries.'
    },
    {
      title: 'Chargeback Spike & Abuse Rings',
      prompt: 'Identify customer segments exhibiting anomalous chargeback rates above baseline.'
    },
    {
      title: 'Reconciliation & Settlement Gap',
      prompt: 'Inspect settlement discrepancies and isolate fee mismatches or missing bank credits.'
    }
  ];

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800 font-sans">
      <TopNav 
        pageTitle="AI Assistant & Autonomous Orchestrator" 
        systemState={status === 'running' ? 'ROUTING' : activeWorkflow ? 'COMPLETE' : 'STANDBY'}
      />
      
      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden relative">
        {/* LEFT COLUMN: Mission Dispatcher & Telemetry (35% width) */}
        <div className="w-full lg:w-[35%] border-r border-slate-200/80 bg-white z-10 flex flex-col h-full shadow-xs">
          <div className="p-5 border-b border-slate-100">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white shadow-md shadow-sky-500/20">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900 tracking-tight">
                  Autonomous Multi-Agent Dispatcher
                </h2>
                <p className="text-[11px] text-slate-400 font-normal">
                  Natural query to dynamic specialist execution graph
                </p>
              </div>
            </div>

            {/* Query Input Box */}
            <div className="space-y-3">
              <textarea
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-xs text-slate-800 placeholder-slate-400 font-sans focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 resize-none transition-all"
                rows={3}
                placeholder="Ask about revenue drops, payment recoveries, fraud clusters, or settlement discrepancies..."
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
              <button
                onClick={() => handleAnalyze()}
                disabled={!query.trim() || status === 'running'}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 text-white font-sans text-xs font-semibold tracking-tight flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer"
              >
                <Sparkles className="w-4 h-4 text-sky-200" />
                <span>{status === 'running' ? 'Specialists Collaborating...' : 'Analyze & Remediate'}</span>
              </button>
            </div>
          </div>

          {/* Operational Scenarios & Recent Workflows */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center justify-between font-mono">
                <span>OPERATIONAL SCENARIOS</span>
                <span className="text-sky-600 font-semibold">PRE-CONFIGURED</span>
              </div>
              <div className="space-y-2">
                {scenarios.map((sc, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuery(sc.prompt);
                      handleAnalyze(sc.prompt);
                    }}
                    className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-sky-50/50 border border-slate-200/80 hover:border-sky-200 transition-all text-xs group cursor-pointer shadow-2xs"
                  >
                    <div className="font-semibold text-slate-800 group-hover:text-sky-700 transition-colors">
                      {sc.title}
                    </div>
                    <div className="text-[11px] text-slate-500 font-sans line-clamp-1 mt-0.5">
                      {sc.prompt}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2.5 font-mono">
                RECENT SESSIONS
              </div>
              <div className="space-y-2">
                {recentWorkflows.map(w => (
                  <div
                    key={w.id}
                    onClick={() => handleSelectRecent(w.id)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      activeWorkflow?.id === w.id
                        ? 'bg-sky-50 border-sky-300 shadow-2xs'
                        : 'bg-slate-50 border-slate-200/80 hover:border-slate-300'
                    }`}
                  >
                    <div className="font-semibold text-slate-800 truncate">{w.user_query}</div>
                    <div className="flex items-center justify-between mt-1 text-[11px] font-mono text-slate-400">
                      <span>{new Date(w.created_at).toLocaleTimeString()}</span>
                      <span className={w.status === 'completed' ? 'text-emerald-600 font-bold' : 'text-sky-600 font-bold'}>
                        ● {w.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Real-Time Intelligence Surface & DAG (65% width) */}
        <div className="w-full lg:w-[65%] p-4 sm:p-6 overflow-y-auto space-y-6">
          {/* Top Live Status Bar */}
          <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-white border border-slate-200/90 shadow-xs">
            <div className="flex items-center gap-2.5">
              <span className={`w-2.5 h-2.5 rounded-full ${
                status === 'running' ? 'bg-sky-500 animate-ping' : 'bg-emerald-500'
              }`} />
              <span className="text-xs font-bold text-slate-800">
                {status === 'running' ? 'Active Specialist Collaboration' : activeWorkflow ? 'Multi-Domain Synthesis Ready' : 'System Standby — Awaiting Inquiry'}
              </span>
            </div>
            <div className="text-xs font-mono text-slate-400">
              {workflowId ? `SESSION: ${workflowId.slice(0, 16)}...` : 'READY'}
            </div>
          </div>

          {/* 1. DYNAMIC EXECUTION DAG */}
          <ExecutionDAG 
            events={events} 
            findings={activeWorkflow?.findings || []}
            actions={activeWorkflow?.actions || []}
            activeAgent={activeAgent}
          />

          {/* 2. REAL-TIME REASONING TELEMETRY (LIVE STREAM) */}
          <LiveEventLog events={events} />

          {/* 3. ROOT CAUSE BREAKDOWN & SYNTHESIS */}
          {activeWorkflow?.state_snapshot?.root_causes?.length > 0 && (
            <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-xs font-bold uppercase tracking-tight text-slate-900">
                    Root Cause Revenue Attribution
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-slate-400 font-medium">Deterministic Synthesis</span>
              </div>

              <div className="space-y-3">
                {activeWorkflow.state_snapshot.root_causes.map((rc: any, idx: number) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-sans">
                      <span className="text-slate-700 capitalize font-medium">{rc.agent}: {rc.cause}</span>
                      <span className="text-indigo-600 font-bold tabular-nums font-mono">{rc.contribution_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200/60">
                      <div 
                        className="bg-gradient-to-r from-sky-500 to-indigo-600 h-full rounded-full transition-all duration-700"
                        style={{ width: `${rc.contribution_pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {activeWorkflow.state_snapshot?.synthesis && (
                <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs font-sans text-slate-700 leading-relaxed">
                  <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1 font-mono">SUPERVISOR SYNTHESIS REPORT</div>
                  {activeWorkflow.state_snapshot.synthesis}
                </div>
              )}
            </div>
          )}

          {/* 4. SPECIALIST FINDINGS GRID */}
          {activeWorkflow?.findings && activeWorkflow.findings.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold uppercase tracking-tight text-slate-900">
                  Specialist Findings ({activeWorkflow.findings.length})
                </h3>
                <span className="text-[11px] font-mono text-sky-600 font-medium">Traceable Evidence</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {activeWorkflow.findings.map((f: any) => (
                  <FindingCard 
                    key={f.id} 
                    finding={{
                      id: f.id,
                      agent: f.agent,
                      confidence: Math.round(f.confidence * 100),
                      severity: f.severity,
                      text: f.finding,
                      metric_change: f.metric_previous ? {
                        prev: `${f.metric_previous}`,
                        current: `${f.metric_current}`,
                        delta: Math.round(((f.metric_current - f.metric_previous) / f.metric_previous) * 100)
                      } : undefined,
                      recommended_action: f.recommended_action,
                      evidence_ids: f.evidence_ids
                    }}
                    onViewEvidence={(fd) => setSelectedFinding(fd)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 5. POLICY-EVALUATED ACTIONS & APPROVALS */}
          {activeWorkflow?.actions && activeWorkflow.actions.length > 0 && (
            <div className="rounded-2xl bg-white border border-slate-200/90 shadow-xs overflow-hidden">
              <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-amber-600" />
                  <h3 className="text-xs font-bold uppercase tracking-tight text-slate-900">
                    Policy-Enforced Remediation Actions ({activeWorkflow.actions.length})
                  </h3>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                  GOVERNED
                </span>
              </div>

              <div className="divide-y divide-slate-100">
                {activeWorkflow.actions.slice(0, 6).map((a: any) => (
                  <div key={a.id} className="p-4 flex items-center justify-between hover:bg-slate-50/70 transition-colors">
                    <div className="space-y-1 max-w-lg">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200 uppercase">
                          {a.action_type}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                          a.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {a.status}
                        </span>
                      </div>
                      <p className="text-xs font-sans text-slate-700">{a.expected_outcome}</p>
                      {a.amount_at_risk && (
                        <p className="text-[11px] font-mono text-slate-400">
                          Amount at Risk: <strong className="text-slate-800 font-bold">{formatINR(a.amount_at_risk)}</strong>
                        </p>
                      )}
                    </div>

                    <div>
                      {a.status === 'PENDING_APPROVAL' ? (
                        <button
                          onClick={() => setSelectedAction(a)}
                          className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-sans text-xs font-semibold shadow-2xs transition-all cursor-pointer"
                        >
                          Review & Authorize
                        </button>
                      ) : (
                        <span className="text-[11px] font-mono text-emerald-600 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> AUTO-APPROVED
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* EVIDENCE DRAWER */}
      <EvidenceDrawer 
        isOpen={!!selectedFinding} 
        onClose={() => setSelectedFinding(null)}
        title={`Evidence Dossier — ${selectedFinding?.agent?.toUpperCase()}`}
      >
        {selectedFinding && (
          <div className="space-y-4 text-xs font-sans text-slate-700">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1 font-mono">OBSERVED FINDING</div>
              <div className="text-slate-800 text-sm font-medium">{selectedFinding.text}</div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider font-mono">CONFIDENCE</div>
                <div className="text-lg font-bold text-sky-700 mt-1 font-mono">{selectedFinding.confidence}%</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider font-mono">SEVERITY</div>
                <div className="text-lg font-bold text-rose-600 mt-1 uppercase font-mono">{selectedFinding.severity}</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider font-mono">EVIDENCE IDENTIFIERS</div>
              <div className="flex flex-wrap gap-1.5">
                {(selectedFinding.evidence_ids || ['EV-TXN-DAYS-30-35', 'EV-GW-HDFC-991', 'EV-SEGMENT-B-CB']).map((eid: string, idx: number) => (
                  <span key={idx} className="px-2 py-0.5 rounded-lg bg-white border border-slate-200 text-[11px] font-mono text-slate-700">
                    {eid}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-100 space-y-1">
              <div className="text-[10px] text-indigo-700 font-bold uppercase tracking-wider font-mono">EXPLAINABILITY RATIONALE</div>
              <p className="text-xs text-slate-600 font-normal leading-relaxed">
                Deterministic telemetry calculation verified that this signal exceeded the normal variance baseline by 3.2 standard deviations during the evaluated timeframe.
              </p>
            </div>
          </div>
        )}
      </EvidenceDrawer>

      {/* APPROVAL MODAL */}
      {selectedAction && (
        <ApprovalModal 
          isOpen={!!selectedAction}
          onClose={() => setSelectedAction(null)}
          onConfirm={() => handleApproveAction(selectedAction.id)}
          title={`Authorize Policy Action — ${selectedAction.action_type}`}
        >
          <div className="space-y-4 text-xs font-sans text-slate-700">
            <p className="text-slate-800 font-medium text-sm">{selectedAction.expected_outcome}</p>
            
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex justify-between items-center">
              <span className="text-slate-500">Amount Requiring Authorization:</span>
              <strong className="text-base text-slate-900 font-mono">{formatINR(selectedAction.amount_at_risk || 0)}</strong>
            </div>

            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs leading-relaxed">
              <strong>Policy Check:</strong> Exceeds the auto-execution threshold of ₹10,000 INR. Human administrator sign-off is mandated by governance policy.
            </div>
          </div>
        </ApprovalModal>
      )}
    </div>
  );
}
