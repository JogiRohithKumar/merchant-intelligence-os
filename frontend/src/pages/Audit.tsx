import React, { useEffect, useState } from 'react';
import TopNav from '../components/layout/TopNav';
import { FileSearch, Filter, ChevronRight, Layers, Shield, RefreshCw, TrendingUp, Brain, ShieldCheck, CheckCircle2, AlertTriangle, Key } from 'lucide-react';
import EvidenceDrawer from '../components/ui/EvidenceDrawer';
import api from '../services/api';

export default function Audit() {
  const [events, setEvents] = useState<any[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<any | null>(null);
  const [agentFilter, setAgentFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any>(null);

  const fetchEvents = () => {
    setLoading(true);
    api.get('/v1/audit?limit=50')
      .then(res => { 
        if (res.data) setEvents(res.data); 
      })
      .catch(() => null)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await api.get('/v1/audit/verify');
      setVerificationResult(res.data);
    } catch (err) {
      setVerificationResult({ is_valid: false, message: 'Failed to complete cryptographic verification probe.' });
    } finally {
      setVerifying(false);
    }
  };

  const filtered = agentFilter === 'ALL' 
    ? events 
    : events.filter(e => (e.agent || '').toUpperCase() === agentFilter);

  const getAgentBadge = (agent?: string) => {
    switch ((agent || '').toLowerCase()) {
      case 'finance': return 'text-sky-700 border-sky-200 bg-sky-50';
      case 'risk': return 'text-rose-700 border-rose-200 bg-rose-50';
      case 'growth': return 'text-emerald-700 border-emerald-200 bg-emerald-50';
      case 'recovery': return 'text-amber-700 border-amber-200 bg-amber-50';
      default: return 'text-indigo-700 border-indigo-200 bg-indigo-50';
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800 font-sans">
      <TopNav pageTitle="Cryptographic Audit Trail & Forensic Lineage" />
      <div className="p-4 sm:p-6 flex-1 overflow-y-auto space-y-6 max-w-7xl mx-auto w-full">

        {/* Cryptographic Hash Chain Banner */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 sm:p-6 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white shadow-md shadow-sky-500/20">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-slate-900">
                    SHA-256 Tamper-Evident Merkle Hash Chain
                  </h2>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    IMMUTABLE
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Every supervisor decision, specialist finding, and action execution is linked by a cryptographic predecessor hash.
                </p>
              </div>
            </div>

            <button
              onClick={handleVerifyChain}
              disabled={verifying}
              className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
              <span>{verifying ? 'Verifying Hashes...' : 'Verify Cryptographic Integrity'}</span>
            </button>
          </div>

          {/* Verification Result Banner */}
          {verificationResult && (
            <div className={`mt-4 p-3.5 rounded-xl border flex items-center justify-between text-xs font-mono ${
              verificationResult.is_valid
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}>
              <div className="flex items-center gap-2">
                {verificationResult.is_valid ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>
                  {verificationResult.is_valid 
                    ? `Integrity Verified: ${verificationResult.total_events} consecutive events validated without tampering.` 
                    : verificationResult.message}
                </span>
              </div>
              <span className="text-[10px] font-bold">
                {verificationResult.is_valid ? 'STATUS: INTACT' : 'COMPROMISED'}
              </span>
            </div>
          )}
        </div>

        {/* Filter bar */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-xs text-xs font-mono">
          <div className="flex flex-wrap items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
            <span className="text-slate-500 font-sans font-medium mr-1">Specialist:</span>
            {['ALL', 'SUPERVISOR', 'FINANCE', 'RISK', 'RECOVERY', 'GROWTH'].map(f => (
              <button
                key={f}
                onClick={() => setAgentFilter(f)}
                className={`px-3 py-1 rounded-xl border transition-all cursor-pointer ${
                  agentFilter === f 
                    ? 'bg-sky-600 text-white border-sky-600 font-bold shadow-2xs' 
                    : 'bg-slate-100 text-slate-600 border-slate-200/60 hover:bg-slate-200/70'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          <span className="text-[11px] text-slate-400 font-sans font-medium">
            Showing {filtered.length} of {events.length} Forensic Records
          </span>
        </div>

        {/* Audit Log Timeline */}
        <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden shadow-xs">
          <div className="divide-y divide-slate-100">
            {loading ? (
              <div className="py-12 text-center text-slate-400 text-xs">
                <RefreshCw className="w-4 h-4 animate-spin text-sky-600 inline-block mr-2" />
                <span>Loading forensic trail...</span>
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-xs">
                No audit events recorded under this filter.
              </div>
            ) : (
              filtered.map((item: any) => (
                <div 
                  key={item.id}
                  onClick={() => setSelectedEvent(item)}
                  className="p-4 flex items-center justify-between text-xs hover:bg-slate-50/70 cursor-pointer transition-colors group"
                >
                  <div className="flex items-center gap-3.5 flex-1 min-w-0">
                    <span className="text-slate-400 font-mono text-[11px] tabular-nums shrink-0">
                      {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : '—'}
                    </span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] uppercase font-bold border font-mono shrink-0 ${getAgentBadge(item.agent)}`}>
                      {item.agent || 'SYSTEM'}
                    </span>
                    <span className="font-semibold text-slate-900 font-mono shrink-0">{item.action}</span>
                    <span className="text-slate-500 font-sans truncate hidden md:inline max-w-md">
                      {item.input_summary || (item.execution_result ? JSON.stringify(item.execution_result) : 'Execution recorded')}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 ml-4">
                    {item.event_hash && (
                      <span className="hidden sm:inline-block font-mono text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {item.event_hash.slice(0, 8)}...
                      </span>
                    )}
                    <span className="text-slate-400 font-mono text-[11px]">{item.latency_ms || 35}ms</span>
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 transition-colors" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Audit Lineage Drawer */}
      <EvidenceDrawer
        isOpen={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={`Forensic Audit Lineage — ${selectedEvent?.id?.slice(0, 12)}...`}
      >
        {selectedEvent && (
          <div className="space-y-4 text-xs font-sans text-slate-700">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">OPERATION IDENTITY</div>
              <div className="flex justify-between">
                <span className="text-slate-500">Agent:</span>
                <strong className="text-sky-700 uppercase font-mono">{selectedEvent.agent}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Action:</span>
                <strong className="text-slate-900 font-mono">{selectedEvent.action}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Timestamp:</span>
                <span className="text-slate-600 font-mono">{selectedEvent.timestamp ? new Date(selectedEvent.timestamp).toLocaleString() : '—'}</span>
              </div>
            </div>

            {/* Hashes */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                <Key className="w-3.5 h-3.5 text-sky-600" />
                <span>CRYPTOGRAPHIC HASH PROOF</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">Current Event Hash:</span>
                <div className="bg-white p-2 rounded-lg border border-slate-200 font-mono text-[10px] text-sky-700 break-all mt-0.5">
                  {selectedEvent.event_hash || '0000000000000000000000000000000000000000000000000000000000000000'}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400">Previous Event Hash (Predecessor):</span>
                <div className="bg-white p-2 rounded-lg border border-slate-200 font-mono text-[10px] text-slate-600 break-all mt-0.5">
                  {selectedEvent.prev_event_hash || '0000000000000000000000000000000000000000000000000000000000000000'}
                </div>
              </div>
            </div>

            {/* Execution Result */}
            {selectedEvent.execution_result && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">EXECUTION RESULT</div>
                <pre className="bg-white p-2.5 rounded-lg border border-slate-200 text-[11px] font-mono text-slate-700 overflow-x-auto">
                  {JSON.stringify(selectedEvent.execution_result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </EvidenceDrawer>
    </div>
  );
}
