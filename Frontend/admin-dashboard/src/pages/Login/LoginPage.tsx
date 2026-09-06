import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Shield, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { login, getMe } from '../../services/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const { setToken, setUser } = useAuthStore();
  const [email, setEmail] = useState('admin@urbansense.in');
  const [password, setPassword] = useState('password123');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !password) { setError('Please enter email and password.'); return; }
    setLoading(true);
    setError('');
    try {
      const tokens = await login({ email, password });
      setToken(tokens.access_token);
      const me = await getMe();
      if (me.role !== 'ADMIN' && me.role !== 'AUTHORITY') {
        setError('Access denied. Admin or Authority role required.');
        setLoading(false);
        return;
      }
      setUser(me);
      navigate('/dashboard');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const msg = axiosErr?.response?.data?.detail;
      if (msg) {
        setError(msg);
      } else if (axiosErr?.message?.includes('Network Error') || !axiosErr?.response) {
        setError('Cannot connect to backend server at ' + (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') + '. Make sure the FastAPI service is running or enable mock mode in .env.');
      } else {
        setError('Login failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      {/* Background orbs */}
      <div className="login-bg-orb" style={{ width: 400, height: 400, background: 'rgba(59,130,246,0.07)', top: -100, left: -100 }} />
      <div className="login-bg-orb" style={{ width: 300, height: 300, background: 'rgba(139,92,246,0.06)', bottom: -80, right: -80 }} />

      <div className="login-card fade-in">
        <div className="login-logo">
          <div className="login-logo-icon">
            <Shield size={26} color="#fff" />
          </div>
          <h1>AI UrbanSense</h1>
          <p>Urban Intelligence Admin Dashboard</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-danger">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <div className="form-input-icon">
              <input
                id="email"
                type="email"
                className="form-input"
                placeholder="admin@urbansense.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                type={showPw ? 'text' : 'password'}
                className="form-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                style={{ paddingRight: 42 }}
              />
              <button
                type="button"
                onClick={() => setShowPw((p) => !p)}
                style={{
                  position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', color: 'var(--clr-text-muted)', padding: 4,
                }}
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-ghost btn-sm" style={{ padding: 0, border: 'none', color: 'var(--clr-accent)' }}>
              Forgot password?
            </button>
          </div>

          <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ justifyContent: 'center', marginTop: 4 }}>
            {loading
              ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Signing in...</>
              : 'Sign In to Dashboard'}
          </button>

          <p style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--clr-text-muted)', marginTop: 8 }}>
            Access restricted to ADMIN and AUTHORITY roles
          </p>
        </form>

        <div style={{ marginTop: 24, padding: 14, background: 'var(--clr-bg-elevated)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>
          <strong style={{ color: 'var(--clr-text-secondary)' }}>Demo credentials</strong><br />
          Email: <span style={{ fontFamily: 'var(--font-mono)' }}>admin@urbansense.in</span><br />
          Password: <span style={{ fontFamily: 'var(--font-mono)' }}>password123</span>
        </div>
      </div>
    </div>
  );
}
