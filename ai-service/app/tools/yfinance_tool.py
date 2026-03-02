"""
AutoGen Tools — Y Finance Tool
Fetches live and historical stock data from Yahoo Finance (yfinance).
Used by AutoGen agents for real-time market data.
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from cachetools import TTLCache
import json

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# In-memory cache for stock data
_stock_cache = TTLCache(maxsize=200, ttl=settings.stock_cache_ttl)


def _get_yf_symbol(symbol: str) -> str:
    """
    Convert Indian stock symbol to yfinance format.
    e.g., RELIANCE → RELIANCE.NS (NSE)
         RELIANCE.BSE → RELIANCE.BO (BSE)
    """
    symbol = symbol.upper().strip()
    if "." in symbol:
        return symbol  # Already has suffix
    return f"{symbol}{settings.default_exchange_suffix}"


def get_stock_info(symbol: str) -> Dict[str, Any]:
    """
    AutoGen Tool: Fetch comprehensive company info from Yahoo Finance.

    Args:
        symbol: Indian stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')

    Returns:
        Dict with company info, key ratios, and market data
    """
    cache_key = f"info_{symbol}"
    if cache_key in _stock_cache:
        logger.debug(f"Cache hit: {cache_key}")
        return _stock_cache[cache_key]

    try:
        yf_symbol = _get_yf_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        result = {
            "symbol": symbol.upper(),
            "yf_symbol": yf_symbol,
            "company_name": info.get("longName") or info.get("shortName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "exchange": info.get("exchange", "NSE"),
            "currency": info.get("financialCurrency", "INR"),

            # Price data
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "market_cap_cr": round((info.get("marketCap") or 0) / 1e7, 2),  # ₹ Crore
            "volume": info.get("regularMarketVolume"),

            # Fundamental ratios
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "eps": info.get("trailingEps"),
            "roe": round((info.get("returnOnEquity") or 0) * 100, 2),     # %
            "roa": round((info.get("returnOnAssets") or 0) * 100, 2),     # %
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),

            # Margins
            "gross_margin": round((info.get("grossMargins") or 0) * 100, 2),
            "operating_margin": round((info.get("operatingMargins") or 0) * 100, 2),
            "profit_margin": round((info.get("profitMargins") or 0) * 100, 2),

            # Revenue & Earnings
            "revenue_cr": round((info.get("totalRevenue") or 0) / 1e7, 2),
            "ebitda_cr": round((info.get("ebitda") or 0) / 1e7, 2),
            "total_cash_cr": round((info.get("totalCash") or 0) / 1e7, 2),
            "total_debt_cr": round((info.get("totalDebt") or 0) / 1e7, 2),

            # Analyst data
            "analyst_target_price": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey", "N/A"),
            "beta": info.get("beta"),
            "dividend_yield": round((info.get("dividendYield") or 0) * 100, 2),

            "fetched_at": datetime.utcnow().isoformat(),
        }

        _stock_cache[cache_key] = result
        logger.info(f"✅ Fetched stock info for {symbol}")
        return result

    except Exception as e:
        logger.error(f"yfinance get_stock_info error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e), "status": "failed"}


def get_historical_prices(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> Dict[str, Any]:
    """
    AutoGen Tool: Fetch historical OHLCV price data.

    Args:
        symbol: Stock symbol
        period: Data period ('1mo', '3mo', '6mo', '1y', '2y', '5y')
        interval: Data interval ('1d', '1wk', '1mo')

    Returns:
        Dict with OHLCV data points
    """
    cache_key = f"hist_{symbol}_{period}_{interval}"
    if cache_key in _stock_cache:
        return _stock_cache[cache_key]

    try:
        yf_symbol = _get_yf_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            return {"symbol": symbol, "data": [], "error": "No historical data found"}

        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        # Calculate returns
        if len(records) >= 2:
            first_close = records[0]["close"]
            last_close = records[-1]["close"]
            total_return = round(((last_close - first_close) / first_close) * 100, 2)
        else:
            total_return = 0

        result = {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "total_records": len(records),
            "total_return_pct": total_return,
            "data": records,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        _stock_cache[cache_key] = result
        return result

    except Exception as e:
        logger.error(f"yfinance historical error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e), "data": []}


def get_financial_statements(symbol: str) -> Dict[str, Any]:
    """
    AutoGen Tool: Fetch income statement, balance sheet, cash flow.

    Args:
        symbol: Stock symbol

    Returns:
        Dict with quarterly and annual financials
    """
    try:
        yf_symbol = _get_yf_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)

        def df_to_records(df: pd.DataFrame) -> List[Dict]:
            if df is None or df.empty:
                return []
            df = df.fillna(0)
            records = []
            for col in df.columns:
                record = {"period": str(col.date() if hasattr(col, 'date') else col)}
                for idx in df.index:
                    value = df.loc[idx, col]
                    # Convert to crores
                    record[str(idx)] = round(float(value) / 1e7, 2) if abs(float(value)) > 1e5 else round(float(value), 2)
                records.append(record)
            return records

        return {
            "symbol": symbol.upper(),
            "income_statement": df_to_records(ticker.financials),
            "income_statement_quarterly": df_to_records(ticker.quarterly_financials),
            "balance_sheet": df_to_records(ticker.balance_sheet),
            "cash_flow": df_to_records(ticker.cashflow),
            "fetched_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"yfinance financials error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def get_peer_comparison(symbols: List[str]) -> Dict[str, Any]:
    """
    AutoGen Tool: Compare multiple stocks (sector benchmarking).

    Args:
        symbols: List of stock symbols to compare

    Returns:
        Dict with comparative ratios for all symbols
    """
    comparison = []
    for symbol in symbols[:10]:  # Limit to 10
        info = get_stock_info(symbol)
        comparison.append({
            "symbol": symbol.upper(),
            "company_name": info.get("company_name", "N/A"),
            "pe_ratio": info.get("pe_ratio"),
            "pb_ratio": info.get("pb_ratio"),
            "roe": info.get("roe"),
            "profit_margin": info.get("profit_margin"),
            "debt_to_equity": info.get("debt_to_equity"),
            "market_cap_cr": info.get("market_cap_cr"),
            "current_ratio": info.get("current_ratio"),
            "eps": info.get("eps"),
            "dividend_yield": info.get("dividend_yield"),
        })

    return {
        "comparison": comparison,
        "count": len(comparison),
        "fetched_at": datetime.utcnow().isoformat(),
    }
