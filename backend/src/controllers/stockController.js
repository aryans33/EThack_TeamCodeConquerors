/**
 * Stock Data Controller
 * Proxies requests to the Python AI Service (FastAPI)
 * Adds Redis-style in-memory caching for performance
 */
const axios = require('axios');
const logger = require('../utils/logger');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
const AI_API_KEY = process.env.AI_SERVICE_API_KEY || 'internal_api_key_between_services';

// Simple in-memory cache (TTL-based)
const cache = new Map();
const CACHE_TTL = {
    stock_info: 5 * 60 * 1000,      // 5 minutes
    history: 30 * 60 * 1000,        // 30 minutes
    financials: 60 * 60 * 1000,     // 1 hour
    peers: 15 * 60 * 1000,          // 15 minutes
    reasoning: 60 * 60 * 1000,      // 1 hour
};

/**
 * Get from cache or call AI service
 */
const getCached = (key) => {
    const entry = cache.get(key);
    if (entry && Date.now() < entry.expiry) {
        return entry.data;
    }
    cache.delete(key);
    return null;
};

const setCache = (key, data, ttl) => {
    cache.set(key, { data, expiry: Date.now() + ttl });
};

/**
 * Axios client for AI service
 */
const aiClient = axios.create({
    baseURL: AI_SERVICE_URL,
    timeout: 30000,
    headers: {
        'x-api-key': AI_API_KEY,
        'Content-Type': 'application/json',
    },
});

// ============================================================
// @route   GET /api/stocks/:symbol
// @desc    Get live stock info (price, ratios, fundamentals)
// @access  Public
// ============================================================
const getStockInfo = async (req, res) => {
    const { symbol } = req.params;
    const upperSymbol = symbol.toUpperCase();

    const cacheKey = `stock_info_${upperSymbol}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, data: cached });
    }

    try {
        const response = await aiClient.get(`/api/v1/stocks/${upperSymbol}`);
        const data = response.data.data;
        setCache(cacheKey, data, CACHE_TTL.stock_info);
        res.json({ success: true, cached: false, data });
    } catch (error) {
        logger.error(`getStockInfo error for ${upperSymbol}: ${error.message}`);
        const status = error.response?.status || 502;
        res.status(status).json({
            success: false,
            message: error.response?.data?.detail || `Failed to fetch data for ${upperSymbol}`,
        });
    }
};

// ============================================================
// @route   GET /api/stocks/:symbol/history
// @desc    Get historical OHLCV data
// @access  Public
// ============================================================
const getStockHistory = async (req, res) => {
    const { symbol } = req.params;
    const { period = '1y', interval = '1d' } = req.query;
    const upperSymbol = symbol.toUpperCase();

    const cacheKey = `history_${upperSymbol}_${period}_${interval}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, data: cached });
    }

    try {
        const response = await aiClient.get(`/api/v1/stocks/${upperSymbol}/history`, {
            params: { period, interval },
        });
        const data = response.data.data;
        setCache(cacheKey, data, CACHE_TTL.history);
        res.json({ success: true, cached: false, data });
    } catch (error) {
        logger.error(`getStockHistory error for ${upperSymbol}: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: error.response?.data?.detail || 'Failed to fetch history',
        });
    }
};

// ============================================================
// @route   GET /api/stocks/:symbol/financials
// @desc    Get P&L, balance sheet, cash flow
// @access  Public
// ============================================================
const getStockFinancials = async (req, res) => {
    const { symbol } = req.params;
    const upperSymbol = symbol.toUpperCase();

    const cacheKey = `financials_${upperSymbol}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, data: cached });
    }

    try {
        const response = await aiClient.get(`/api/v1/stocks/${upperSymbol}/financials`);
        const data = response.data.data;
        setCache(cacheKey, data, CACHE_TTL.financials);
        res.json({ success: true, cached: false, data });
    } catch (error) {
        logger.error(`getStockFinancials error for ${upperSymbol}: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: error.response?.data?.detail || 'Failed to fetch financials',
        });
    }
};

// ============================================================
// @route   GET /api/stocks/compare?symbols=TCS,INFY,WIPRO
// @desc    Compare multiple stocks
// @access  Public
// ============================================================
const compareStocks = async (req, res) => {
    const { symbols } = req.query;
    if (!symbols) {
        return res.status(400).json({ success: false, message: 'symbols query param required' });
    }

    const symbolList = symbols.split(',').map((s) => s.trim().toUpperCase());
    if (symbolList.length < 2) {
        return res.status(400).json({ success: false, message: 'Provide at least 2 symbols' });
    }

    const cacheKey = `compare_${symbolList.sort().join('_')}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, data: cached });
    }

    try {
        const response = await aiClient.get(`/api/v1/stocks/compare/peers`, {
            params: { symbols: symbolList.join(',') },
        });
        const data = response.data.data;
        setCache(cacheKey, data, CACHE_TTL.peers);
        res.json({ success: true, cached: false, data });
    } catch (error) {
        logger.error(`compareStocks error: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: error.response?.data?.detail || 'Failed to compare stocks',
        });
    }
};

// ============================================================
// @route   GET /api/stocks/nse/top
// @desc    Get top NSE stocks (Nifty 50)
// @access  Public
// ============================================================
const getNseTop = async (req, res) => {
    const { limit = 20 } = req.query;

    const cacheKey = `nse_top_${limit}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, data: cached });
    }

    try {
        const response = await aiClient.get(`/api/v1/stocks/search/nse-top`, {
            params: { limit },
        });
        const data = response.data.data;
        setCache(cacheKey, data, CACHE_TTL.stock_info);
        res.json({ success: true, cached: false, data });
    } catch (error) {
        logger.error(`getNseTop error: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: 'Failed to fetch top NSE stocks',
        });
    }
};

// ============================================================
// REASONING PROXY ROUTES
// ============================================================

// @route   GET /api/stocks/:symbol/thesis
// @desc    Investment thesis via Gemini reasoning
const getInvestmentThesis = async (req, res) => {
    const { symbol } = req.params;
    const upperSymbol = symbol.toUpperCase();

    const cacheKey = `thesis_${upperSymbol}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, ...cached });
    }

    try {
        const response = await aiClient.post(
            `/api/v1/reasoning/investment-thesis/${upperSymbol}`
        );
        setCache(cacheKey, response.data, CACHE_TTL.reasoning);
        res.json({ success: true, cached: false, ...response.data });
    } catch (error) {
        logger.error(`getInvestmentThesis error for ${upperSymbol}: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: error.response?.data?.detail || 'Failed to generate thesis',
        });
    }
};

// @route   GET /api/stocks/:symbol/risk
// @desc    AI risk assessment for a stock
const getRiskAssessment = async (req, res) => {
    const { symbol } = req.params;
    const upperSymbol = symbol.toUpperCase();

    const cacheKey = `risk_${upperSymbol}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, ...cached });
    }

    try {
        const response = await aiClient.post(`/api/v1/reasoning/risk/${upperSymbol}`);
        setCache(cacheKey, response.data, CACHE_TTL.reasoning);
        res.json({ success: true, cached: false, ...response.data });
    } catch (error) {
        logger.error(`getRiskAssessment error for ${upperSymbol}: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: error.response?.data?.detail || 'Failed to assess risk',
        });
    }
};

// @route   GET /api/stocks/:symbol/summary
// @desc    Financial summary with health score
const getFinancialSummary = async (req, res) => {
    const { symbol } = req.params;
    const upperSymbol = symbol.toUpperCase();

    const cacheKey = `summary_${upperSymbol}`;
    const cached = getCached(cacheKey);
    if (cached) {
        return res.json({ success: true, cached: true, ...cached });
    }

    try {
        const response = await aiClient.get(`/api/v1/reasoning/summary/${upperSymbol}`);
        setCache(cacheKey, response.data, CACHE_TTL.reasoning);
        res.json({ success: true, cached: false, ...response.data });
    } catch (error) {
        logger.error(`getFinancialSummary error for ${upperSymbol}: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: 'Failed to generate financial summary',
        });
    }
};

// @route   POST /api/stocks/ask
// @desc    Free-form AI financial Q&A
const askQuestion = async (req, res) => {
    const { question, symbol, additional_context } = req.body;

    if (!question) {
        return res.status(400).json({ success: false, message: 'question is required' });
    }

    try {
        const response = await aiClient.post('/api/v1/reasoning/ask', {
            question,
            symbol,
            additional_context,
        });
        res.json({ success: true, ...response.data });
    } catch (error) {
        logger.error(`askQuestion error: ${error.message}`);
        res.status(error.response?.status || 502).json({
            success: false,
            message: error.response?.data?.detail || 'Failed to process question',
        });
    }
};

// ============================================================
// CACHE MANAGEMENT
// ============================================================
const clearCache = async (req, res) => {
    const { symbol } = req.params;
    if (symbol) {
        // Clear all cache entries for a specific symbol
        let cleared = 0;
        for (const key of cache.keys()) {
            if (key.includes(symbol.toUpperCase())) {
                cache.delete(key);
                cleared++;
            }
        }
        return res.json({ success: true, message: `Cleared ${cleared} cache entries for ${symbol}` });
    }
    cache.clear();
    res.json({ success: true, message: 'All cache cleared', entries_cleared: cache.size });
};

const getCacheStats = async (req, res) => {
    const stats = {
        total_entries: cache.size,
        entries: [],
    };
    for (const [key, value] of cache.entries()) {
        stats.entries.push({
            key,
            expires_in_seconds: Math.round((value.expiry - Date.now()) / 1000),
        });
    }
    res.json({ success: true, cache: stats });
};

module.exports = {
    getStockInfo,
    getStockHistory,
    getStockFinancials,
    compareStocks,
    getNseTop,
    getInvestmentThesis,
    getRiskAssessment,
    getFinancialSummary,
    askQuestion,
    clearCache,
    getCacheStats,
};
