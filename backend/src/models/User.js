const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema(
    {
        name: {
            type: String,
            required: [true, 'Name is required'],
            trim: true,
            minlength: [2, 'Name must be at least 2 characters'],
            maxlength: [50, 'Name cannot exceed 50 characters'],
        },
        email: {
            type: String,
            required: [true, 'Email is required'],
            unique: true,
            lowercase: true,
            trim: true,
            match: [/^\S+@\S+\.\S+$/, 'Please provide a valid email'],
        },
        password: {
            type: String,
            required: [true, 'Password is required'],
            minlength: [8, 'Password must be at least 8 characters'],
            select: false, // Don't return password by default
        },
        avatar: {
            type: String,
            default: null,
        },
        role: {
            type: String,
            enum: ['user', 'premium', 'admin'],
            default: 'user',
        },
        // User's watchlist of stock symbols
        watchlist: [
            {
                symbol: { type: String, uppercase: true },
                exchange: { type: String, default: 'NSE' },
                addedAt: { type: Date, default: Date.now },
            },
        ],
        // Alert preferences
        alerts: [
            {
                symbol: { type: String, uppercase: true },
                type: { type: String, enum: ['price_above', 'price_below', 'percent_change'] },
                targetValue: { type: Number },
                isActive: { type: Boolean, default: true },
                createdAt: { type: Date, default: Date.now },
                triggeredAt: { type: Date, default: null },
            },
        ],
        // User preferences
        preferences: {
            currency: { type: String, default: 'INR' },
            theme: { type: String, enum: ['dark', 'light'], default: 'dark' },
            defaultExchange: { type: String, enum: ['NSE', 'BSE'], default: 'NSE' },
            emailNotifications: { type: Boolean, default: true },
        },
        isVerified: {
            type: Boolean,
            default: false,
        },
        verificationToken: String,
        passwordResetToken: String,
        passwordResetExpires: Date,
        refreshToken: {
            type: String,
            select: false,
        },
        lastLogin: {
            type: Date,
            default: null,
        },
    },
    {
        timestamps: true, // Adds createdAt and updatedAt
    }
);

// ============================================
// PRE-SAVE HOOK: Hash password before saving
// ============================================
userSchema.pre('save', async function (next) {
    // Only hash password if it was modified
    if (!this.isModified('password')) return next();

    const saltRounds = 12;
    this.password = await bcrypt.hash(this.password, saltRounds);
    next();
});

// ============================================
// INSTANCE METHOD: Compare passwords
// ============================================
userSchema.methods.comparePassword = async function (candidatePassword) {
    return bcrypt.compare(candidatePassword, this.password);
};

// ============================================
// INSTANCE METHOD: Transform to safe JSON (no sensitive fields)
// ============================================
userSchema.methods.toSafeObject = function () {
    const obj = this.toObject();
    delete obj.password;
    delete obj.refreshToken;
    delete obj.verificationToken;
    delete obj.passwordResetToken;
    delete obj.passwordResetExpires;
    return obj;
};

// ============================================
// Add stock to watchlist
// ============================================
userSchema.methods.addToWatchlist = async function (symbol, exchange = 'NSE') {
    const exists = this.watchlist.some((item) => item.symbol === symbol.toUpperCase());
    if (!exists) {
        this.watchlist.push({ symbol: symbol.toUpperCase(), exchange });
        await this.save();
    }
    return this.watchlist;
};

// ============================================
// Remove stock from watchlist
// ============================================
userSchema.methods.removeFromWatchlist = async function (symbol) {
    this.watchlist = this.watchlist.filter((item) => item.symbol !== symbol.toUpperCase());
    await this.save();
    return this.watchlist;
};

const User = mongoose.model('User', userSchema);
module.exports = User;
