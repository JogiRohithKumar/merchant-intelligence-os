import React, { useState, useEffect } from 'react';
import TopNav from '../components/layout/TopNav';
import { formatINR } from '../utils/format';
import StatusBadge from '../components/ui/StatusBadge';
import { api } from '../services/api';
import { 
  RefreshCw, 
  Filter, 
  Search, 
  X,
  ShieldAlert,
  CheckCircle2,
  CreditCard
} from 'lucide-react';

interface TransactionItem {
  id: string;
  amount: number;
  status: string;
  gateway: string;
  payment_method: string;
  currency: string;
  risk_score: number;
  created_at: string;
}

interface TransactionDetail {
  id: string;
  amount: number;
  status: string;
  gateway?: string;
  payment_method?: string;
  currency?: string;
  risk_score?: number;
  created_at?: string;
  payment_attempts: Array<{ id: string; status: string; gateway: string }>;
  risk_events: Array<{ id: string; event_type: string; severity: string }>;
  settlement_items: Array<{ id: string; amount: number }>;
}

export default function Transactions() {
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const pageSize = 25;
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTx, setSelectedTx] = useState<TransactionDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params: any = {
        skip: page * pageSize,
        limit: pageSize,
      };
      if (statusFilter !== 'ALL') {
        params.status = statusFilter;
      }
      const res = await api.get('/v1/transactions', { params });
      setTransactions(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Failed to fetch transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [page, statusFilter]);

  const inspectTransaction = async (txId: string) => {
    setLoadingDetail(true);
    try {
      const res = await api.get(`/v1/transactions/${txId}`);
      setSelectedTx(res.data);
    } catch (err) {
      console.error('Failed to load transaction details:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const filteredItems = transactions.filter(t => 
    t.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.gateway.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.payment_method.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800 overflow-y-auto font-sans">
      <TopNav pageTitle="Transaction Operations Ledger" />

      <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* Header Summary & Live Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Total Filtered Volume</div>
            <div className="text-xl font-bold text-slate-900 mt-1 font-mono">{total.toLocaleString()} txns</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{total > 0 ? `${total.toLocaleString()} in ledger` : 'Zero transactions recorded'}</div>
          </div>
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Active Filter</div>
            <div className="text-xl font-bold text-sky-700 mt-1 uppercase font-mono">{statusFilter}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Status partition</div>
          </div>
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Gateway Pipeline</div>
            <div className="text-sm font-bold text-emerald-700 mt-2 font-mono">Razorpay / PayU / Cashfree</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Automated multi-switch</div>
          </div>
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Audit Lineage</div>
            <div className="text-sm font-bold text-indigo-700 mt-2 font-mono">Deterministic SHA-256</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Tamper-evident proof</div>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
          <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
            <div className="relative w-full max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Filter by Transaction ID, Gateway, or Method..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(0);
                }}
                className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-sky-500 cursor-pointer"
              >
                <option value="ALL">All Statuses</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
                <option value="disputed">Disputed</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchTransactions}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-xl text-xs font-medium transition-colors cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-sky-600' : ''}`} />
              <span>Refresh</span>
            </button>
            <div className="text-xs text-slate-400 font-mono">
              Page {page + 1} of {Math.max(1, Math.ceil(total / pageSize))}
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg text-xs text-slate-700 disabled:opacity-40 cursor-pointer"
              >
                Prev
              </button>
              <button
                onClick={() => setPage((p) => ((p + 1) * pageSize < total ? p + 1 : p))}
                disabled={(page + 1) * pageSize >= total}
                className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg text-xs text-slate-700 disabled:opacity-40 cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Ledger Table */}
        <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs divide-y divide-slate-100">
              <thead className="bg-slate-50 text-[11px] font-semibold text-slate-500 tracking-wider uppercase">
                <tr>
                  <th className="px-5 py-3.5">Timestamp</th>
                  <th className="px-5 py-3.5">Transaction ID</th>
                  <th className="px-5 py-3.5 text-right">Amount</th>
                  <th className="px-5 py-3.5 text-center">Status</th>
                  <th className="px-5 py-3.5">Gateway / Method</th>
                  <th className="px-5 py-3.5">Risk Score</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                      <div className="inline-flex items-center gap-2">
                        <RefreshCw className="h-4 w-4 animate-spin text-sky-600" />
                        <span>Querying deterministic ledger partition...</span>
                      </div>
                    </td>
                  </tr>
                ) : filteredItems.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                      No transactions found matching the current criteria.
                    </td>
                  </tr>
                ) : (
                  filteredItems.map((tx) => (
                    <tr
                      key={tx.id}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                      onClick={() => inspectTransaction(tx.id)}
                    >
                      <td className="px-5 py-3.5 text-slate-400 whitespace-nowrap text-[11px] font-mono">
                        {new Date(tx.created_at).toLocaleString('en-IN', {
                          month: 'short',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                          hour12: false,
                        })}
                      </td>
                      <td className="px-5 py-3.5 font-medium font-mono text-sky-700 group-hover:text-sky-900">
                        {tx.id.slice(0, 14)}...
                      </td>
                      <td className="px-5 py-3.5 text-right font-bold text-slate-900 font-mono">
                        {formatINR(tx.amount)}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <StatusBadge
                          status={tx.status}
                          label={tx.status.toUpperCase()}
                        />
                      </td>
                      <td className="px-5 py-3.5 text-slate-700 font-sans">
                        <div className="flex items-center gap-1.5">
                          <CreditCard className="h-3.5 w-3.5 text-slate-400" />
                          <span className="capitalize">{tx.gateway}</span>
                          <span className="text-slate-300">/</span>
                          <span className="uppercase text-[10px] text-slate-500 font-semibold font-mono">{tx.payment_method}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-mono">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                            tx.risk_score > 0.65 ? 'bg-rose-50 text-rose-700 border-rose-200' :
                            tx.risk_score > 0.3 ? 'bg-amber-50 text-amber-700 border-amber-200' :
                            'bg-emerald-50 text-emerald-700 border-emerald-200'
                          }`}>
                            {tx.risk_score.toFixed(2)}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            inspectTransaction(tx.id);
                          }}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-[11px] font-medium transition-colors cursor-pointer"
                        >
                          Dossier →
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Forensic Transaction Detail Drawer */}
      {selectedTx && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-xl bg-white border-l border-slate-200 h-full overflow-y-auto p-6 flex flex-col justify-between shadow-2xl animate-fade-in font-sans">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-sky-50 text-sky-600 border border-sky-200/60">
                    <CreditCard className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">
                      Transaction Forensic Dossier
                    </h3>
                    <p className="text-xs text-slate-400 font-mono">ID: {selectedTx.id}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedTx(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {loadingDetail ? (
                <div className="py-20 text-center text-slate-400 text-xs">
                  <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-sky-600" />
                  <span>Loading full transaction context...</span>
                </div>
              ) : (
                <div className="mt-6 space-y-4">
                  {/* Financial Overview Card */}
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-2">
                      Transaction Identity
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="text-xl font-bold text-slate-900 font-mono">
                        {formatINR(selectedTx.amount)}
                      </div>
                      <StatusBadge
                        status={selectedTx.status}
                        label={selectedTx.status.toUpperCase()}
                      />
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-400">Gateway:</span>
                        <span className="ml-1 text-slate-700 font-semibold capitalize">{selectedTx.gateway}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">Method:</span>
                        <span className="ml-1 text-slate-700 font-semibold uppercase font-mono">{selectedTx.payment_method}</span>
                      </div>
                    </div>
                  </div>

                  {/* Multi-Gateway Switch Attempts */}
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-2 flex items-center justify-between">
                      <span>Gateway Switch Attempts</span>
                      <span className="text-sky-700 text-xs font-mono">
                        {selectedTx.payment_attempts?.length || 0} recorded
                      </span>
                    </div>
                    <div className="space-y-2">
                      {selectedTx.payment_attempts && selectedTx.payment_attempts.length > 0 ? (
                        selectedTx.payment_attempts.map((att: any, idx: number) => (
                          <div
                            key={att.id || idx}
                            className="bg-white border border-slate-200 rounded-lg p-2.5 flex items-center justify-between text-xs"
                          >
                            <div>
                              <div className="text-slate-800 font-semibold capitalize">Gateway: {att.gateway}</div>
                              <div className="text-[10px] text-slate-400 font-mono">Attempt ID: {att.id?.slice(0, 12)}...</div>
                            </div>
                            <StatusBadge
                              status={att.status}
                              label={att.status.toUpperCase()}
                            />
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-slate-400">No multi-gateway attempts logged.</div>
                      )}
                    </div>
                  </div>

                  {/* Risk Events */}
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-2 flex items-center justify-between">
                      <span>Risk Specialist Evaluations</span>
                      <span className="text-amber-700 text-xs font-mono">
                        {selectedTx.risk_events?.length || 0} alerts
                      </span>
                    </div>
                    <div className="space-y-2">
                      {selectedTx.risk_events && selectedTx.risk_events.length > 0 ? (
                        selectedTx.risk_events.map((rev: any, idx: number) => (
                          <div
                            key={rev.id || idx}
                            className="bg-white border border-slate-200 rounded-lg p-2.5 flex items-center justify-between text-xs"
                          >
                            <div className="flex items-center gap-2">
                              <ShieldAlert className="h-4 w-4 text-amber-500" />
                              <div>
                                <div className="text-slate-800 font-medium">{rev.event_type}</div>
                                <div className="text-[10px] text-slate-400 font-mono">Event ID: {rev.id?.slice(0, 12)}...</div>
                              </div>
                            </div>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 uppercase font-mono">
                              {rev.severity}
                            </span>
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-slate-400 flex items-center gap-1.5">
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          <span>No anomalous risk markers flagged for this item.</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Settlement Allocation */}
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-2 flex items-center justify-between">
                      <span>Reconciliation Settlement Link</span>
                      <span className="text-indigo-700 text-xs font-mono">
                        {selectedTx.settlement_items?.length || 0} batch matches
                      </span>
                    </div>
                    <div className="space-y-2">
                      {selectedTx.settlement_items && selectedTx.settlement_items.length > 0 ? (
                        selectedTx.settlement_items.map((s: any, idx: number) => (
                          <div
                            key={s.id || idx}
                            className="bg-white border border-slate-200 rounded-lg p-2.5 flex items-center justify-between text-xs"
                          >
                            <div>
                              <div className="text-slate-800 font-medium font-mono">Batch Item #{s.id?.slice(0, 10)}...</div>
                              <div className="text-[10px] text-slate-400">Reconciled in bank payout</div>
                            </div>
                            <div className="font-bold text-slate-900 font-mono">{formatINR(s.amount)}</div>
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-slate-400">Pending next settlement cycle payout.</div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="pt-5 border-t border-slate-100 flex gap-3">
              <button
                onClick={() => setSelectedTx(null)}
                className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
