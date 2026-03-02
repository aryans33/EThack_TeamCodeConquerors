const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth');
const {
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
} = require('../controllers/stockController');

// ============================================================
// MARKET DATA ROUTES (Public)
// ============================================================

// GET /api/stocks/nse/top?limit=20
// Get top NSE stocks (Nifty 50)
router.get('/nse/top', getNseTop);

// GET /api/stocks/compare?symbols=TCS,INFY,WIPRO
// Compare multiple stocks side by side
router.get('/compare', compareStocks);

// GET /api/stocks/:symbol
// Live stock info — price, ratios, fundamentals
router.get('/:symbol', getStockInfo);

// GET /api/stocks/:symbol/history?period=1y&interval=1d
// Historical OHLCV data
router.get('/:symbol/history', getStockHistory);

// GET /api/stocks/:symbol/financials
// P&L, Balance Sheet, Cash Flow
router.get('/:symbol/financials', getStockFinancials);

// ============================================================
// AI REASONING ROUTES (Protected — requires JWT)
// ============================================================

// GET /api/stocks/:symbol/thesis
// Generate investment thesis via Gemini
router.get('/:symbol/thesis', protect, getInvestmentThesis);

// GET /api/stocks/:symbol/risk
// AI-powered risk assessment
router.get('/:symbol/risk', protect, getRiskAssessment);

// GET /api/stocks/:symbol/summary
// Financial summary with health score (A-F)
router.get('/:symbol/summary', protect, getFinancialSummary);

// POST /api/stocks/ask
// Free-form financial Q&A
router.post('/ask', protect, askQuestion);

// ============================================================
// CACHE MANAGEMENT (Protected)
// ============================================================

// GET /api/stocks/cache/stats
router.get('/cache/stats', protect, getCacheStats);

// DELETE /api/stocks/cache
// Clear all cache
router.delete('/cache', protect, clearCache);

// DELETE /api/stocks/cache/:symbol
// Clear cache for specific symbol
router.delete('/cache/:symbol', protect, clearCache);

module.exports = router;
