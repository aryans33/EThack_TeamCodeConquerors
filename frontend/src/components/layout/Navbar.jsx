import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell } from 'lucide-react';
import { stockAPI } from '../../services/api';
import './Navbar.css';

const NIFTY_SYMBOLS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'WIPRO', 'SBIN', 'TATAMOTORS', 'BHARTIARTL'];

export default function Navbar() {
    const [search, setSearch] = useState('');
    const [tickers, setTickers] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        stockAPI.getNseTop(9)
            .then((res) => setTickers(res.data.data || []))
            .catch(() => { });
    }, []);

    const handleSearch = (e) => {
        e.preventDefault();
        if (search.trim()) {
            navigate(`/stock/${search.trim().toUpperCase()}`);
            setSearch('');
        }
    };

    const tickerDisplay = tickers.length > 0 ? [...tickers, ...tickers] : [];

    return (
        <header className="navbar">
            {/* Ticker Strip */}
            {tickerDisplay.length > 0 && (
                <div className="ticker-strip">
                    <div className="ticker-content">
                        {tickerDisplay.map((stock, i) => {
                            const chg = stock.change_percent ?? 0;
                            return (
                                <span key={i} className="ticker-item" onClick={() => navigate(`/stock/${stock.symbol}`)} style={{ cursor: 'pointer' }}>
                                    <span className="ticker-symbol">{stock.symbol}</span>
                                    <span className="ticker-price">₹{stock.current_price?.toFixed(2) ?? '—'}</span>
                                    <span className={chg >= 0 ? 'change-positive' : 'change-negative'}>
                                        {chg >= 0 ? '+' : ''}{chg?.toFixed(2)}%
                                    </span>
                                </span>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Search Bar */}
            <div className="navbar-bar">
                <form className="search-form" onSubmit={handleSearch}>
                    <Search size={16} className="search-icon" />
                    <input
                        className="search-input"
                        placeholder="Search stocks… (e.g. TCS, RELIANCE)"
                        value={search}
                        onChange={(e) => setSearch(e.target.value.toUpperCase())}
                    />
                </form>
                <div className="navbar-actions">
                    <button className="btn btn-icon btn-ghost"><Bell size={18} /></button>
                </div>
            </div>
        </header>
    );
}
