const { verifyAccessToken } = require('../utils/jwt');
const User = require('../models/User');
const logger = require('../utils/logger');

/**
 * Protect routes — ensures user is authenticated
 */
const protect = async (req, res, next) => {
    try {
        let token;

        // Get token from Authorization header: "Bearer <token>"
        if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
            token = req.headers.authorization.split(' ')[1];
        }

        if (!token) {
            return res.status(401).json({
                success: false,
                message: 'Access denied. No token provided.',
            });
        }

        // Verify token
        const decoded = verifyAccessToken(token);
        if (!decoded) {
            return res.status(401).json({
                success: false,
                message: 'Invalid or expired token. Please login again.',
            });
        }

        // Check token type
        if (decoded.type !== 'access') {
            return res.status(401).json({
                success: false,
                message: 'Invalid token type.',
            });
        }

        // Fetch user from DB
        const user = await User.findById(decoded.id);
        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'User no longer exists.',
            });
        }

        // Attach user to request object
        req.user = user;
        next();

    } catch (error) {
        logger.error(`Auth middleware error: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: 'Authentication error. Please try again.',
        });
    }
};

/**
 * Restrict to specific roles
 * Usage: restrictTo('admin', 'premium')
 */
const restrictTo = (...roles) => {
    return (req, res, next) => {
        if (!roles.includes(req.user.role)) {
            return res.status(403).json({
                success: false,
                message: `Access denied. Required role: ${roles.join(' or ')}.`,
            });
        }
        next();
    };
};

/**
 * Optional auth — attaches user if token present, doesn't fail if not
 */
const optionalAuth = async (req, res, next) => {
    try {
        let token;
        if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
            token = req.headers.authorization.split(' ')[1];
        }

        if (token) {
            const decoded = verifyAccessToken(token);
            if (decoded) {
                const user = await User.findById(decoded.id);
                if (user) req.user = user;
            }
        }
        next();
    } catch (error) {
        next(); // Silently continue without auth
    }
};

module.exports = { protect, restrictTo, optionalAuth };
