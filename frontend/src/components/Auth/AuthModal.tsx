import React, { useState } from 'react';
import { X, Shield, Sparkles, UserPlus, LogIn, LogOut } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: {
    id: string;
    email: string;
    full_name: string;
  } | null;
  onLoginSuccess: (user: { id: string; email: string; full_name: string }, token: string) => void;
  onSignOut: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onLoginSuccess,
  onSignOut,
}) => {
  const [tab, setTab] = useState<'profile' | 'login' | 'register'>(currentUser ? 'profile' : 'login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (!currentUser && tab === 'profile') {
      setTab('login');
    }
  }, [currentUser, tab]);

  if (!isOpen) return null;

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/auth/demo-login', {
        method: 'POST',
      });
      const data = await res.json();
      if (data.status === 'success') {
        localStorage.removeItem('nivo_signed_out');
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('nivo_auth_token', data.token);
        localStorage.setItem('nivo_user', JSON.stringify(data.user));
        onLoginSuccess(data.user, data.token);
        onClose();
      } else {
        setError(data.message || 'Demo login failed');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide email and password.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        localStorage.removeItem('nivo_signed_out');
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('nivo_auth_token', data.token);
        localStorage.setItem('nivo_user', JSON.stringify(data.user));
        onLoginSuccess(data.user, data.token);
        onClose();
      } else {
        setError(data.detail || 'Login failed. Check your credentials.');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !fullName) {
      setError('Please fill in all fields.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
        }),
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        localStorage.removeItem('nivo_signed_out');
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('nivo_auth_token', data.token);
        localStorage.setItem('nivo_user', JSON.stringify(data.user));
        onLoginSuccess(data.user, data.token);
        onClose();
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('nivo_auth_token');
    localStorage.removeItem('nivo_user');
    localStorage.setItem('nivo_signed_out', 'true');
    onSignOut();
    setTab('login');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 text-slate-100">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">Account & Ledger Access</h2>
              <p className="text-[11px] text-slate-400">Multi-tenant privacy & data isolation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className={`grid ${currentUser ? 'grid-cols-3' : 'grid-cols-2'} gap-1 p-1 my-4 rounded-xl bg-slate-950 border border-slate-800 text-xs`}>
          {currentUser && (
            <button
              type="button"
              onClick={() => { setTab('profile'); setError(null); }}
              className={`py-1.5 rounded-lg font-medium transition ${
                tab === 'profile'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Account
            </button>
          )}
          <button
            type="button"
            onClick={() => { setTab('login'); setError(null); }}
            className={`py-1.5 rounded-lg font-medium transition ${
              tab === 'login'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('register'); setError(null); }}
            className={`py-1.5 rounded-lg font-medium transition ${
              tab === 'register'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            + Register
          </button>
        </div>

        {error && (
          <div className="mb-4 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
            {error}
          </div>
        )}

        {tab === 'profile' && currentUser && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-sm font-bold text-emerald-400">
                {currentUser.full_name
                  .split(' ')
                  .map((n) => n[0])
                  .join('')
                  .slice(0, 2)
                  .toUpperCase()}
              </div>
              <div className="truncate flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-xs font-semibold text-white">{currentUser.full_name}</p>
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-mono">
                    Active
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 truncate">{currentUser.email}</p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-850/50 border border-slate-800 text-xs space-y-1.5 text-slate-300">
              <p className="font-medium text-slate-200">Ledger Security & Isolation:</p>
              <p className="text-[11px] text-slate-400">
                • Strict multi-tenancy enforced: all queries scoped to your account ID ({currentUser.id}).
              </p>
              <p className="text-[11px] text-slate-400">
                • Transactions, accounts, and chat history are private and isolated.
              </p>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleDemoLogin}
                disabled={loading}
                className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white text-xs font-medium flex items-center justify-center gap-1.5 transition disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Demo (Lokender)</span>
              </button>
              <button
                type="button"
                onClick={handleSignOut}
                data-testid="auth-modal-signout-btn"
                className="py-2 px-3 rounded-xl bg-slate-800 hover:bg-rose-950/40 hover:border-rose-500/30 border border-slate-700 text-slate-300 hover:text-rose-300 text-xs font-medium flex items-center gap-1.5 transition"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        )}

        {tab === 'login' && (
          <form onSubmit={handleLogin} className="space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 mt-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-md shadow-indigo-600/30"
            >
              <LogIn className="w-4 h-4" />
              <span>{loading ? 'Authenticating...' : 'Sign In to Ledger'}</span>
            </button>

            <div className="relative my-3">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-800" />
              </div>
              <div className="relative flex justify-center text-[10px] uppercase">
                <span className="bg-slate-900 px-2 text-slate-500 font-medium">Quick Demo Access</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={loading}
              className="w-full py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-200 hover:text-white text-xs font-medium flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Demo (Lokender)</span>
            </button>
          </form>
        )}

        {tab === 'register' && (
          <form onSubmit={handleRegister} className="space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Priya Sharma"
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="priya@example.com"
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 mt-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-md shadow-indigo-600/30"
            >
              <UserPlus className="w-4 h-4" />
              <span>{loading ? 'Creating Account...' : 'Provision Clean Ledger'}</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
