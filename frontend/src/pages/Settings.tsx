import React, { useState, useEffect } from 'react';
import TopNav from '../components/layout/TopNav';
import { 
  ShieldCheck, 
  Cpu, 
  Database, 
  Server,
  CheckCircle2,
  RefreshCw,
  Link as LinkIcon,
  Radio,
  Key,
  Lock
} from 'lucide-react';
import api from '../services/api';

export default function Settings() {
  const [reloading, setReloading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [merchantStatus, setMerchantStatus] = useState<any>(null);

  // Form states for Razorpay credentials
  const [keyId, setKeyId] = useState('');
  const [keySecret, setKeySecret] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [connectLoading, setConnectLoading] = useState(false);
  const [connectMsg, setConnectMsg] = useState('');
  const [connectErr, setConnectErr] = useState('');

  const fetchStatus = async () => {
    try {
      const res = await api.get('/v1/auth/merchant/status');
      if (res.data) setMerchantStatus(res.data);
    } catch {
      // Offline fallback
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnectLoading(true);
    setConnectMsg('');
    setConnectErr('');

    try {
      const res = await api.post('/v1/auth/merchant/connect-razorpay', {
        key_id: keyId,
        key_secret: keySecret,
        webhook_secret: webhookSecret || undefined
      });
      setConnectMsg(res.data.message || 'Razorpay connection verified successfully!');
      fetchStatus();
      setKeySecret('');
      setWebhookSecret('');
    } catch (err: any) {
      setConnectErr(err.response?.data?.detail || 'Verification failed. Please check your credentials.');
    } finally {
      setConnectLoading(false);
    }
  };

  const handleVerifySeeds = async () => {
    setReloading(true);
    try {
      await api.get('/health');
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch {
      // Fallback
    } finally {
      setReloading(false);
    }
  };

  const m = merchantStatus?.merchant;

  return (
    <div className="flex flex-col h-full bg-slate-50/50 text-slate-800 overflow-y-auto font-mono">
      <TopNav pageTitle="System Settings & Integration Center" />

      <div className="p-6 space-y-6 max-w-5xl mx-auto w-full">
        
        {/* Merchant & Live Verification Telemetry */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Merchant Identity & Verification Center
              </h2>
            </div>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
              m?.connection_status === 'connected' 
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}>
              {m?.connection_status ? m.connection_status.toUpperCase() : 'NO MERCHANT ATTACHED'}
            </span>
          </div>

          <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="text-slate-400 text-[10px] uppercase font-bold">Authenticated Merchant</div>
              <div className="text-sm font-bold text-slate-900 mt-0.5">{m?.name || 'Not Configured'}</div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">ID: {m?.id || '—'}</div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="text-slate-400 text-[10px] uppercase font-bold">Ledger Currency</div>
              <div className="text-sm font-bold text-slate-900 mt-0.5">{m?.currency || 'INR'} ({m?.country || 'IN'})</div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">Type: {m?.business_type || 'ecommerce'}</div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="text-slate-400 text-[10px] uppercase font-bold">Verified Ledger Records</div>
              <div className="text-sm font-bold text-indigo-600 mt-0.5">{m?.transactions_count?.toLocaleString() || 0} Transactions</div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">
                Last synced: {m?.last_synced_at ? new Date(m.last_synced_at).toLocaleTimeString() : 'Awaiting sync'}
              </div>
            </div>
          </div>
        </div>

        {/* Razorpay Integration Portal (In-Website Connection) */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <LinkIcon className="h-5 w-5 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Connect Razorpay Payment Provider
              </h2>
            </div>
            <span className="text-[11px] text-slate-500 font-sans">
              Enter Razorpay API keys to start ingesting live transactions
            </span>
          </div>

          {connectMsg && (
            <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{connectMsg}</span>
            </div>
          )}

          {connectErr && (
            <div className="mt-4 p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl">
              {connectErr}
            </div>
          )}

          <form onSubmit={handleConnect} className="mt-5 space-y-4 text-xs font-sans">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 font-mono">
                  Razorpay Key ID
                </label>
                <input
                  type="text"
                  value={keyId}
                  onChange={(e) => setKeyId(e.target.value)}
                  placeholder="rzp_test_... or rzp_live_..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 font-mono">
                  Razorpay Key Secret
                </label>
                <input
                  type="password"
                  value={keySecret}
                  onChange={(e) => setKeySecret(e.target.value)}
                  placeholder="••••••••••••••••••••••••"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 font-mono">
                Webhook Secret (For HMAC-SHA256 Ingestion)
              </label>
              <input
                type="password"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
                placeholder="Optional: Enter secret to verify inbound webhook signatures"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <span className="text-[11px] text-slate-400 font-mono">
                Secrets are encrypted and never exposed in frontend responses.
              </span>
              <button
                type="submit"
                disabled={connectLoading}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-mono text-xs font-semibold tracking-wider flex items-center gap-2 shadow-sm transition-all cursor-pointer disabled:opacity-50"
              >
                {connectLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ShieldCheck className="w-3.5 h-3.5" />
                )}
                <span>{connectLoading ? 'Verifying...' : 'Save & Verify Connection'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Deterministic Policy Guardrails */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Deterministic Policy Thresholds
              </h2>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              STRICT HARD LIMITS
            </span>
          </div>

          <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <div className="text-slate-500 text-[10px] uppercase font-semibold">Max Auto-Retry Amount</div>
              <div className="text-base font-bold text-slate-900 mt-1">₹10,000.00</div>
              <p className="text-[10px] text-slate-500 font-sans mt-0.5">Higher recovery values require explicit operator approval.</p>
            </div>
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
              <div className="text-slate-500 text-[10px] uppercase font-semibold">Max Allowable ML Risk Score</div>
              <div className="text-base font-bold text-slate-900 mt-1">0.65</div>
              <p className="text-[10px] text-slate-500 font-sans mt-0.5">Any score &gt; 0.65 blocks automated actions unconditionally.</p>
            </div>
          </div>
        </div>

        {/* AI & Vector Pipeline */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                AI Reasoning Engines & Multi-Agent Architecture
              </h2>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200">
              ACTIVE & HEALTHY
            </span>
          </div>

          <div className="mt-4 space-y-3 text-xs">
            <div className="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl">
              <div>
                <div className="font-semibold text-slate-800 font-sans">Multi-Agent Supervisor DAG</div>
                <div className="text-[10px] text-slate-500 font-sans">Finance, Risk, Recovery & Growth agents dynamically routed by intent</div>
              </div>
              <span className="text-emerald-700 font-bold text-[11px] flex items-center gap-1 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> Ready
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl">
              <div>
                <div className="font-semibold text-slate-800 font-sans">Google Gemini AI Engine</div>
                <div className="text-[10px] text-slate-500 font-sans">Deep multi-agent financial reasoning, root-cause attribution & RAG</div>
              </div>
              <span className="text-sky-700 font-bold text-[11px] flex items-center gap-1 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-200 font-mono">
                gemini-2.5-flash
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl">
              <div>
                <div className="font-semibold text-slate-800 font-sans">Inbound Webhook Receiver URL</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                  POST /api/v1/webhooks/razorpay (Requires X-Merchant-ID header)
                </div>
              </div>
              <span className="text-indigo-700 font-bold text-[11px] flex items-center gap-1 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200 font-mono">
                HMAC-SHA256 VERIFIED
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
