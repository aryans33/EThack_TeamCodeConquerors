"""
FastAPI Router — Reasoning Endpoints
Investment thesis, stock comparison, sector analysis, risk assessment.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.tools.reasoning_tool import (
    generate_investment_thesis,
    compare_stocks_reasoning,
    assess_stock_risk,
    get_financial_summary,
    custom_financial_reasoning,
)
from app.tools.yfinance_tool import get_stock_info, get_financial_statements, get_peer_comparison
from app.services.mongo.mongo_service import get_mongo_service

router = APIRouter(prefix="/api/v1/reasoning", tags=["Reasoning"])
logger = logging.getLogger(__name__)


# ============================================================
# REQUEST MODELS
# ============================================================
class InvestmentThesisRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol e.g. RELIANCE")
    include_agent_analysis: bool = Field(default=False)


class CompareStocksRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of stock symbols to compare", min_length=2, max_length=5)


class SectorAnalysisRequest(BaseModel):
    sector: str = Field(..., description="Sector name e.g. Banking, IT, Pharma")
    symbols: List[str] = Field(..., description="Stocks in this sector")


class CustomReasoningRequest(BaseModel):
    question: str = Field(..., description="Financial question to analyze")
    symbol: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None


# ============================================================
# INVESTMENT THESIS
# ============================================================
@router.post("/investment-thesis/{symbol}")
async def get_investment_thesis(symbol: str, include_agent_cache: bool = False):
    """
    Generate a complete investment thesis for a stock using Gemini reasoning.

    Fetches live financial data from yfinance and synthesizes a structured:
    - Bull Case / Bear Case / Base Case
    - Buy/Hold/Sell verdict
    - Target price range
    - Investment horizon recommendation
    """
    # Fetch live financial data
    stock_info = get_stock_info(symbol)
    if "error" in stock_info:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}")

    financials = get_financial_statements(symbol)

    financial_data = {
        "market_data": stock_info,
        "financials": financials,
    }

    # Optionally include cached agent analysis
    analysis_data = None
    if include_agent_cache:
        try:
            mongo = await get_mongo_service()
            cached = await mongo.get_cached_analysis(symbol, "full_analysis")
            if cached:
                analysis_data = cached.get("data", {})
        except Exception:
            pass

    result = generate_investment_thesis(
        symbol=symbol,
        financial_data=financial_data,
        analysis_data=analysis_data,
    )

    return {"success": True, **result}


# ============================================================
# STOCK COMPARISON
# ============================================================
@router.post("/compare")
async def compare_stocks(request: CompareStocksRequest):
    """
    Compare 2–5 stocks side by side with AI-reasoned recommendation.

    Returns ranking, differentiators, and portfolio allocation suggestion.

    **Example:** Compare TCS, Infosys, Wipro
    """
    stocks_data = []
    for symbol in request.symbols:
        info = get_stock_info(symbol)
        if "error" not in info:
            stocks_data.append(info)

    if len(stocks_data) < 2:
        raise HTTPException(status_code=400, detail="Could not fetch data for at least 2 stocks.")

    result = compare_stocks_reasoning(stocks_data)
    return {"success": True, **result}


# ============================================================
# SECTOR ANALYSIS
# ============================================================
@router.post("/sector")
async def sector_analysis(request: SectorAnalysisRequest):
    """
    Analyze an entire market sector with AI reasoning.

    Provides sector outlook, key drivers, headwinds, and best picks.
    """
    stocks_data = []
    for symbol in request.symbols[:8]:  # Limit to 8
        info = get_stock_info(symbol)
        if "error" not in info:
            stocks_data.append({
                "symbol": info["symbol"],
                "company": info["company_name"],
                "market_cap_cr": info["market_cap_cr"],
                "pe_ratio": info["pe_ratio"],
                "roe": info["roe"],
                "revenue_cr": info["revenue_cr"],
                "profit_margin": info["profit_margin"],
            })

    from app.tools.reasoning_tool import get_reasoning_tool
    result = get_reasoning_tool().sector_analysis(request.sector, stocks_data)

    return {"success": True, **result}


# ============================================================
# RISK ASSESSMENT
# ============================================================
@router.post("/risk/{symbol}")
async def risk_assessment(symbol: str):
    """
    Comprehensive AI-powered risk assessment for a stock.

    Scores business, financial, market, and regulatory risks 1-10.
    """
    stock_info = get_stock_info(symbol)
    if "error" in stock_info:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}")

    financials = get_financial_statements(symbol)

    data = {
        "market_data": stock_info,
        "financials": {
            "income_statement": financials.get("income_statement", [])[:4],
            "balance_sheet": financials.get("balance_sheet", [])[:2],
        },
    }

    result = assess_stock_risk(symbol=symbol, data=data)
    return {"success": True, **result}


# ============================================================
# FINANCIAL SUMMARY
# ============================================================
@router.get("/summary/{symbol}")
async def financial_summary(symbol: str):
    """
    AI-generated financial summary with health score (A-F).

    Quick overview of revenue, profitability, returns, balance sheet, and valuation.
    """
    stock_info = get_stock_info(symbol)
    if "error" in stock_info:
        raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}")

    data = {
        "valuation": {
            "pe_ratio": stock_info.get("pe_ratio"),
            "pb_ratio": stock_info.get("pb_ratio"),
            "market_cap_cr": stock_info.get("market_cap_cr"),
        },
        "profitability": {
            "gross_margin": stock_info.get("gross_margin"),
            "operating_margin": stock_info.get("operating_margin"),
            "profit_margin": stock_info.get("profit_margin"),
            "roe": stock_info.get("roe"),
            "roa": stock_info.get("roa"),
        },
        "leverage": {
            "debt_to_equity": stock_info.get("debt_to_equity"),
            "current_ratio": stock_info.get("current_ratio"),
            "total_debt_cr": stock_info.get("total_debt_cr"),
        },
        "growth": {
            "revenue_cr": stock_info.get("revenue_cr"),
            "eps": stock_info.get("eps"),
        },
        "market": {
            "current_price": stock_info.get("current_price"),
            "52w_high": stock_info.get("fifty_two_week_high"),
            "52w_low": stock_info.get("fifty_two_week_low"),
            "beta": stock_info.get("beta"),
            "recommendation": stock_info.get("recommendation"),
        },
    }

    result = get_financial_summary(symbol=symbol, data=data)
    return {"success": True, **result}


# ============================================================
# CUSTOM REASONING
# ============================================================
@router.post("/ask")
async def custom_reasoning(request: CustomReasoningRequest):
    """
    Ask any financial question — free-form AI reasoning with Gemini.

    If a symbol is provided, live stock data is automatically included as context.

    **Examples:**
    - "Is HDFC Bank a better buy than ICICI Bank right now?"
    - "What sectors should I invest in during rising interest rates?"
    - "Explain the impact of RBI rate hikes on IT stocks"
    """
    context = request.additional_context or {}

    if request.symbol:
        stock_info = get_stock_info(request.symbol)
        if "error" not in stock_info:
            context["stock_data"] = stock_info

    result = custom_financial_reasoning(
        question=request.question,
        context_data=context,
    )

    return {"success": True, **result}
