import React, { useState } from 'react';
import { Zap, ShieldCheck, UserCheck, AlertCircle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth';
import api from '../services/api';

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [forgotStep, setForgotStep] = useState<'request' | 'reset' | 'done'>('request');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotMsg, setForgotMsg] = useState('');
  const [forgotErr, setForgotErr] = useState('');

  const navigate = useNavigate();
  const setToken = useAuthStore(state => state.setToken);
  const setUser = useAuthStore(state => state.setUser);

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotLoading(true);
    setForgotErr('');
    setForgotMsg('');
    try {
      const res = await api.post('/v1/auth/forgot-password', { email: forgotEmail });
      setForgotMsg(res.data.message || 'Password reset link/token issued.');
      if (res.data.reset_token) {
        setResetToken(res.data.reset_token);
      }
      setForgotStep('reset');
    } catch (err: any) {
      setForgotErr(err.response?.data?.detail || 'Failed to request password reset.');
    } finally {
      setForgotLoading(false);
    }
  };

  const handlePerformReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotLoading(true);
    setForgotErr('');
    setForgotMsg('');
    try {
      const res = await api.post('/v1/auth/reset-password', {
        token: resetToken,
        new_password: newPassword
      });
      setForgotMsg(res.data.message || 'Password successfully updated.');
      setForgotStep('done');
      setPassword('');
    } catch (err: any) {
      setForgotErr(err.response?.data?.detail || 'Failed to reset password. Please check your token.');
    } finally {
      setForgotLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      if (isRegister) {
        // Registration Flow
        const res = await api.post('/v1/auth/register', {
          email,
          password,
          full_name: fullName,
          role: 'operator'
        });
        if (res.data?.access_token) {
          const token = res.data.access_token;
          localStorage.setItem('token', token);
          setToken(token);
          if (res.data.user) {
            setUser(res.data.user);
          }
          if (res.data.user?.onboarding_required) {
            navigate('/onboarding');
          } else {
            navigate('/');
          }
        } else {
          setSuccessMsg('Account created successfully! Please sign in.');
          setIsRegister(false);
        }
      } else {
        // Sign-In Flow
        const res = await api.post('/v1/auth/login', { email, password });
        if (res.data?.access_token) {
          const token = res.data.access_token;
          localStorage.setItem('token', token);
          setToken(token);
          if (res.data.user) {
            setUser(res.data.user);
          }
          if (res.data.user?.onboarding_required) {
            navigate('/onboarding');
          } else {
            navigate('/');
          }
        } else {
          setError('Login failed. Please check your credentials.');
        }
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Authentication service error. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setGoogleLoading(true);
    setError('');
    try {
      // Sandbox/development Google OAuth simulation with genuine fresh user identity
      const devRandomId = Math.random().toString(36).substring(2, 9);
      const googleEmail = email.trim() || `google.founder.${devRandomId}@example.com`;
      const googleName = fullName.trim() || 'New Merchant Founder';
      const mockGoogleToken = `google_oauth2_${Date.now()}_${devRandomId}`;

      const res = await api.post('/v1/auth/firebase-login', {
        id_token: mockGoogleToken,
        email: googleEmail,
        full_name: googleName
      });

      if (res.data?.access_token) {
        const token = res.data.access_token;
        localStorage.setItem('token', token);
        setToken(token);
        if (res.data.user) {
          setUser(res.data.user);
        }
        if (res.data.user?.onboarding_required) {
          navigate('/onboarding');
        } else {
          navigate('/');
        }
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Google authentication failed';
      setError(msg);
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50/20 to-sky-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center text-indigo-600 mb-3">
          <div className="p-3 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-600/20">
            <Zap className="w-8 h-8" />
          </div>
        </div>
        <h2 className="text-center text-2xl font-bold tracking-tight text-slate-900 font-sans">
          Merchant Intelligence OS
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500 font-medium">
          Autonomous Financial Operating System · Release Candidate
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl shadow-slate-200/50 rounded-2xl border border-slate-200/80 sm:px-10">
          
          {/* Tab Selection */}
          <div className="flex border-b border-slate-200 mb-6">
            <button
              onClick={() => { setIsRegister(false); setError(''); }}
              className={`flex-1 pb-3 text-sm font-semibold text-center border-b-2 transition-colors ${
                !isRegister
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-400 hover:text-slate-700'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsRegister(true); setError(''); }}
              className={`flex-1 pb-3 text-sm font-semibold text-center border-b-2 transition-colors ${
                isRegister
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-400 hover:text-slate-700'
              }`}
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded-xl text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-4 bg-emerald-50 border border-emerald-200 text-emerald-700 p-3 rounded-xl text-xs flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            {isRegister && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                  required={isRegister}
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="merchant@example.com"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                required
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Password
                </label>
                {!isRegister && (
                  <button
                    type="button"
                    onClick={() => {
                      setShowForgotPassword(true);
                      setForgotStep('request');
                      setForgotMsg('');
                      setForgotErr('');
                      setForgotEmail(email);
                    }}
                    className="text-[11px] text-indigo-600 hover:text-indigo-800 font-medium transition-colors cursor-pointer"
                  >
                    Forgot Password?
                  </button>
                )}
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                'Processing...'
              ) : isRegister ? (
                <>
                  <span>Create Merchant Account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Social Google Sign-In */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-slate-400 font-semibold tracking-wider">
                  Or authenticate with
                </span>
              </div>
            </div>

            <div className="mt-4">
              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={googleLoading}
                className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 shadow-2xs transition-all cursor-pointer disabled:opacity-50"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                  />
                </svg>
                <span>{googleLoading ? 'Connecting...' : 'Continue with Google'}</span>
              </button>
            </div>
          </div>

          {/* Sandbox & Operational Notice */}
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block"></span>
              DATA MODE: SANDBOX
            </span>
            <span>Razorpay Safe Gate: ACTIVE</span>
          </div>

        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotPassword && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 font-sans">
                {forgotStep === 'done' ? 'Password Reset Complete' : forgotStep === 'reset' ? 'Set New Password' : 'Reset Account Password'}
              </h3>
              <button
                type="button"
                onClick={() => setShowForgotPassword(false)}
                className="text-slate-400 hover:text-slate-600 p-1 text-xs cursor-pointer"
              >
                ✕
              </button>
            </div>

            {forgotErr && (
              <div className="bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded-xl text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
                <span>{forgotErr}</span>
              </div>
            )}

            {forgotMsg && (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 p-3 rounded-xl text-xs flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{forgotMsg}</span>
              </div>
            )}

            {forgotStep === 'request' && (
              <form onSubmit={handleRequestReset} className="space-y-3">
                <p className="text-xs text-slate-600">
                  Enter your registered merchant email. A cryptographic verification token will be generated to safely update your password.
                </p>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Account Email</label>
                  <input
                    type="email"
                    value={forgotEmail}
                    onChange={e => setForgotEmail(e.target.value)}
                    placeholder="merchant@example.com"
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  />
                </div>
                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50 cursor-pointer"
                >
                  {forgotLoading ? 'Issuing Token...' : 'Generate Reset Token'}
                </button>
              </form>
            )}

            {forgotStep === 'reset' && (
              <form onSubmit={handlePerformReset} className="space-y-3">
                <p className="text-xs text-slate-600">
                  Verification token generated. Please enter your new password (minimum 8 characters).
                </p>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Reset Token</label>
                  <input
                    type="text"
                    value={resetToken}
                    onChange={e => setResetToken(e.target.value)}
                    placeholder="Paste your reset token"
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">New Password</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                  />
                </div>
                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50 cursor-pointer"
                >
                  {forgotLoading ? 'Updating Password...' : 'Save New Password'}
                </button>
              </form>
            )}

            {forgotStep === 'done' && (
              <div className="text-center py-3 space-y-3">
                <p className="text-xs text-slate-600">
                  Your credentials have been securely updated. You can now log into your merchant workspace.
                </p>
                <button
                  type="button"
                  onClick={() => { setShowForgotPassword(false); setIsRegister(false); }}
                  className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all cursor-pointer"
                >
                  Proceed to Sign In
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
