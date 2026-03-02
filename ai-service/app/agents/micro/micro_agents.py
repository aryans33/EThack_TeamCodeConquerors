"""
AutoGen v0.7 — Micro Agents
10 specialized micro-agents:
  Valuation, Profitability, Liquidity, Leverage, Efficiency,
  News, Historical, Guidance, Sentiment, Financial Metrics

Each uses Gemini 1.5 Flash for speed/cost efficiency.
"""
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

from typing import Dict, Any, Optional
import logging
import asyncio

from app.config.settings import get_settings
from app.tools.yfinance_tool import (
    get_stock_info,
    get_financial_statements,
    get_historical_prices,
)
from app.tools.vector_rag_tool import rag_query
from app.tools.arithmetic_tool import (
    calculate_pe_ratio, calculate_pb_ratio, calculate_ev_ebitda,
    calculate_roe, calculate_roce, calculate_margins,
    calculate_current_ratio, calculate_quick_ratio,
    calculate_debt_to_equity, calculate_interest_coverage,
    calculate_asset_turnover, calculate_inventory_days,
    calculate_cagr, calculate_yoy_growth,
    run_full_ratio_analysis,
)

settings = get_settings()
logger = logging.getLogger(__name__)


def _flash_client():
    return OpenAIChatCompletionClient(
        model=settings.gemini_flash_model,
        api_key=settings.google_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model_info=ModelInfo(
            vision=True,
            function_calling=True,
            json_output=True,
            family="unknown",
            structured_output=True,
        ),
    )


# ============================================================
# MICRO AGENT 1: Valuation
# ============================================================
def create_valuation_agent() -> AssistantAgent:
    return AssistantAgent(
        name="ValuationAgent",
        model_client=_flash_client(),
        tools=[get_stock_info, calculate_pe_ratio, calculate_pb_ratio, calculate_ev_ebitda, rag_query],
        description="Calculates and interprets stock valuation metrics (P/E, P/B, EV/EBITDA, DCF).",
        system_message="""You are a valuation specialist for Indian equities.

Compute and interpret:
- P/E Ratio (trailing and forward)
- P/B Ratio (price to book)
- EV/EBITDA
- DCF fair value estimate (qualitative)
- PEG ratio (P/E to growth)

Compare to sector averages. Conclude with: Undervalued / Fairly Valued / Overvalued.
Format all values clearly with ₹ where applicable.""",
    )


# ============================================================
# MICRO AGENT 2: Profitability
# ============================================================
def create_profitability_agent() -> AssistantAgent:
    return AssistantAgent(
        name="ProfitabilityAgent",
        model_client=_flash_client(),
        tools=[get_financial_statements, calculate_roe, calculate_roce, calculate_margins],
        description="Analyzes profitability via ROE, ROCE, and margin trends.",
        system_message="""You are a profitability analyst for Indian companies.

Analyze:
- Revenue growth (YoY and 3-year CAGR)  
- Gross, EBITDA, EBIT, and Net Profit margins
- ROE and ROCE trends
- Quality of earnings (recurring vs one-time items)

Identify improving/deteriorating margin trends.
Provide a Profitability Score: Strong / Moderate / Weak.""",
    )


# ============================================================
# MICRO AGENT 3: Liquidity
# ============================================================
def create_liquidity_agent() -> AssistantAgent:
    return AssistantAgent(
        name="LiquidityAgent",
        model_client=_flash_client(),
        tools=[get_financial_statements, get_stock_info, calculate_current_ratio, calculate_quick_ratio],
        description="Assesses short-term liquidity and working capital management.",
        system_message="""You are a liquidity analyst.

Analyze:
- Current Ratio (target: > 1.5)
- Quick Ratio (target: > 1.0)
- Cash and cash equivalents
- Working capital cycle (receivables days, payables days)
- Operating cash flow coverage

Flag any liquidity concerns. Rate: Excellent / Good / Adequate / ⚠️ Concern.""",
    )


# ============================================================
# MICRO AGENT 4: Leverage
# ============================================================
def create_leverage_agent() -> AssistantAgent:
    return AssistantAgent(
        name="LeverageAgent",
        model_client=_flash_client(),
        tools=[get_financial_statements, get_stock_info, calculate_debt_to_equity, calculate_interest_coverage],
        description="Evaluates debt levels and financial leverage.",
        system_message="""You are a credit analyst assessing leverage.

Analyze:
- Debt-to-Equity ratio (D/E)
- Net Debt / EBITDA
- Interest Coverage Ratio
- Debt maturity profile (from annual reports)
- Credit rating (if available)
- Free cash flow for debt repayment

Rate leverage: Conservative / Moderate / High / ⚠️ Very High Risk.""",
    )


# ============================================================
# MICRO AGENT 5: Efficiency
# ============================================================
def create_efficiency_agent() -> AssistantAgent:
    return AssistantAgent(
        name="EfficiencyAgent",
        model_client=_flash_client(),
        tools=[get_financial_statements, calculate_asset_turnover, calculate_inventory_days],
        description="Measures operating efficiency and asset utilization.",
        system_message="""You are an operations analyst.

Analyze:
- Asset Turnover Ratio
- Inventory Turnover and Days
- Receivables Days Outstanding (DSO)
- Payable Days Outstanding (DPO)
- Cash Conversion Cycle
- Capex efficiency (Revenue / Gross Block)

Benchmark against industry norms for Indian companies.""",
    )


# ============================================================
# MICRO AGENT 6: News
# ============================================================
def create_news_agent() -> AssistantAgent:
    return AssistantAgent(
        name="NewsAgent",
        model_client=_flash_client(),
        tools=[rag_query, get_stock_info],
        description="Analyzes recent news and corporate announcements.",
        system_message="""You are a financial news analyst.

Analyze recent news, press releases, and corporate announcements for the company.

Focus on:
- Recent quarterly results and management commentary
- New orders, contracts, or business wins
- Regulatory announcements, SEBI filings
- Management changes
- Mergers, acquisitions, or strategic moves
- Any negative news (fraud allegations, legal issues, etc.)

Rate news sentiment: Positive / Neutral / Negative.""",
    )


# ============================================================
# MICRO AGENT 7: Historical Performance
# ============================================================
def create_historical_agent() -> AssistantAgent:
    return AssistantAgent(
        name="HistoricalAgent",
        model_client=_flash_client(),
        tools=[get_historical_prices, calculate_cagr, calculate_yoy_growth],
        description="Analyzes historical stock price performance and returns.",
        system_message="""You are a quantitative analyst studying historical performance.

Analyze:
- 1M, 3M, 6M, 1Y, 3Y, 5Y returns
- CAGR vs Nifty 50 benchmark
- Maximum drawdown periods
- Volatility (beta)
- Price correlation with sector

Provide context on: Has the stock been a wealth creator or destroyer?""",
    )


# ============================================================
# MICRO AGENT 8: Guidance
# ============================================================
def create_guidance_agent() -> AssistantAgent:
    return AssistantAgent(
        name="GuidanceAgent",
        model_client=_flash_client(),
        tools=[rag_query],
        description="Extracts management guidance and forward-looking statements from concall transcripts.",
        system_message="""You are a specialist in analyzing management guidance from concall transcripts.

Extract and evaluate:
- Revenue and margin guidance for current/next year
- Capex plans and project pipeline
- Order book status (for capital goods / infra companies)
- New product/market launches
- Cost reduction targets
- Management confidence vs historical delivery

Search concall transcripts and annual report chairman letters.
Assess: Is management guidance credible? Optimistic / Realistic / Conservative?""",
    )


# ============================================================
# MICRO AGENT 9: Sentiment
# ============================================================
def create_sentiment_agent() -> AssistantAgent:
    return AssistantAgent(
        name="SentimentAgent",
        model_client=_flash_client(),
        tools=[rag_query, get_stock_info],
        description="Aggregates sentiment from news, concalls, and analyst reports.",
        system_message="""You are a sentiment analyst for Indian stock markets.

Aggregate sentiment from:
1. Concall transcript tone (is management confident or hedging?)
2. News headlines and articles
3. Analyst consensus (buy/hold/sell ratings)
4. Social sentiment signals

Output:
- **Overall Sentiment Score**: Bullish / Neutral / Bearish (with score 1-10)
- **News Sentiment**: Positive/Negative headline count
- **Management Tone**: Optimistic / Cautious / Defensive
- **Analyst Consensus**: Majority recommendation""",
    )


# ============================================================
# MICRO AGENT 10: Financial Metrics Summary
# ============================================================
def create_financial_metrics_agent() -> AssistantAgent:
    return AssistantAgent(
        name="FinancialMetricsAgent",
        model_client=_flash_client(),
        tools=[get_stock_info, get_financial_statements, run_full_ratio_analysis],
        description="Generates a comprehensive financial metrics summary table.",
        system_message="""You are a financial data analyst.

Generate a COMPLETE METRICS TABLE for the company including:

| Metric | Value | Industry Avg | Rating |
|--------|-------|-------------|--------|

Include:
- All valuation ratios (P/E, P/B, EV/EBITDA)
- All profitability ratios (ROE, ROCE, margins)
- All liquidity ratios (CR, QR)
- All leverage ratios (D/E, Interest Coverage)
- All efficiency ratios (Asset Turnover)
- Growth rates (Revenue CAGR, EPS CAGR)
- Market data (Market Cap, 52W H/L, Beta)

Always compute actual values using run_full_ratio_analysis.""",
    )


# ============================================================
# MICRO AGENT REGISTRY
# ============================================================
MICRO_AGENT_FACTORY = {
    "valuation": create_valuation_agent,
    "profitability": create_profitability_agent,
    "liquidity": create_liquidity_agent,
    "leverage": create_leverage_agent,
    "efficiency": create_efficiency_agent,
    "news": create_news_agent,
    "historical": create_historical_agent,
    "guidance": create_guidance_agent,
    "sentiment": create_sentiment_agent,
    "financial_metrics": create_financial_metrics_agent,
}


async def run_micro_agent(
    agent_type: str,
    symbol: str,
    question: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a single micro agent for a given stock symbol.

    Args:
        agent_type: One of the MICRO_AGENT_FACTORY keys
        symbol: Stock symbol (e.g., 'TCS')
        question: Optional specific question

    Returns:
        Dict with analysis result
    """
    if agent_type not in MICRO_AGENT_FACTORY:
        return {
            "error": f"Unknown agent type: {agent_type}",
            "available": list(MICRO_AGENT_FACTORY.keys()),
        }

    try:
        agent = MICRO_AGENT_FACTORY[agent_type]()
        task = question or f"Perform a {agent_type} analysis for {symbol} listed on NSE/BSE."

        logger.info(f"🤖 Running {agent_type} micro-agent for {symbol}")
        result = await agent.run(task=task)

        content = ""
        if hasattr(result, "messages") and result.messages:
            last_msg = result.messages[-1]
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        else:
            content = str(result)

        return {
            "agent_type": agent_type,
            "symbol": symbol.upper(),
            "analysis": content,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Micro agent {agent_type} error for {symbol}: {e}")
        return {"agent_type": agent_type, "symbol": symbol, "status": "error", "error": str(e)}


async def run_all_micro_agents(symbol: str) -> Dict[str, Any]:
    """Run all 10 micro agents concurrently for maximum speed."""
    logger.info(f"🤖 Running ALL micro agents for {symbol}")

    tasks = [
        run_micro_agent(agent_type, symbol)
        for agent_type in MICRO_AGENT_FACTORY.keys()
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    results = {}
    for agent_type, result in zip(MICRO_AGENT_FACTORY.keys(), results_list):
        if isinstance(result, Exception):
            results[agent_type] = {"status": "error", "error": str(result)}
        else:
            results[agent_type] = result

    return {
        "symbol": symbol.upper(),
        "micro_analysis": results,
        "total_agents": len(MICRO_AGENT_FACTORY),
        "successful": sum(1 for r in results.values() if r.get("status") == "success"),
    }

