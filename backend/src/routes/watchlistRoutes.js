const express = require('express');
const { protect } = require('../middleware/auth');
const {
    getWatchlist,
    addToWatchlist,
    removeFromWatchlist,
} = require('../controllers/watchlistController');

const router = express.Router();

// All watchlist routes are protected
router.use(protect);

router.get('/', getWatchlist);
router.post('/', addToWatchlist);
router.delete('/:symbol', removeFromWatchlist);

module.exports = router;
