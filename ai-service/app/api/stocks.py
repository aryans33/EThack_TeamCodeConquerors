"""
FastAPI Router — Stock Data
Live market data via yfinance for Indian NSE/BSE stocks.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from app.tools.yfinance_tool import (
    get_stock_info,
    get_historical_prices,
    get_financial_statements,
    get_peer_comparison,
)

router = APIRouter(prefix="/api/v1/stocks", tags=["Stocks"])
logger = logging.getLogger(__name__)


@router.get("/{symbol}")
async def stock_info(symbol: str):
    """
    Get comprehensive stock info for an Indian stock (NSE/BSE).
    Includes price, ratios, fundamentals. Cached for 5 minutes.

    **Example:** /api/v1/stocks/RELIANCE
    """
    result = get_stock_info(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=f"Stock data not found for {symbol}: {result['error']}")
    return {"success": True, "data": result}


@router.get("/{symbol}/history")
async def stock_history(
    symbol: str,
    period: str = Query(default="1y", pattern="^(1mo|3mo|6mo|1y|2y|5y|10y|max)$"),
    interval: str = Query(default="1d", pattern="^(1d|1wk|1mo)$"),
):
    """
    Get historical OHLCV price data.

    - **period**: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max
    - **interval**: 1d (daily), 1wk (weekly), 1mo (monthly)
    """
    result = get_historical_prices(symbol=symbol, period=period, interval=interval)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"success": True, "data": result}


@router.get("/{symbol}/financials")
async def stock_financials(symbol: str):
    """
    Get income statement, balance sheet, and cash flow data.
    Values in ₹ Crore.
    """
    result = get_financial_statements(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"success": True, "data": result}


@router.get("/compare/peers")
async def compare_peers(
    symbols: str = Query(..., description="Comma-separated symbols e.g. RELIANCE,ONGC,BPCL"),
):
    """
    Compare multiple stocks side by side.
    Useful for sector benchmarking.

    **Example:** /api/v1/stocks/compare/peers?symbols=TCS,INFY,WIPRO
    """
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 symbols.")
    if len(symbol_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 symbols allowed.")

    result = get_peer_comparison(symbol_list)
    return {"success": True, "data": result}


@router.get("/search/nse-top")
async def get_nse_top(
    limit: int = Query(default=20, ge=5, le=50)
):
    """
    Get data for top NSE stocks (Nifty 50 constituents).
    """
    nifty50 = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "ITC", "AXISBANK", "BAJFINANCE", "LT",
        "SUNPHARMA", "MARUTI", "NTPC", "ULTRA_CEMCO", "TITAN",
        "WIPRO", "ONGC", "TECHM", "POWERGRID", "INDUSINDBK",
    ]

    top_stocks = []
    for symbol in nifty50[:limit]:
        info = get_stock_info(symbol)
        if "error" not in info:
            top_stocks.append({
                "symbol": info["symbol"],
                "company_name": info["company_name"],
                "current_price": info["current_price"],
                "market_cap_cr": info["market_cap_cr"],
                "pe_ratio": info["pe_ratio"],
                "roe": info["roe"],
                "sector": info["sector"],
                "recommendation": info["recommendation"],
            })

    return {
        "success": True,
        "data": top_stocks,
        "total": len(top_stocks),
    }
