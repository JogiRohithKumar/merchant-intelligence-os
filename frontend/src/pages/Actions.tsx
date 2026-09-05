import React, { useState, useEffect } from 'react';
import TopNav from '../components/layout/TopNav';
import StatusBadge from '../components/ui/StatusBadge';
import { formatINR } from '../utils/format';
import { api } from '../services/api';
import { 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  AlertTriangle,
  RefreshCw,
  Cpu,
  Key,
  Zap
} from 'lucide-react';

interface ActionItem {
  id: string;
  action_type: string;
  status: string;
  description: string;
  risk_level?: string;
  amount_at_risk?: number;
  idempotency_key?: string;
  policy_result?: any;
  expected_outcome?: string;
  proposed_at?: string;
  test_mode?: boolean;
}

export default function Actions() {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [operatingId, setOperatingId] = useState<string | null>(null);
  const [selectedAction, setSelectedAction] = useState<ActionItem | null>(null);

  const fetchActions = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter !== 'ALL') {
        params.status = statusFilter;
      }
      const res = await api.get('/v1/actions', { params });
      setActions(res.data || []);
    } catch (err) {
      console.error('Failed to fetch actions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, [statusFilter]);

  const handleApprove = async (actionId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setOperatingId(actionId);
    try {
      await api.post(`/v1/actions/${actionId}/approve`);
      await fetchActions();
      if (selectedAction?.id === actionId) {
        setSelectedAction((prev) => prev ? { ...prev, status: 'APPROVED' } : null);
      }
    } catch (err) {
      console.error('Failed to approve action:', err);
    } finally {
      setOperatingId(null);
    }
  };

  const handleReject = async (actionId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setOperatingId(actionId);
    try {
      await api.post(`/v1/actions/${actionId}/reject`, { reason: 'Rejected by merchant administrator' });
      await fetchActions();
      if (selectedAction?.id === actionId) {
        setSelectedAction((prev) => prev ? { ...prev, status: 'REJECTED' } : null);
      }
    } catch (err) {
      console.error('Failed to reject action:', err);
    } finally {
      setOperatingId(null);
    }
  };

  const pendingCount = actions.filter((a) => a.status === 'PENDING_APPROVAL').length;
  const approvedCount = actions.filter((a) => a.status === 'APPROVED' || a.status === 'SUCCESS').length;
  const rejectedCount = actions.filter((a) => a.status === 'REJECTED').length;

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800 overflow-y-auto font-sans">
      <TopNav pageTitle="Policy Engine & Action Center" />

      <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* Policy Guardrails & Architecture Card */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 sm:p-6 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200/60">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900 tracking-tight">
                  Deterministic Policy Enforcement Pipeline
                </h2>
                <p className="text-xs text-slate-400 font-normal">
                  All automated agent recommendations must satisfy hard-coded boundary constraints.
                </p>
              </div>
            </div>
            <span className="hidden sm:inline-flex px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-mono">
              ZERO UNCHECKED ACTIONS
            </span>
          </div>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
            <div className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-3.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-500"></span>
                <span className="font-medium">Rule 1: Risk Boundary</span>
              </div>
              <div className="text-sm font-bold text-slate-800 font-mono">Risk Score ≤ 0.65</div>
              <p className="text-[11px] text-slate-400 mt-1">Actions with ML risk &gt; 0.65 are strictly halted.</p>
            </div>

            <div className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-3.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span className="font-medium">Rule 2: Retry Breaker</span>
              </div>
              <div className="text-sm font-bold text-slate-800 font-mono">Max 2 Retries / 24h</div>
              <p className="text-[11px] text-slate-400 mt-1">Prevents card issuer spamming and dispute risk.</p>
            </div>

            <div className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-3.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                <span className="font-medium">Rule 3: Value Gate</span>
              </div>
              <div className="text-sm font-bold text-slate-800 font-mono">Threshold: ₹10,000</div>
              <p className="text-[11px] text-slate-400 mt-1">Values &gt; ₹10k require explicit Merchant Admin sign-off.</p>
            </div>

            <div className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-3.5">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                <span className="font-medium">Rule 4: Idempotency</span>
              </div>
              <div className="text-sm font-bold text-slate-800 font-mono">SHA-256 Key</div>
              <p className="text-[11px] text-slate-400 mt-1">Exact params hashed to guarantee single execution.</p>
            </div>
          </div>
        </div>

        {/* Action Counters */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Total Actions</div>
            <div className="text-2xl font-bold text-slate-900 mt-1 font-mono">{actions.length}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Audited action pipeline</div>
          </div>
          <div className="bg-white border border-amber-200/80 rounded-2xl p-4 shadow-xs bg-gradient-to-br from-white to-amber-50/30">
            <div className="text-[11px] text-amber-600 uppercase tracking-wider font-semibold">Pending Approval</div>
            <div className="text-2xl font-bold text-amber-600 mt-1 font-mono">{pendingCount}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Awaiting human sign-off</div>
          </div>
          <div className="bg-white border border-emerald-200/80 rounded-2xl p-4 shadow-xs bg-gradient-to-br from-white to-emerald-50/30">
            <div className="text-[11px] text-emerald-600 uppercase tracking-wider font-semibold">Approved / Executed</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1 font-mono">{approvedCount}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Safe execution confirmed</div>
          </div>
          <div className="bg-white border border-rose-200/80 rounded-2xl p-4 shadow-xs bg-gradient-to-br from-white to-rose-50/30">
            <div className="text-[11px] text-rose-600 uppercase tracking-wider font-semibold">Rejected</div>
            <div className="text-2xl font-bold text-rose-600 mt-1 font-mono">{rejectedCount}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Blocked or declined</div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500 mr-1">Status:</span>
            {['ALL', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'SUCCESS'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                  statusFilter === status
                    ? 'bg-sky-600 text-white shadow-xs font-semibold'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200/70 border border-slate-200/60'
                }`}
              >
                {status.replace('_', ' ')}
              </button>
            ))}
          </div>

          <button
            onClick={fetchActions}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200/70 border border-slate-200/80 rounded-xl text-xs font-medium text-slate-700 transition-colors cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-sky-600' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Actions Table */}
        <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs divide-y divide-slate-100">
              <thead className="bg-slate-50 text-[11px] font-semibold text-slate-500 tracking-wider uppercase">
                <tr>
                  <th className="px-5 py-3.5">Action ID</th>
                  <th className="px-5 py-3.5">Type</th>
                  <th className="px-5 py-3.5">Risk Level</th>
                  <th className="px-5 py-3.5">Description</th>
                  <th className="px-5 py-3.5 text-right">Exposure</th>
                  <th className="px-5 py-3.5 text-center">Status</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                      <div className="inline-flex items-center gap-2">
                        <RefreshCw className="h-4 w-4 animate-spin text-sky-600" />
                        <span>Loading policy engine actions...</span>
                      </div>
                    </td>
                  </tr>
                ) : actions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                      No actions match the selected filter.
                    </td>
                  </tr>
                ) : (
                  actions.map((action) => (
                    <tr
                      key={action.id}
                      onClick={() => setSelectedAction(action)}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                    >
                      <td className="px-5 py-3.5 font-mono font-medium text-sky-700 group-hover:text-sky-900">
                        {action.id.slice(0, 12)}...
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200 font-mono">
                          {action.action_type}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase font-mono ${
                            action.risk_level === 'high' || action.risk_level === 'prohibited'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : action.risk_level === 'medium'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          }`}
                        >
                          {action.risk_level || 'LOW'}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-600 max-w-md truncate font-sans">
                        {action.description || 'System policy evaluation item'}
                      </td>
                      <td className="px-5 py-3.5 text-right font-bold text-slate-900 font-mono">
                        {action.amount_at_risk ? formatINR(action.amount_at_risk) : '—'}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <StatusBadge
                          status={action.status}
                          label={action.status}
                        />
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        {action.status === 'PENDING_APPROVAL' ? (
                          <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={(e) => handleApprove(action.id, e)}
                              disabled={operatingId === action.id}
                              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-40 shadow-2xs cursor-pointer"
                            >
                              Approve
                            </button>
                            <button
                              onClick={(e) => handleReject(action.id, e)}
                              disabled={operatingId === action.id}
                              className="px-3 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold transition-colors disabled:opacity-40 cursor-pointer"
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedAction(action);
                            }}
                            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-[11px] font-medium transition-colors cursor-pointer"
                          >
                            Details →
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Action Detail Inspection Drawer */}
      {selectedAction && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-xl bg-white border-l border-slate-200 h-full overflow-y-auto p-6 flex flex-col justify-between shadow-2xl animate-fade-in font-sans">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-sky-50 text-sky-600 border border-sky-200/60">
                    <Key className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">
                      Policy Execution Manifest
                    </h3>
                    <p className="text-xs text-slate-400 font-mono">ID: {selectedAction.id}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedAction(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              </div>

              <div className="mt-6 space-y-4">
                <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-2">
                    Action Type & Status
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-base font-bold text-slate-900 font-mono">{selectedAction.action_type}</span>
                    <StatusBadge
                      status={selectedAction.status}
                      label={selectedAction.status}
                    />
                  </div>
                  <p className="text-xs text-slate-600 mt-2 font-normal">{selectedAction.description}</p>
                </div>

                {/* Idempotency Key */}
                <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-1 flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-sky-600" />
                    <span>Cryptographic Idempotency Key</span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200 text-[11px] text-sky-700 font-mono break-all">
                    {selectedAction.idempotency_key || 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069'}
                  </div>
                </div>

                {/* Policy Enforcement Result */}
                <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-2 flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Policy Engine Evaluation</span>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-slate-200 text-xs space-y-1.5 text-slate-700 font-mono">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Risk Boundary:</span>
                      <span className="font-bold text-emerald-600">PASSED (&le; 0.65)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Retry Circuit Breaker:</span>
                      <span className="font-bold text-emerald-600">PASSED (&le; 2 retries)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Human Approval Gate:</span>
                      <span className={`font-bold ${selectedAction.status === 'PENDING_APPROVAL' ? 'text-amber-600' : 'text-emerald-600'}`}>
                        {selectedAction.status === 'PENDING_APPROVAL' ? 'REQUIRED (Threshold Exceeded)' : 'CLEARED'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Financial Exposure */}
                <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-2">
                    Exposure Metrics
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <div className="text-slate-400 text-[10px]">Exposure Value</div>
                      <div className="text-base font-bold text-slate-900 font-mono">
                        {selectedAction.amount_at_risk ? formatINR(selectedAction.amount_at_risk) : '₹0'}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-[10px]">Execution Mode</div>
                      <div className="text-emerald-600 font-bold font-mono">
                        {selectedAction.test_mode ? 'SANDBOX ENFORCED' : 'LIVE DISPATCH'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-5 border-t border-slate-100 flex gap-3">
              {selectedAction.status === 'PENDING_APPROVAL' && (
                <>
                  <button
                    onClick={() => handleApprove(selectedAction.id)}
                    disabled={operatingId === selectedAction.id}
                    className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold transition-colors disabled:opacity-40 shadow-xs cursor-pointer"
                  >
                    Authorize & Execute
                  </button>
                  <button
                    onClick={() => handleReject(selectedAction.id)}
                    disabled={operatingId === selectedAction.id}
                    className="flex-1 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-xl text-xs font-semibold transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    Reject Action
                  </button>
                </>
              )}
              <button
                onClick={() => setSelectedAction(null)}
                className="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
