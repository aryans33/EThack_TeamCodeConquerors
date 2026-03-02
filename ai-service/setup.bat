@echo off
REM ================================================
REM FinAnalysis — AI Service Python Setup Script
REM Run this once to create venv and install deps
REM ================================================

echo [1/4] Creating Python virtual environment...
python -m venv venv

echo [2/4] Activating virtual environment...
call venv\Scripts\activate

echo [3/4] Installing dependencies (this may take 2-5 minutes)...
pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Creating data directories...
if not exist "data\chromadb" mkdir data\chromadb
if not exist "uploads\temp" mkdir uploads\temp

echo.
echo ========================================
echo  Setup complete!
echo  To start the AI service:
echo    venv\Scripts\activate
echo    python main.py
echo  
echo  API docs: http://localhost:8000/docs
echo ========================================
