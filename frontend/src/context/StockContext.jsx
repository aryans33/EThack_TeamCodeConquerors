import { createContext, useContext, useState, useCallback } from 'react';
import { stockAPI } from '../services/api';

const StockContext = createContext(null);

export const StockProvider = ({ children }) => {
    const [cache, setCache] = useState({});
    const [watchlist, setWatchlist] = useState([]);

    const getStock = useCallback(async (symbol) => {
        if (cache[symbol] && Date.now() - cache[symbol].ts < 5 * 60 * 1000) {
            return cache[symbol].data;
        }
        const res = await stockAPI.getInfo(symbol);
        const data = res.data.data;
        setCache((prev) => ({ ...prev, [symbol]: { data, ts: Date.now() } }));
        return data;
    }, [cache]);

    const addToWatchlist = useCallback((symbol) => setWatchlist((p) => [...new Set([...p, symbol.toUpperCase()])]), []);
    const removeFromWatchlist = useCallback((symbol) => setWatchlist((p) => p.filter((s) => s !== symbol)), []);

    return (
        <StockContext.Provider value={{ cache, getStock, watchlist, addToWatchlist, removeFromWatchlist }}>
            {children}
        </StockContext.Provider>
    );
};

export const useStock = () => {
    const ctx = useContext(StockContext);
    if (!ctx) throw new Error('useStock must be used within StockProvider');
    return ctx;
};
