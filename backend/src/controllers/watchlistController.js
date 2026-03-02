const User = require('../models/User');
const logger = require('../utils/logger');

// ============================================
// @route   GET /api/watchlist
// @desc    Get user's watchlist
// @access  Private
// ============================================
const getWatchlist = async (req, res) => {
    try {
        const user = await User.findById(req.user._id);
        return res.status(200).json({
            success: true,
            data: { watchlist: user.watchlist },
        });
    } catch (error) {
        logger.error(`Get watchlist error: ${error.message}`);
        return res.status(500).json({ success: false, message: 'Failed to fetch watchlist.' });
    }
};

// ============================================
// @route   POST /api/watchlist
// @desc    Add stock to watchlist
// @access  Private
// ============================================
const addToWatchlist = async (req, res) => {
    try {
        const { symbol, exchange = 'NSE' } = req.body;

        if (!symbol) {
            return res.status(400).json({ success: false, message: 'Stock symbol is required.' });
        }

        const user = await User.findById(req.user._id);
        const watchlist = await user.addToWatchlist(symbol, exchange);

        return res.status(200).json({
            success: true,
            message: `${symbol.toUpperCase()} added to watchlist.`,
            data: { watchlist },
        });
    } catch (error) {
        logger.error(`Add to watchlist error: ${error.message}`);
        return res.status(500).json({ success: false, message: 'Failed to add to watchlist.' });
    }
};

// ============================================
// @route   DELETE /api/watchlist/:symbol
// @desc    Remove stock from watchlist
// @access  Private
// ============================================
const removeFromWatchlist = async (req, res) => {
    try {
        const { symbol } = req.params;
        const user = await User.findById(req.user._id);
        const watchlist = await user.removeFromWatchlist(symbol);

        return res.status(200).json({
            success: true,
            message: `${symbol.toUpperCase()} removed from watchlist.`,
            data: { watchlist },
        });
    } catch (error) {
        logger.error(`Remove from watchlist error: ${error.message}`);
        return res.status(500).json({ success: false, message: 'Failed to remove from watchlist.' });
    }
};

module.exports = { getWatchlist, addToWatchlist, removeFromWatchlist };
