import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Activity, Eye, EyeOff, TrendingUp, BarChart2, Brain } from 'lucide-react';
import './Auth.css';

export default function Login() {
    const [form, setForm] = useState({ email: '', password: '' });
    const [showPwd, setShowPwd] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(''); setLoading(true);
        try {
            await login(form.email, form.password);
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.message || 'Login failed. Check your credentials.');
        } finally { setLoading(false); }
    };

    return (
        <div className="auth-layout">
            {/* Left Panel */}
            <div className="auth-left">
                <div className="auth-brand">
                    <div className="auth-logo"><Activity size={28} /></div>
                    <h1>FinAnalysis <span className="accent">AI</span></h1>
                    <p>AI-powered financial intelligence for Indian markets</p>
                </div>
                <div className="auth-features">
                    {[
                        { icon: Brain, title: 'AutoGen Agents', desc: '14 specialized AI agents for deep analysis' },
                        { icon: TrendingUp, title: 'Live Market Data', desc: 'Real-time NSE/BSE data via yfinance' },
                        { icon: BarChart2, title: 'Investment Thesis', desc: 'Gemini-powered bull/bear case generation' },
                    ].map(({ icon: Icon, title, desc }) => (
                        <div className="auth-feature" key={title}>
                            <div className="auth-feature-icon"><Icon size={18} /></div>
                            <div>
                                <div className="auth-feature-title">{title}</div>
                                <div className="auth-feature-desc">{desc}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right Panel */}
            <div className="auth-right">
                <div className="auth-form-header">
                    <h2>Welcome back</h2>
                    <p>Sign in to your account</p>
                </div>

                {error && <div className="auth-error">{error}</div>}

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label className="input-label">Email</label>
                        <input className="input" type="email" placeholder="you@example.com"
                            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                    </div>

                    <div className="input-group">
                        <label className="input-label">Password</label>
                        <div className="input-with-icon">
                            <input className="input" type={showPwd ? 'text' : 'password'} placeholder="••••••••"
                                value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                            <button type="button" className="input-eye" onClick={() => setShowPwd(!showPwd)}>
                                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>
                    </div>

                    <button className="btn btn-primary btn-lg" type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
                        {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Signing in…</> : 'Sign In'}
                    </button>
                </form>

                <p className="auth-switch">
                    Don't have an account? <Link to="/register">Create one</Link>
                </p>
            </div>
        </div>
    );
}
