const express = require('express');
const { body } = require('express-validator');
const {
    register,
    login,
    refreshToken,
    logout,
    getMe,
    updateProfile,
} = require('../controllers/authController');
const { protect } = require('../middleware/auth');

const router = express.Router();

// ============================================
// Validation rules
// ============================================
const registerValidation = [
    body('name')
        .trim()
        .notEmpty().withMessage('Name is required')
        .isLength({ min: 2, max: 50 }).withMessage('Name must be 2–50 characters'),
    body('email')
        .isEmail().withMessage('Please provide a valid email')
        .normalizeEmail(),
    body('password')
        .isLength({ min: 8 }).withMessage('Password must be at least 8 characters')
        .matches(/\d/).withMessage('Password must contain at least one number'),
];

const loginValidation = [
    body('email').isEmail().withMessage('Valid email is required').normalizeEmail(),
    body('password').notEmpty().withMessage('Password is required'),
];

const updateProfileValidation = [
    body('name')
        .optional()
        .trim()
        .isLength({ min: 2, max: 50 }).withMessage('Name must be 2–50 characters'),
    body('preferences.theme')
        .optional()
        .isIn(['dark', 'light']).withMessage('Theme must be dark or light'),
    body('preferences.defaultExchange')
        .optional()
        .isIn(['NSE', 'BSE']).withMessage('Exchange must be NSE or BSE'),
];

// ============================================
// Routes
// ============================================
// Public routes
router.post('/register', registerValidation, register);
router.post('/login', loginValidation, login);
router.post('/refresh', refreshToken);

// Protected routes
router.post('/logout', protect, logout);
router.get('/me', protect, getMe);
router.put('/update-profile', protect, updateProfileValidation, updateProfile);

module.exports = router;
