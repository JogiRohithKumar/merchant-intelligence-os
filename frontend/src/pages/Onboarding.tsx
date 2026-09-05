import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, ArrowRight, ShieldCheck, CheckCircle2, Zap, AlertCircle } from 'lucide-react';
import api from '../services/api';
import { useAuthStore } from '../store/auth';

export default function Onboarding() {
  const [step, setStep] = useState<'create' | 'connect' | 'verified'>('create');
  const [businessName, setBusinessName] = useState('');
  const [businessType, setBusinessType] = useState('ecommerce');
  const [currency, setCurrency] = useState('INR');
  const [country, setCountry] = useState('IN');

  const [razorpayKeyId, setRazorpayKeyId] = useState('');
  const [razorpayKeySecret, setRazorpayKeySecret] = useState('');
  const [razorpayWebhookSecret, setRazorpayWebhookSecret] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [merchantData, setMerchantData] = useState<any>(null);

  const navigate = useNavigate();
  const setToken = useAuthStore(state => state.setToken);
  const setUser = useAuthStore(state => state.setUser);
  const user = useAuthStore(state => state.user);

  const handleCreateMerchant = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Endpoint is on auth_router: /api/v1/auth/onboarding/create-merchant
      const res = await api.post('/v1/auth/onboarding/create-merchant', {
        name: businessName,
        business_type: businessType,
        country,
        currency
      });

      if (res.data?.access_token) {
        localStorage.setItem('token', res.data.access_token);
        setToken(res.data.access_token);
      }

      setMerchantData(res.data.merchant);
      // Update store user with newly associated merchant
      if (user) {
        setUser({
          ...user,
          merchant_id: res.data.merchant.id,
          role: 'merchant_admin'
        });
      }
      setStep('connect');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create merchant. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectRazorpay = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Endpoint is on auth_router: /api/v1/auth/merchant/connect-razorpay
      const res = await api.post('/v1/auth/merchant/connect-razorpay', {
        key_id: razorpayKeyId,
        key_secret: razorpayKeySecret,
        webhook_secret: razorpayWebhookSecret || undefined
      });
      setStep('verified');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to verify Razorpay credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50/20 to-sky-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-600/20">
            <Zap className="w-8 h-8" />
          </div>
        </div>
        <h1 className="text-center text-2xl font-bold tracking-tight text-slate-900 font-sans">
          Welcome to Merchant Intelligence OS
        </h1>
        <p className="mt-1 text-center text-xs text-slate-500">
          Setup your dedicated merchant organization and connect live telemetry
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-white py-8 px-6 shadow-xl shadow-slate-200/50 rounded-2xl border border-slate-200/80 sm:px-10">

          {/* Step Indicator */}
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-100 text-xs font-semibold">
            <span className={`flex items-center gap-1.5 ${step === 'create' ? 'text-indigo-600' : 'text-slate-400'}`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 'create' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>1</span>
              Merchant Details
            </span>
            <span className="text-slate-300">→</span>
            <span className={`flex items-center gap-1.5 ${step === 'connect' ? 'text-indigo-600' : 'text-slate-400'}`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 'connect' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>2</span>
              Payment Provider
            </span>
            <span className="text-slate-300">→</span>
            <span className={`flex items-center gap-1.5 ${step === 'verified' ? 'text-emerald-600' : 'text-slate-400'}`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 'verified' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-500'}`}>3</span>
              Verified
            </span>
          </div>

          {error && (
            <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded-xl text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* STEP 1: CREATE MERCHANT */}
          {step === 'create' && (
            <form onSubmit={handleCreateMerchant} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Business / Organization Name
                </label>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="e.g. Acme Retail Pvt Ltd"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Business Type
                  </label>
                  <select
                    value={businessType}
                    onChange={(e) => setBusinessType(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  >
                    <option value="ecommerce">E-Commerce</option>
                    <option value="saas">SaaS / Subscription</option>
                    <option value="marketplace">Marketplace</option>
                    <option value="retail">Retail POS</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Operating Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  >
                    <option value="INR">INR (₹) - Indian Rupee</option>
                    <option value="USD">USD ($) - US Dollar</option>
                    <option value="EUR">EUR (€) - Euro</option>
                  </select>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50 cursor-pointer"
                >
                  {loading ? 'Creating Organization...' : (
                    <>
                      <span>Continue to Payment Setup</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* STEP 2: CONNECT PAYMENT PROVIDER */}
          {step === 'connect' && (
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-mono">Organization</span>
                  <span className="font-bold text-slate-800">{merchantData?.name || businessName}</span>
                </div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                  Not Connected
                </span>
              </div>

              <p className="text-xs text-slate-600">
                Connect your Razorpay account to start receiving real-time transactions and webhooks. Or skip to start with a clean zero-data state.
              </p>

              <form onSubmit={handleConnectRazorpay} className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Razorpay Key ID
                  </label>
                  <input
                    type="text"
                    value={razorpayKeyId}
                    onChange={(e) => setRazorpayKeyId(e.target.value)}
                    placeholder="rzp_test_... or rzp_live_..."
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Razorpay Key Secret
                  </label>
                  <input
                    type="password"
                    value={razorpayKeySecret}
                    onChange={(e) => setRazorpayKeySecret(e.target.value)}
                    placeholder="••••••••••••••••••••"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Webhook Secret (Optional)
                  </label>
                  <input
                    type="password"
                    value={razorpayWebhookSecret}
                    onChange={(e) => setRazorpayWebhookSecret(e.target.value)}
                    placeholder="Optional webhook signing secret"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  />
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => navigate('/')}
                    className="flex-1 py-2.5 px-3 rounded-xl text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors cursor-pointer"
                  >
                    Skip for Now
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-2.5 px-3 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50 cursor-pointer"
                  >
                    {loading ? 'Verifying...' : 'Verify Connection'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* STEP 3: CONNECTION VERIFIED */}
          {step === 'verified' && (
            <div className="text-center space-y-4 py-4">
              <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Razorpay Connection Verified ✓
              </h3>
              <p className="text-xs text-slate-600 max-w-sm mx-auto">
                Your merchant is ready. The system will now ingest webhooks and stream transactions into your private isolated ledger.
              </p>
              <button
                onClick={() => navigate('/')}
                className="w-full py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
              >
                Go to Dashboard
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
