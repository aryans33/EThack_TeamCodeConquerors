import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Activity, Eye, EyeOff } from 'lucide-react';

export default function Register() {
    const [form, setForm] = useState({ name: '', email: '', password: '' });
    const [showPwd, setShowPwd] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(''); setLoading(true);
        try {
            await register(form.name, form.email, form.password);
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.message || 'Registration failed. Please try again.');
        } finally { setLoading(false); }
    };

    return (
        <div className="auth-layout">
            <div className="auth-left">
                <div className="auth-brand">
                    <div className="auth-logo"><Activity size={28} /></div>
                    <h1>FinAnalysis <span className="accent">AI</span></h1>
                    <p>Join thousands of investors using AI for smarter decisions</p>
                </div>
                <div className="auth-tagline">
                    <p className="auth-quote">"The stock market is a device for transferring money from the impatient to the patient."</p>
                    <p className="auth-quote-author">— Warren Buffett</p>
                </div>
            </div>

            <div className="auth-right">
                <div className="auth-form-header">
                    <h2>Create account</h2>
                    <p>Start your AI-powered market journey</p>
                </div>

                {error && <div className="auth-error">{error}</div>}

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label className="input-label">Full Name</label>
                        <input className="input" type="text" placeholder="Aryan Shah"
                            value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                    </div>
                    <div className="input-group">
                        <label className="input-label">Email</label>
                        <input className="input" type="email" placeholder="you@example.com"
                            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                    </div>
                    <div className="input-group">
                        <label className="input-label">Password</label>
                        <div className="input-with-icon">
                            <input className="input" type={showPwd ? 'text' : 'password'} placeholder="Min. 8 characters"
                                value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} minLength={8} required />
                            <button type="button" className="input-eye" onClick={() => setShowPwd(!showPwd)}>
                                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>
                    </div>

                    <button className="btn btn-primary btn-lg" type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
                        {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Creating account…</> : 'Create Account'}
                    </button>
                </form>

                <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
            </div>
        </div>
    );
}
