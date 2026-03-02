import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { stockAPI, watchlistAPI } from '../../services/api';
import {
    Line, Bar
} from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale, LinearScale, PointElement, LineElement,
    BarElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Star, StarOff, TrendingUp, TrendingDown, Brain, Shield, FileText, ChevronLeft } from 'lucide-react';
import './Stock.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler);

const fmt = (n, d = 2) => n != null ? Number(n).toFixed(d) : '—';

const CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#0d1321', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 } },
    scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#475569', maxTicksLimit: 8 } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#475569' } },
    },
};

export default function StockDetail() {
    const { symbol } = useParams();
    const navigate = useNavigate();
    const [stock, setStock] = useState(null);
    const [history, setHistory] = useState([]);
    const [tab, setTab] = useState('overview');
    const [period, setPeriod] = useState('1y');
    const [loading, setLoading] = useState(true);
    const [aiLoading, setAiLoading] = useState(false);
    const [watched, setWatched] = useState(false);
    const [aiData, setAiData] = useState({ summary: null, thesis: null, risk: null });

    useEffect(() => {
        setLoading(true);
        Promise.all([
            stockAPI.getInfo(symbol),
            stockAPI.getHistory(symbol, period),
        ]).then(([infoRes, histRes]) => {
            setStock(infoRes.data.data);
            setHistory(histRes.data.data || []);
        }).catch(() => { }).finally(() => setLoading(false));
    }, [symbol, period]);

    const loadAI = async (type) => {
        if (aiData[type]) return;
        setAiLoading(true);
        try {
            let res;
            if (type === 'summary') res = await stockAPI.getSummary(symbol);
            if (type === 'thesis') res = await stockAPI.getThesis(symbol);
            if (type === 'risk') res = await stockAPI.getRisk(symbol);
            setAiData((prev) => ({ ...prev, [type]: res.data }));
        } catch (e) {
            setAiData((prev) => ({ ...prev, [type]: { error: 'Failed to load. Please ensure you are logged in.' } }));
        }
        setAiLoading(false);
    };

    const toggleWatch = async () => {
        try {
            if (watched) { await watchlistAPI.remove(symbol); setWatched(false); }
            else { await watchlistAPI.add(symbol); setWatched(true); }
        } catch { }
    };

    if (loading) return <div className="loading-container"><div className="spinner spinner-lg" /><p>Loading {symbol}…</p></div>;
    if (!stock) return <div className="loading-container"><p>Stock not found: {symbol}</p></div>;

    const chg = stock.change_percent ?? 0;
    const pos = chg >= 0;

    // Chart data
    const labels = history.map((h) => h.date?.slice(5) ?? '');
    const prices = history.map((h) => h.close);
    const chartData = {
        labels,
        datasets: [{
            label: symbol,
            data: prices,
            fill: true,
            borderColor: pos ? '#00d4aa' : '#ff4d6d',
            backgroundColor: pos ? 'rgba(0,212,170,0.06)' : 'rgba(255,77,109,0.06)',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.3,
        }],
    };

    const volumes = history.map((h) => h.volume);
    const volData = {
        labels,
        datasets: [{
            label: 'Volume',
            data: volumes,
            backgroundColor: 'rgba(59,130,246,0.4)',
            borderRadius: 2,
        }],
    };

    return (
        <div className="stock-detail fade-in">
            {/* Back */}
            <button className="btn btn-ghost btn-sm back-btn" onClick={() => navigate(-1)}>
                <ChevronLeft size={16} /> Back
            </button>

            {/* Stock Header */}
            <div className="stock-header card">
                <div className="stock-header-left">
                    <div className="stock-logo">{symbol.slice(0, 2)}</div>
                    <div>
                        <h1 className="stock-name">{stock.company_name}</h1>
                        <div className="stock-meta">
                            <span className="stock-symbol-badge">{symbol}</span>
                            <span className="badge badge-muted">{stock.sector || 'NSE'}</span>
                        </div>
                    </div>
                </div>
                <div className="stock-header-right">
                    <div className="stock-price">₹{fmt(stock.current_price)}</div>
                    <div className={pos ? 'change-positive stock-change' : 'change-negative stock-change'}>
                        {pos ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                        {pos ? '+' : ''}{fmt(chg)}%
                    </div>
                    <button className={`btn btn-ghost watch-toggle ${watched ? 'watched' : ''}`} onClick={toggleWatch}>
                        {watched ? <Star size={16} fill="currentColor" /> : <StarOff size={16} />}
                        {watched ? 'Watching' : 'Watch'}
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs">
                {['overview', 'charts', 'financials', 'ai'].map((t) => (
                    <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`} onClick={() => { setTab(t); if (t === 'ai') loadAI('summary'); }}>
                        {t === 'ai' ? '🤖 AI Analysis' : t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                ))}
            </div>

            {/* OVERVIEW TAB */}
            {tab === 'overview' && (
                <div className="metric-grid fade-in">
                    {[
                        { label: 'Market Cap', value: stock.market_cap_cr ? `₹${(stock.market_cap_cr / 1e5).toFixed(2)}L Cr` : '—' },
                        { label: 'P/E Ratio', value: fmt(stock.pe_ratio, 1) },
                        { label: 'P/B Ratio', value: fmt(stock.pb_ratio, 2) },
                        { label: 'ROE', value: stock.roe ? `${fmt(stock.roe * 100, 1)}%` : '—' },
                        { label: 'ROCE', value: stock.roce ? `${fmt(stock.roce * 100, 1)}%` : '—' },
                        { label: 'Gross Margin', value: stock.gross_margin ? `${fmt(stock.gross_margin * 100, 1)}%` : '—' },
                        { label: 'Net Margin', value: stock.profit_margin ? `${fmt(stock.profit_margin * 100, 1)}%` : '—' },
                        { label: 'D/E Ratio', value: fmt(stock.debt_to_equity, 2) },
                        { label: 'Current Ratio', value: fmt(stock.current_ratio, 2) },
                        { label: 'Beta', value: fmt(stock.beta, 2) },
                        { label: '52W High', value: stock.fifty_two_week_high ? `₹${fmt(stock.fifty_two_week_high)}` : '—' },
                        { label: '52W Low', value: stock.fifty_two_week_low ? `₹${fmt(stock.fifty_two_week_low)}` : '—' },
                        { label: 'EPS', value: stock.eps ? `₹${fmt(stock.eps)}` : '—' },
                        { label: 'Dividend %', value: stock.dividend_yield ? `${fmt(stock.dividend_yield * 100, 2)}%` : '—' },
                        { label: 'Analyst', value: stock.recommendation || '—' },
                        { label: 'Exchange', value: stock.exchange || 'NSE' },
                    ].map(({ label, value }) => (
                        <div className="metric-card" key={label}>
                            <div className="metric-label">{label}</div>
                            <div className="metric-value">{value}</div>
                        </div>
                    ))}
                </div>
            )}

            {/* CHARTS TAB */}
            {tab === 'charts' && (
                <div className="fade-in">
                    <div className="period-selector">
                        {['1mo', '3mo', '6mo', '1y', '2y', '5y'].map((p) => (
                            <button key={p} className={`btn btn-sm ${period === p ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setPeriod(p)}>
                                {p}
                            </button>
                        ))}
                    </div>
                    <div className="card" style={{ marginBottom: 16 }}>
                        <div className="card-header"><span>{symbol} — Price Chart</span></div>
                        <div className="card-body" style={{ height: 320 }}>
                            <Line data={chartData} options={CHART_OPTIONS} />
                        </div>
                    </div>
                    <div className="card">
                        <div className="card-header"><span>Volume</span></div>
                        <div className="card-body" style={{ height: 180 }}>
                            <Bar data={volData} options={{ ...CHART_OPTIONS, plugins: { ...CHART_OPTIONS.plugins, legend: { display: false } } }} />
                        </div>
                    </div>
                </div>
            )}

            {/* FINANCIALS TAB */}
            {tab === 'financials' && <FinancialsTab symbol={symbol} />}

            {/* AI TAB */}
            {tab === 'ai' && (
                <div className="ai-tab fade-in">
                    <div className="ai-actions">
                        {[
                            { key: 'summary', icon: FileText, label: 'Financial Summary' },
                            { key: 'thesis', icon: TrendingUp, label: 'Investment Thesis' },
                            { key: 'risk', icon: Shield, label: 'Risk Assessment' },
                        ].map(({ key, icon: Icon, label }) => (
                            <button key={key} className="btn btn-ghost ai-btn" onClick={() => loadAI(key)}>
                                <Icon size={14} /> {label}
                            </button>
                        ))}
                    </div>

                    {aiLoading && <div className="loading-container" style={{ minHeight: 200 }}><div className="spinner spinner-lg" /><p>Gemini is analyzing…</p></div>}

                    {Object.entries(aiData).map(([key, data]) => {
                        if (!data) return null;
                        const text = data.thesis ?? data.summary ?? data.assessment ?? data.error ?? JSON.stringify(data);
                        return (
                            <div key={key} className="card ai-result fade-in">
                                <div className="card-header">
                                    <span className="flex items-center gap-8"><Brain size={16} style={{ color: 'var(--accent)' }} /> {key.charAt(0).toUpperCase() + key.slice(1)}</span>
                                    <span className="badge badge-info">Gemini 2.0</span>
                                </div>
                                <div className="card-body ai-result-body">{text}</div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

function FinancialsTab({ symbol }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        stockAPI.getFinancials(symbol).then((r) => setData(r.data.data)).catch(() => { }).finally(() => setLoading(false));
    }, [symbol]);

    if (loading) return <div className="loading-container"><div className="spinner spinner-lg" /></div>;
    if (!data) return <div className="empty-state"><p>Financial data not available</p></div>;

    const income = data.income_statement?.slice(0, 4) || [];

    return (
        <div className="fade-in">
            <div className="card">
                <div className="card-header"><span>Income Statement (Annual, ₹ Cr)</span></div>
                <div className="table-container">
                    <table>
                        <thead><tr>
                            <th>Metric</th>
                            {income.map((r) => <th key={r.date} style={{ textAlign: 'right' }}>{r.date?.slice(0, 4)}</th>)}
                        </tr></thead>
                        <tbody>
                            {[
                                { key: 'revenue', label: 'Revenue' },
                                { key: 'gross_profit', label: 'Gross Profit' },
                                { key: 'ebit', label: 'EBIT' },
                                { key: 'net_income', label: 'Net Income' },
                                { key: 'eps', label: 'EPS' },
                            ].map(({ key, label }) => (
                                <tr key={key}>
                                    <td style={{ color: 'var(--text-secondary)' }}>{label}</td>
                                    {income.map((r) => <td key={r.date} style={{ textAlign: 'right' }} className="mono">{r[key] != null ? Number(r[key]).toFixed(1) : '—'}</td>)}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
