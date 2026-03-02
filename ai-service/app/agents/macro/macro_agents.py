"""
AutoGen v0.7 — Macro Agents
Business, Financial, Market, and Risk macro agents.
Each uses AssistantAgent with Gemini 1.5 Pro as the LLM backbone.
"""
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

from typing import Dict, Any, Optional
import asyncio
import logging

from app.config.settings import get_settings
from app.tools.yfinance_tool import get_stock_info, get_financial_statements, get_historical_prices
from app.tools.vector_rag_tool import rag_query
from app.tools.arithmetic_tool import run_full_ratio_analysis

settings = get_settings()
logger = logging.getLogger(__name__)


# ============================================================
# Shared Gemini Model Client for AutoGen
# ============================================================
def get_gemini_model_client(use_flash: bool = False):
    """
    Returns an OpenAIChatCompletionClient configured for Google Gemini.
    Using Gemini's OpenAI-compatible API (beta) as per official AutoGen docs:
    https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/models.html
    """
    model = settings.gemini_flash_model if use_flash else settings.gemini_model
    return OpenAIChatCompletionClient(
        model=model,
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
# MACRO AGENT 1: Business Analyst Agent
# Analyzes the company's business model, competitive moat, and strategy
# ============================================================
def create_business_agent() -> AssistantAgent:
    return AssistantAgent(
        name="BusinessAnalystAgent",
        model_client=get_gemini_model_client(use_flash=False),
        tools=[rag_query, get_stock_info],
        description="Analyzes the company's business model, competitive advantages, and strategic positioning.",
        system_message="""You are a senior business analyst specializing in Indian companies.

Your role: Analyze the BUSINESS MODEL of the company.

Focus on:
1. Business segments and revenue mix
2. Competitive moat (brand, patents, switching costs, network effects)
3. Key customers and markets served
4. Management quality and corporate governance
5. Strategic initiatives and growth plans from concall transcripts

Use the rag_query tool to search annual reports and concall transcripts.
Use get_stock_info to get current market context.

Always structure your output as:
- **Business Overview**: Core business description
- **Revenue Segments**: Breakdown of business units
- **Competitive Moat**: Sustainable advantages
- **Management**: Key leadership and track record  
- **Strategy**: Near-term and long-term plans
- **Risks to Business Model**: Business-specific risks

Be precise with numbers (₹ Crore format for India) and cite sources.""",
    )


# ============================================================
# MACRO AGENT 2: Financial Analyst Agent
# Evaluates financial performance and health
# ============================================================
def create_financial_agent() -> AssistantAgent:
    return AssistantAgent(
        name="FinancialAnalystAgent",
        model_client=get_gemini_model_client(use_flash=False),
        tools=[get_stock_info, get_financial_statements, run_full_ratio_analysis, rag_query],
        description="Evaluates financial performance including P&L, balance sheet, cash flows, and key ratios.",
        system_message="""You are a CFA-level financial analyst specializing in Indian equities.

Your role: Evaluate FINANCIAL PERFORMANCE and health.

Focus on:
1. Revenue growth trajectory (3-5 year CAGR)
2. Profitability trends (EBITDA margin, net margin evolution)
3. Return metrics (ROE, ROCE, ROA)
4. Balance sheet health (debt levels, working capital)
5. Cash flow quality (FCF generation, capex intensity)
6. Dividend history and payout policy

Tools to use:
- get_financial_statements: For P&L, BS, cash flow data
- get_stock_info: For current ratios and market data
- run_full_ratio_analysis: To compute all financial ratios
- rag_query: To extract specific data from annual reports

Structure your output as:
- **Revenue & Growth**: Top-line trends
- **Profitability**: Margin analysis
- **Return Ratios**: ROE, ROCE trends
- **Balance Sheet**: Debt, liquidity analysis
- **Cash Flows**: FCF quality
- **Key Ratios Summary**: P/E, P/B, EV/EBITDA

Use ₹ Crore for all monetary values.""",
    )


# ============================================================
# MACRO AGENT 3: Market Analyst Agent
# Assesses market trends, technical factors, and sector dynamics
# ============================================================
def create_market_agent() -> AssistantAgent:
    return AssistantAgent(
        name="MarketAnalystAgent",
        model_client=get_gemini_model_client(use_flash=False),
        tools=[get_stock_info, get_historical_prices, rag_query],
        description="Assesses market trends, technical price action, and sector dynamics.",
        system_message="""You are a market analyst covering Indian equity markets (NSE/BSE).

Your role: Assess MARKET TRENDS and positioning.

Focus on:
1. Current stock price vs 52-week high/low
2. Price performance vs Nifty 50 / sector index
3. Valuation vs historical averages
4. Sector tailwinds and headwinds
5. Institutional holdings and FII/DII activity
6. Technical levels (support/resistance) from price history

Tools to use:
- get_historical_prices: For 1y/5y price data and returns
- get_stock_info: For current price, 52-week range, beta
- rag_query: For management guidance and outlook

Structure your output as:
- **Price Action**: Recent price trends and returns
- **Relative Performance**: Vs benchmark
- **Valuation Context**: Current vs historical
- **Sector Dynamics**: Industry tailwinds/headwinds
- **Technical Overview**: Key levels
- **Institutional Activity**: FII/DII flow if available""",
    )


# ============================================================
# MACRO AGENT 4: Risk Analyst Agent
# Identifies and analyzes all risk factors
# ============================================================
def create_risk_agent() -> AssistantAgent:
    return AssistantAgent(
        name="RiskAnalystAgent",
        model_client=get_gemini_model_client(use_flash=False),
        tools=[get_stock_info, get_financial_statements, rag_query],
        description="Identifies and analyzes business, financial, regulatory, and market risks.",
        system_message="""You are a risk analyst specializing in Indian equity investment risks.

Your role: Identify and analyze ALL RISKS for the investment.

Focus on:
1. Business risks (competition, disruption, customer concentration)
2. Financial risks (leverage, liquidity, currency exposure)
3. Regulatory risks (SEBI, sector regulations, government policy)
4. Macro risks (interest rates, inflation, INR depreciation)
5. ESG risks (environmental, social, governance concerns)
6. Execution risks (project delays, cost overruns)

Tools to use:
- rag_query: Search for "risk factors" in annual reports and concalls
- get_financial_statements: For leverage/liquidity assessment
- get_stock_info: For beta and market sensitivity

Structure your output as:
- **High Risk Factors**: Critical risks (🔴)
- **Medium Risk Factors**: Notable concerns (🟡)
- **Low Risk Factors**: Minor risks (🟢)
- **Risk Mitigation**: How company addresses each risk
- **Overall Risk Rating**: Conservative/Moderate/Aggressive

Be thorough — surface non-obvious risks from document analysis.""",
    )


# ============================================================
# ORCHESTRATOR: Run all 4 macro agents on a symbol
# ============================================================
async def run_macro_analysis(symbol: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Orchestrate all 4 macro agents to produce a comprehensive company analysis.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        context: Optional user question or focus area

    Returns:
        Dict with each agent's analysis
    """
    logger.info(f"🤖 Starting macro agent analysis for {symbol}")

    question = context or f"Provide a comprehensive analysis of {symbol} for investment decision-making."

    results = {}

    # Run agents sequentially to avoid API rate limits
    agents_and_names = [
        ("business", create_business_agent),
        ("financial", create_financial_agent),
        ("market", create_market_agent),
        ("risk", create_risk_agent),
    ]

    for agent_name, agent_factory in agents_and_names:
        try:
            agent = agent_factory()
            logger.info(f"Running {agent_name} agent for {symbol}...")

            # Run single-agent analysis
            result = await agent.run(task=f"Analyze {symbol}. {question}")

            # Extract text response
            if hasattr(result, "messages") and result.messages:
                last_msg = result.messages[-1]
                content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            else:
                content = str(result)

            results[agent_name] = {
                "status": "success",
                "analysis": content,
                "agent": agent.name,
            }
            logger.info(f"✅ {agent_name} agent complete for {symbol}")

        except Exception as e:
            logger.error(f"❌ {agent_name} agent error for {symbol}: {e}")
            results[agent_name] = {
                "status": "error",
                "analysis": f"Analysis failed: {str(e)}",
                "agent": agent_name,
            }

    return {
        "symbol": symbol.upper(),
        "macro_analysis": results,
        "completed_agents": [k for k, v in results.items() if v["status"] == "success"],
    }
