require('dotenv').config();
const app = require('./app');
const connectDB = require('./config/database');
const logger = require('./utils/logger');

const PORT = process.env.PORT || 5000;

// ============================================
// Connect to MongoDB, then start server
// ============================================
const startServer = async () => {
    await connectDB();

    const server = app.listen(PORT, () => {
        logger.info(`
╔═══════════════════════════════════════════╗
║   🚀 FinAnalysis Backend Server           ║
║   📡 Port     : ${PORT}                       ║
║   🛠️  Env      : ${process.env.NODE_ENV || 'development'}           ║
║   🕒 Started  : ${new Date().toLocaleTimeString()}              ║
╚═══════════════════════════════════════════╝
    `);
    });

    // ============================================
    // Graceful shutdown
    // ============================================
    const gracefulShutdown = (signal) => {
        logger.info(`${signal} received. Shutting down gracefully...`);
        server.close(() => {
            logger.info('HTTP server closed.');
            process.exit(0);
        });

        // Force exit if not done in 10s
        setTimeout(() => {
            logger.error('Forced shutdown after timeout');
            process.exit(1);
        }, 10000);
    };

    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

    // Handle uncaught exceptions
    process.on('uncaughtException', (err) => {
        logger.error(`Uncaught Exception: ${err.message}`, { stack: err.stack });
        process.exit(1);
    });

    process.on('unhandledRejection', (reason) => {
        logger.error(`Unhandled Rejection: ${reason}`);
        process.exit(1);
    });
};

startServer();
