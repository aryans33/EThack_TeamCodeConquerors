import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { watchlistAPI, stockAPI } from '../../services/api';
import { Star, Trash2, TrendingUp, TrendingDown, Plus } from 'lucide-react';

const fmt = (n, d = 2) => n != null ? Number(n).toFixed(d) : '—';

export default function Watchlist() {
    const [watchlist, setWatchlist] = useState([]);
    const [stockData, setStockData] = useState({});
    const [loading, setLoading] = useState(true);
    const [addSymbol, setAddSymbol] = useState('');
    const [adding, setAdding] = useState(false);
    const navigate = useNavigate();

    const fetchWatchlist = async () => {
        try {
            const res = await watchlistAPI.get();
            const items = res.data.watchlist || [];
            setWatchlist(items);
            // Fetch live data for each symbol
            const results = await Promise.allSettled(items.map((w) => stockAPI.getInfo(w.symbol)));
            const dataMap = {};
            results.forEach((r, i) => {
                if (r.status === 'fulfilled') dataMap[items[i].symbol] = r.value.data.data;
            });
            setStockData(dataMap);
        } catch { }
        setLoading(false);
    };

    useEffect(() => { fetchWatchlist(); }, []);

    const handleAdd = async () => {
        if (!addSymbol.trim()) return;
        setAdding(true);
        try {
            await watchlistAPI.add(addSymbol.toUpperCase());
            setAddSymbol('');
            fetchWatchlist();
        } catch { }
        setAdding(false);
    };

    const handleRemove = async (symbol) => {
        try {
            await watchlistAPI.remove(symbol);
            setWatchlist((prev) => prev.filter((w) => w.symbol !== symbol));
        } catch { }
    };

    if (loading) return <div className="loading-container"><div className="spinner spinner-lg" /><p>Loading watchlist…</p></div>;

    return (
        <div className="fade-in">
            <div className="page-title-row">
                <h1 className="flex items-center gap-8"><Star size={22} style={{ color: '#f59e0b' }} /> My Watchlist</h1>
                <p>Track your favorite stocks with live data</p>
            </div>

            {/* Add Stock */}
            <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-body" style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
                    <div className="input-group" style={{ flex: 1, maxWidth: 300, marginBottom: 0 }}>
                        <label className="input-label">Add Stock</label>
                        <input className="input" placeholder="e.g. TCS, INFY, RELIANCE" value={addSymbol}
                            onChange={(e) => setAddSymbol(e.target.value.toUpperCase())}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleAdd(); }}
                        />
                    </div>
                    <button className="btn btn-primary" onClick={handleAdd} disabled={adding || !addSymbol.trim()}>
                        <Plus size={14} /> Add
                    </button>
                </div>
            </div>

            {/* Watchlist Table */}
            {watchlist.length === 0
                ? <div className="empty-state card" style={{ padding: 60 }}>
                    <Star size={40} style={{ color: 'var(--text-muted)', opacity: 0.3 }} />
                    <p>Your watchlist is empty</p>
                    <p style={{ fontSize: '0.8rem' }}>Search for stocks on the Dashboard and click the ★ icon</p>
                </div>
                : <div className="card">
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
                                    <th style={{ textAlign: 'center' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {watchlist.map(({ symbol }) => {
                                    const s = stockData[symbol];
                                    const chg = s?.change_percent ?? 0;
                                    const pos = chg >= 0;
                                    return (
                                        <tr key={symbol} style={{ cursor: 'pointer' }} onClick={() => navigate(`/stock/${symbol}`)}>
                                            <td><span className="stock-symbol-badge">{symbol}</span></td>
                                            <td style={{ color: 'var(--text-secondary)', maxWidth: 200 }}>{s?.company_name ?? '—'}</td>
                                            <td style={{ textAlign: 'right' }} className="mono">₹{s ? fmt(s.current_price) : '—'}</td>
                                            <td style={{ textAlign: 'right' }}>
                                                {s ? (
                                                    <span className={pos ? 'change-positive' : 'change-negative'} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                                        {pos ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                                                        {pos ? '+' : ''}{fmt(chg)}%
                                                    </span>
                                                ) : '—'}
                                            </td>
                                            <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{s?.pe_ratio ? fmt(s.pe_ratio, 1) : '—'}</td>
                                            <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                                                {s?.market_cap_cr ? `₹${(s.market_cap_cr / 1e5).toFixed(1)}L Cr` : '—'}
                                            </td>
                                            <td style={{ textAlign: 'center' }} onClick={(e) => { e.stopPropagation(); handleRemove(symbol); }}>
                                                <button className="btn btn-danger btn-sm btn-icon"><Trash2 size={13} /></button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            }
        </div>
    );
}
