"""
AutoGen Tools — Arithmetic Tool
Financial calculation toolkit for computing key ratios and metrics.
Used by micro-agents to verify and compute financial ratios.
"""
from typing import Dict, Any, Optional, List
import math
import logging

logger = logging.getLogger(__name__)


# ============================================================
# VALUATION RATIOS
# ============================================================
def calculate_pe_ratio(market_price: float, eps: float) -> Dict[str, Any]:
    """P/E Ratio = Market Price / EPS"""
    if eps == 0:
        return {"ratio": None, "interpretation": "EPS is zero — P/E undefined"}
    pe = round(market_price / eps, 2)
    if pe < 0:
        interp = "Negative earnings (loss-making company)"
    elif pe < 15:
        interp = "Potentially undervalued (P/E < 15)"
    elif pe < 25:
        interp = "Fairly valued (P/E 15–25)"
    elif pe < 40:
        interp = "Moderately expensive (P/E 25–40)"
    else:
        interp = "Expensive / high growth expectations (P/E > 40)"

    return {"ratio": pe, "interpretation": interp, "formula": f"{market_price} / {eps}"}


def calculate_pb_ratio(market_price: float, book_value_per_share: float) -> Dict[str, Any]:
    """P/B Ratio = Market Price / Book Value Per Share"""
    if book_value_per_share == 0:
        return {"ratio": None, "interpretation": "Book value is zero"}
    pb = round(market_price / book_value_per_share, 2)
    if pb < 1:
        interp = "Trading below book value — potential value buy"
    elif pb < 3:
        interp = "Fairly valued relative to book"
    else:
        interp = "Premium to book value"
    return {"ratio": pb, "interpretation": interp}


def calculate_ev_ebitda(
    market_cap: float,
    total_debt: float,
    cash: float,
    ebitda: float,
) -> Dict[str, Any]:
    """EV/EBITDA = (Market Cap + Debt - Cash) / EBITDA"""
    if ebitda == 0:
        return {"ratio": None, "interpretation": "EBITDA is zero"}
    ev = market_cap + total_debt - cash
    ev_ebitda = round(ev / ebitda, 2)
    interp = "Undervalued" if ev_ebitda < 8 else ("Fairly valued" if ev_ebitda < 15 else "Expensive")
    return {"enterprise_value": round(ev, 2), "ratio": ev_ebitda, "interpretation": interp}


# ============================================================
# PROFITABILITY RATIOS
# ============================================================
def calculate_roe(net_income: float, shareholders_equity: float) -> Dict[str, Any]:
    """ROE = Net Income / Shareholders' Equity × 100"""
    if shareholders_equity == 0:
        return {"ratio": None, "interpretation": "Equity is zero"}
    roe = round((net_income / shareholders_equity) * 100, 2)
    interp = "Excellent (> 20%)" if roe > 20 else ("Good (15–20%)" if roe > 15 else ("Average (10–15%)" if roe > 10 else "Below average (< 10%)"))
    return {"ratio": roe, "unit": "%", "interpretation": interp}


def calculate_roce(ebit: float, capital_employed: float) -> Dict[str, Any]:
    """ROCE = EBIT / Capital Employed × 100"""
    if capital_employed == 0:
        return {"ratio": None, "interpretation": "Capital employed is zero"}
    roce = round((ebit / capital_employed) * 100, 2)
    interp = "Excellent" if roce > 20 else ("Good" if roce > 15 else "Average or below")
    return {"ratio": roce, "unit": "%", "interpretation": interp}


def calculate_margins(
    revenue: float,
    gross_profit: float,
    ebitda: float,
    ebit: float,
    net_income: float,
) -> Dict[str, Any]:
    """Calculate all margin ratios."""
    if revenue == 0:
        return {"error": "Revenue is zero"}

    return {
        "gross_margin": round((gross_profit / revenue) * 100, 2),
        "ebitda_margin": round((ebitda / revenue) * 100, 2),
        "ebit_margin": round((ebit / revenue) * 100, 2),
        "net_profit_margin": round((net_income / revenue) * 100, 2),
        "unit": "%",
    }


# ============================================================
# LIQUIDITY RATIOS
# ============================================================
def calculate_current_ratio(current_assets: float, current_liabilities: float) -> Dict[str, Any]:
    """Current Ratio = Current Assets / Current Liabilities"""
    if current_liabilities == 0:
        return {"ratio": None}
    cr = round(current_assets / current_liabilities, 2)
    interp = "Excellent (> 2)" if cr > 2 else ("Good (1.5–2)" if cr > 1.5 else ("Adequate (1–1.5)" if cr >= 1 else "⚠️ Liquidity concern (< 1)"))
    return {"ratio": cr, "interpretation": interp}


def calculate_quick_ratio(
    current_assets: float,
    inventories: float,
    current_liabilities: float,
) -> Dict[str, Any]:
    """Quick Ratio = (Current Assets - Inventories) / Current Liabilities"""
    if current_liabilities == 0:
        return {"ratio": None}
    qr = round((current_assets - inventories) / current_liabilities, 2)
    interp = "Good (≥ 1)" if qr >= 1 else "⚠️ May struggle to meet short-term obligations"
    return {"ratio": qr, "interpretation": interp}


# ============================================================
# LEVERAGE RATIOS
# ============================================================
def calculate_debt_to_equity(total_debt: float, shareholders_equity: float) -> Dict[str, Any]:
    """D/E Ratio = Total Debt / Shareholders' Equity"""
    if shareholders_equity == 0:
        return {"ratio": None}
    de = round(total_debt / shareholders_equity, 2)
    interp = "Conservative (< 0.5)" if de < 0.5 else ("Moderate (0.5–1)" if de < 1 else ("High (1–2)" if de < 2 else "⚠️ Very high leverage (> 2)"))
    return {"ratio": de, "interpretation": interp}


def calculate_interest_coverage(ebit: float, interest_expense: float) -> Dict[str, Any]:
    """Interest Coverage = EBIT / Interest Expense"""
    if interest_expense == 0:
        return {"ratio": None, "interpretation": "No interest expense (debt-free)"}
    ic = round(ebit / interest_expense, 2)
    interp = "Excellent (> 5x)" if ic > 5 else ("Good (3–5x)" if ic > 3 else ("Adequate (1.5–3x)" if ic > 1.5 else "⚠️ Risk of default (< 1.5x)"))
    return {"ratio": ic, "unit": "x", "interpretation": interp}


# ============================================================
# EFFICIENCY RATIOS
# ============================================================
def calculate_asset_turnover(revenue: float, total_assets: float) -> Dict[str, Any]:
    """Asset Turnover = Revenue / Total Assets"""
    if total_assets == 0:
        return {"ratio": None}
    at = round(revenue / total_assets, 2)
    return {"ratio": at, "interpretation": f"{at}x — higher is better for asset efficiency"}


def calculate_inventory_days(cogs: float, inventory: float) -> Dict[str, Any]:
    """Inventory Days = (Inventory / COGS) × 365"""
    if cogs == 0:
        return {"ratio": None}
    days = round((inventory / cogs) * 365, 1)
    interp = "Efficient (< 30 days)" if days < 30 else ("Good (30–60 days)" if days < 60 else ("Average (60–90 days)" if days < 90 else "⚠️ High inventory (> 90 days)"))
    return {"ratio": days, "unit": "days", "interpretation": interp}


# ============================================================
# GROWTH CALCULATIONS
# ============================================================
def calculate_cagr(start_value: float, end_value: float, years: float) -> Dict[str, Any]:
    """CAGR = ((End/Start)^(1/years) - 1) × 100"""
    if start_value <= 0 or years <= 0:
        return {"ratio": None, "error": "Invalid inputs"}
    cagr = round(((end_value / start_value) ** (1 / years) - 1) * 100, 2)
    return {"ratio": cagr, "unit": "%", "years": years}


def calculate_yoy_growth(current: float, previous: float) -> Dict[str, Any]:
    """Year-over-Year growth rate."""
    if previous == 0:
        return {"ratio": None, "error": "Previous value is zero"}
    growth = round(((current - previous) / abs(previous)) * 100, 2)
    return {"ratio": growth, "unit": "%", "trend": "↑ Growth" if growth > 0 else "↓ Decline"}


# ============================================================
# COMPREHENSIVE ANALYSIS
# ============================================================
def run_full_ratio_analysis(data: Dict[str, float]) -> Dict[str, Any]:
    """
    AutoGen Tool: Run all available ratio calculations from a data dict.

    Expected keys in data (all in same currency units, e.g., ₹ Crore):
        market_price, eps, book_value_per_share, market_cap,
        total_debt, cash, ebitda, shareholders_equity, net_income,
        ebit, revenue, gross_profit, current_assets, current_liabilities,
        inventories, total_assets, interest_expense, cogs
    """
    results = {}

    # Valuation
    if all(k in data for k in ["market_price", "eps"]):
        results["pe_ratio"] = calculate_pe_ratio(data["market_price"], data["eps"])
    if all(k in data for k in ["market_price", "book_value_per_share"]):
        results["pb_ratio"] = calculate_pb_ratio(data["market_price"], data["book_value_per_share"])

    # Profitability
    if all(k in data for k in ["net_income", "shareholders_equity"]):
        results["roe"] = calculate_roe(data["net_income"], data["shareholders_equity"])
    if all(k in data for k in ["revenue", "gross_profit", "ebitda", "ebit", "net_income"]):
        results["margins"] = calculate_margins(
            data["revenue"], data["gross_profit"],
            data["ebitda"], data["ebit"], data["net_income"]
        )

    # Liquidity
    if all(k in data for k in ["current_assets", "current_liabilities"]):
        results["current_ratio"] = calculate_current_ratio(data["current_assets"], data["current_liabilities"])

    # Leverage
    if all(k in data for k in ["total_debt", "shareholders_equity"]):
        results["debt_to_equity"] = calculate_debt_to_equity(data["total_debt"], data["shareholders_equity"])
    if all(k in data for k in ["ebit", "interest_expense"]):
        results["interest_coverage"] = calculate_interest_coverage(data["ebit"], data["interest_expense"])

    return {"analysis": results, "computed_ratios": list(results.keys())}
