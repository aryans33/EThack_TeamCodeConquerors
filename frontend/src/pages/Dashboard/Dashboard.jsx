import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { stockAPI, watchlistAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { TrendingUp, TrendingDown, Star, StarOff, BarChart2, RefreshCw } from 'lucide-react';
import './Dashboard.css';

const TOP_STOCKS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'WIPRO', 'SBIN', 'TATAMOTORS', 'BHARTIARTL', 'HINDUNILVR'];

const fmt = (n, dec = 2) => n != null ? Number(n).toFixed(dec) : '—';
const fmtK = (n) => { if (!n) return '—'; if (n >= 1e5) return `₹${(n / 1e5).toFixed(1)}L Cr`; if (n >= 1e3) return `₹${(n / 1e3).toFixed(1)}K Cr`; return `₹${n} Cr`; };

export default function Dashboard() {
    const [stocks, setStocks] = useState([]);
    const [watchlist, setWatchlist] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const { user } = useAuth();
    const navigate = useNavigate();

    const fetchData = async () => {
        try {
            const res = await stockAPI.getNseTop(10);
            setStocks(res.data.data || []);
        } catch { }
        try {
            const wl = await watchlistAPI.get();
            setWatchlist((wl.data.watchlist || []).map((w) => w.symbol));
        } catch { }
        setLoading(false); setRefreshing(false);
    };

    useEffect(() => { fetchData(); }, []);

    const toggleWatch = async (symbol) => {
        try {
            if (watchlist.includes(symbol)) {
                await watchlistAPI.remove(symbol);
                setWatchlist((p) => p.filter((s) => s !== symbol));
            } else {
                await watchlistAPI.add(symbol);
                setWatchlist((p) => [...p, symbol]);
            }
        } catch { }
    };

    if (loading) return (
        <div className="loading-container">
            <div className="spinner spinner-lg" />
            <p>Loading market data…</p>
        </div>
    );

    const gainers = stocks.filter((s) => (s.change_percent ?? 0) >= 0).slice(0, 3);
    const losers = stocks.filter((s) => (s.change_percent ?? 0) < 0).slice(0, 3);

    return (
        <div className="dashboard fade-in">
            {/* Header */}
            <div className="dashboard-header">
                <div>
                    <h1>Good {getGreeting()}, {user?.name?.split(' ')[0] || 'Investor'} 👋</h1>
                    <p className="dashboard-sub">Here's your market overview for today</p>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => { setRefreshing(true); fetchData(); }}>
                    <RefreshCw size={14} className={refreshing ? 'spin-icon' : ''} /> Refresh
                </button>
            </div>

            {/* Movers */}
            <div className="movers-row">
                <div className="movers-card card">
                    <div className="card-header">
                        <span className="flex items-center gap-8"><TrendingUp size={16} style={{ color: 'var(--profit)' }} /> Top Gainers</span>
                    </div>
                    <div className="card-body">
                        {gainers.map((s) => <MoverRow key={s.symbol} stock={s} navigate={navigate} />)}
                    </div>
                </div>
                <div className="movers-card card">
                    <div className="card-header">
                        <span className="flex items-center gap-8"><TrendingDown size={16} style={{ color: 'var(--loss)' }} /> Top Losers</span>
                    </div>
                    <div className="card-body">
                        {losers.map((s) => <MoverRow key={s.symbol} stock={s} navigate={navigate} />)}
                    </div>
                </div>
            </div>

            {/* Market Table */}
            <div className="card" style={{ marginTop: 20 }}>
                <div className="card-header">
                    <span className="flex items-center gap-8"><BarChart2 size={16} /> Nifty 50 — Top Stocks</span>
                    <span className="badge badge-info">{stocks.length} Stocks</span>
                </div>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Company</th>
                                <th style={{ textAlign: 'right' }}>Price (₹)</th>
                                <th style={{ textAlign: 'right' }}>Change %</th>
                                <th style={{ textAlign: 'right' }}>P/E</th>
                                <th style={{ textAlign: 'right' }}>Mkt Cap</th>
                                <th style={{ textAlign: 'center' }}>Watch</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stocks.map((s) => {
                                const chg = s.change_percent ?? 0;
                                const watched = watchlist.includes(s.symbol);
                                return (
                                    <tr key={s.symbol} className="table-row-click" onClick={() => navigate(`/stock/${s.symbol}`)}>
                                        <td><span className="stock-symbol-badge">{s.symbol}</span></td>
                                        <td style={{ color: 'var(--text-secondary)', maxWidth: 180 }}>{s.company_name}</td>
                                        <td style={{ textAlign: 'right' }} className="mono">₹{fmt(s.current_price)}</td>
                                        <td style={{ textAlign: 'right' }}>
                                            <span className={chg >= 0 ? 'change-positive' : 'change-negative'}>
                                                {chg >= 0 ? '+' : ''}{fmt(chg)}%
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{s.pe_ratio ? fmt(s.pe_ratio, 1) : '—'}</td>
                                        <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{fmtK(s.market_cap_cr)}</td>
                                        <td style={{ textAlign: 'center' }} onClick={(e) => { e.stopPropagation(); toggleWatch(s.symbol); }}>
                                            <button className={`watch-btn ${watched ? 'watched' : ''}`}>
                                                {watched ? <Star size={14} fill="currentColor" /> : <StarOff size={14} />}
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function MoverRow({ stock, navigate }) {
    const chg = stock.change_percent ?? 0;
    return (
        <div className="mover-row" onClick={() => navigate(`/stock/${stock.symbol}`)}>
            <div>
                <div className="mover-symbol">{stock.symbol}</div>
                <div className="mover-company">{stock.company_name}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
                <div className="mono" style={{ fontSize: '0.9rem' }}>₹{Number(stock.current_price ?? 0).toFixed(2)}</div>
                <div className={chg >= 0 ? 'change-positive' : 'change-negative'} style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                    {chg >= 0 ? '+' : ''}{Number(chg).toFixed(2)}%
                </div>
            </div>
        </div>
    );
}

function getGreeting() {
    const h = new Date().getHours();
    if (h < 12) return 'morning';
    if (h < 17) return 'afternoon';
    return 'evening';
}
