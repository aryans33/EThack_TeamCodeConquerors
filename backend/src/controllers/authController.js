const { validationResult } = require('express-validator');
const User = require('../models/User');
const { generateTokenPair, verifyRefreshToken } = require('../utils/jwt');
const logger = require('../utils/logger');

// ============================================
// @route   POST /api/auth/register
// @desc    Register a new user
// @access  Public
// ============================================
const register = async (req, res) => {
    try {
        // Validate request body
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array(),
            });
        }

        const { name, email, password } = req.body;

        // Check if email already exists
        const existingUser = await User.findOne({ email: email.toLowerCase() });
        if (existingUser) {
            return res.status(409).json({
                success: false,
                message: 'An account with this email already exists.',
            });
        }

        // Create user (password will be hashed by pre-save hook)
        const user = await User.create({ name, email, password });

        // Generate tokens
        const { accessToken, refreshToken } = generateTokenPair(user._id);

        // Save refresh token
        user.refreshToken = refreshToken;
        user.lastLogin = new Date();
        await user.save({ validateBeforeSave: false });

        logger.info(`New user registered: ${email}`);

        return res.status(201).json({
            success: true,
            message: 'Account created successfully!',
            data: {
                user: user.toSafeObject(),
                accessToken,
                refreshToken,
            },
        });

    } catch (error) {
        logger.error(`Register error: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: 'Registration failed. Please try again.',
        });
    }
};

// ============================================
// @route   POST /api/auth/login
// @desc    Login user
// @access  Public
// ============================================
const login = async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array(),
            });
        }

        const { email, password } = req.body;

        // Fetch user WITH password (select: false by default)
        const user = await User.findOne({ email: email.toLowerCase() }).select('+password +refreshToken');
        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password.',
            });
        }

        // Compare password
        const isPasswordValid = await user.comparePassword(password);
        if (!isPasswordValid) {
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password.',
            });
        }

        // Generate new tokens
        const { accessToken, refreshToken } = generateTokenPair(user._id);

        // Update refresh token and last login
        user.refreshToken = refreshToken;
        user.lastLogin = new Date();
        await user.save({ validateBeforeSave: false });

        logger.info(`User logged in: ${email}`);

        return res.status(200).json({
            success: true,
            message: 'Login successful!',
            data: {
                user: user.toSafeObject(),
                accessToken,
                refreshToken,
            },
        });

    } catch (error) {
        logger.error(`Login error: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: 'Login failed. Please try again.',
        });
    }
};

// ============================================
// @route   POST /api/auth/refresh
// @desc    Refresh access token using refresh token
// @access  Public
// ============================================
const refreshToken = async (req, res) => {
    try {
        const { refreshToken: token } = req.body;

        if (!token) {
            return res.status(400).json({
                success: false,
                message: 'Refresh token is required.',
            });
        }

        // Verify refresh token
        const decoded = verifyRefreshToken(token);
        if (!decoded) {
            return res.status(401).json({
                success: false,
                message: 'Invalid or expired refresh token. Please login again.',
            });
        }

        // Check token type
        if (decoded.type !== 'refresh') {
            return res.status(401).json({
                success: false,
                message: 'Invalid token type.',
            });
        }

        // Fetch user
        const user = await User.findById(decoded.id).select('+refreshToken');
        if (!user || user.refreshToken !== token) {
            return res.status(401).json({
                success: false,
                message: 'Refresh token is invalid or has been revoked.',
            });
        }

        // Issue new token pair (rotation)
        const { accessToken, refreshToken: newRefreshToken } = generateTokenPair(user._id);

        user.refreshToken = newRefreshToken;
        await user.save({ validateBeforeSave: false });

        return res.status(200).json({
            success: true,
            message: 'Tokens refreshed.',
            data: {
                accessToken,
                refreshToken: newRefreshToken,
            },
        });

    } catch (error) {
        logger.error(`Refresh token error: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: 'Token refresh failed.',
        });
    }
};

// ============================================
// @route   POST /api/auth/logout
// @desc    Logout user (invalidate refresh token)
// @access  Private
// ============================================
const logout = async (req, res) => {
    try {
        const user = await User.findById(req.user._id);
        user.refreshToken = null;
        await user.save({ validateBeforeSave: false });

        logger.info(`User logged out: ${req.user.email}`);

        return res.status(200).json({
            success: true,
            message: 'Logged out successfully.',
        });

    } catch (error) {
        logger.error(`Logout error: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: 'Logout failed.',
        });
    }
};

// ============================================
// @route   GET /api/auth/me
// @desc    Get current logged-in user
// @access  Private
// ============================================
const getMe = async (req, res) => {
    try {
        const user = await User.findById(req.user._id);
        return res.status(200).json({
            success: true,
            data: { user: user.toSafeObject() },
        });
    } catch (error) {
        logger.error(`Get me error: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: 'Failed to get user info.',
        });
    }
};

// ============================================
// @route   PUT /api/auth/update-profile
// @desc    Update user profile
// @access  Private
// ============================================
const updateProfile = async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array(),
            });
        }

        const { name, preferences } = req.body;
        const updateData = {};
        if (name) updateData.name = name;
        if (preferences) updateData.preferences = { ...req.user.preferences, ...preferences };

        const user = await User.findByIdAndUpdate(
            req.user._id,
            { $set: updateData },
            { new: true, runValidators: true }
        );

        return res.status(200).json({
            success: true,
            message: 'Profile updated successfully.',
            data: { user: user.toSafeObject() },
        });

    } catch (error) {
        logger.error(`Update profile error: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: 'Profile update failed.',
        });
    }
};

module.exports = { register, login, refreshToken, logout, getMe, updateProfile };
