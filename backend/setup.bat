@echo off
REM ================================================
REM FinAnalysis — Backend Setup Script  
REM Run this once from the backend/ directory
REM ================================================

echo [1/2] Installing Node.js dependencies...
npm install

echo [2/2] Creating logs directory...
if not exist "logs" mkdir logs

echo.
echo ========================================
echo  Backend setup complete!
echo  To start the backend:
echo    npm run dev
echo  
echo  API: http://localhost:5000
echo  Health: http://localhost:5000/health
echo ========================================
