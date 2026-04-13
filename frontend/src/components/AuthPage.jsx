import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useSettings } from '@/context/SettingsContext';
import { LogoPreview } from '@/components/SettingsModal';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

const AuthPage = () => {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, signup } = useAuth();
  const { settings } = useSettings();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        if (!name.trim()) { setError('Name is required'); setLoading(false); return; }
        if (password.length < 6) { setError('Password must be at least 6 characters'); setLoading(false); return; }
        await signup(name.trim(), email, password);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Something went wrong';
      setError(msg);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: settings.mainBg }}>
      <div className="w-full max-w-sm">
        {/* Logo & Title */}
        <div className="flex flex-col items-center mb-8">
          <LogoPreview settings={settings} size={56} className="mb-4" />
          <h1 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            {mode === 'login' ? `Sign in to ${settings.appName || 'Open WebUI'}` : `Create an Account`}
          </h1>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4" data-testid="auth-form">
          {mode === 'signup' && (
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>Name</label>
              <input
                data-testid="auth-name-input"
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Your name"
                className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-colors"
                style={{ backgroundColor: settings.inputBg, color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                required
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>Email</label>
            <input
              data-testid="auth-email-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="email@example.com"
              className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-colors"
              style={{ backgroundColor: settings.inputBg, color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>Password</label>
            <div className="relative">
              <input
                data-testid="auth-password-input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl px-4 py-3 pr-11 text-sm outline-none transition-colors"
                style={{ backgroundColor: settings.inputBg, color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                required
              />
              <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 p-1" style={{ color: 'var(--text-muted)' }}>
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="rounded-lg px-4 py-2.5 text-sm text-red-400" style={{ backgroundColor: 'rgba(239,68,68,0.1)' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            data-testid="auth-submit-button"
            className="w-full rounded-xl px-4 py-3 text-sm font-semibold transition-colors flex items-center justify-center gap-2"
            style={{ backgroundColor: settings.accentColor, color: isLightBg(settings.accentColor) ? '#000' : '#fff', opacity: loading ? 0.7 : 1 }}
          >
            {loading && <Loader2 size={16} className="animate-spin" />}
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        {/* Toggle mode */}
        <p className="text-center text-sm mt-6" style={{ color: 'var(--text-muted)' }}>
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button
            onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(''); }}
            className="font-medium underline transition-colors"
            style={{ color: settings.accentColor }}
            data-testid="auth-toggle-mode"
          >
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  );
};

function isLightBg(hex) {
  if (!hex) return false;
  const c = hex.replace('#', '');
  const r = parseInt(c.substr(0, 2), 16);
  const g = parseInt(c.substr(2, 2), 16);
  const b = parseInt(c.substr(4, 2), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 128;
}

export default AuthPage;
