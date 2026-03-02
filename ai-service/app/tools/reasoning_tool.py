"""
AutoGen Tools — Reasoning Tool
Chain-of-thought financial reasoning using Gemini.
Used by agents to synthesize findings from multiple data sources
into a structured investment thesis.
"""
from google import genai
from google.genai import types as genai_types
from typing import Dict, Any, List, Optional
import logging
import json

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Reasoning prompts for different analysis types
REASONING_PROMPTS = {
    "investment_thesis": """You are a senior equity research analyst.
Based on the provided financial data, generate a structured investment thesis.

Data provided:
{data}

Generate a well-reasoned investment thesis covering:
1. **Bull Case** (3 key reasons to buy)
2. **Bear Case** (3 key risks)
3. **Base Case** (most likely scenario)
4. **Verdict**: Strong Buy / Buy / Hold / Sell / Strong Sell
5. **Target Price Range** (if data available)
6. **Investment Horizon**: Short (< 1yr) / Medium (1-3yr) / Long (> 3yr)

Use ₹ Crore for Indian market values. Be concise and evidence-based.""",

    "compare_stocks": """You are a portfolio manager comparing Indian stocks.

Stock data:
{data}

Compare these stocks and recommend:
1. **Ranking**: Best to Worst (with reasons)
2. **Key differentiators** between them
3. **Best for**: Value investor / Growth investor / Dividend investor
4. **Risks** specific to each stock
5. **Final allocation suggestion** (e.g., 60% Stock A, 40% Stock B)""",

    "sector_analysis": """You are a sector analyst for Indian markets.

Data:
{data}

Analyze the sector and provide:
1. **Sector Outlook**: Bullish / Neutral / Bearish
2. **Key Sector Drivers** (tailwinds)
3. **Key Headwinds** (risks)
4. **Best positioned companies** in the sector
5. **Regulatory or macro factors** affecting the sector
6. **Investment strategy** for this sector""",

    "risk_assessment": """You are a risk manager for an Indian equity portfolio.

Data:
{data}

Provide a comprehensive risk assessment:
1. **Risk Score**: 1-10 (1=very low, 10=very high)
2. **Business Risks**: Operational and competitive risks
3. **Financial Risks**: Leverage, liquidity, earnings quality
4. **Market Risks**: Beta, volatility, valuation risk
5. **Regulatory/ESG Risks**: Governance, compliance issues
6. **Risk Mitigation**: How to protect portfolio from these risks""",

    "financial_summary": """You are a financial analyst summarizing key metrics.

Financial data:
{data}

Provide a concise financial summary:
1. **Revenue & Growth**: Top-line performance
2. **Profitability**: Margin analysis
3. **Returns**: ROE, ROCE assessment
4. **Balance Sheet**: Debt and liquidity health
5. **Valuation**: Fair/expensive/cheap with rationale
6. **Overall Financial Health Score**: A / B / C / D / F""",
}


class ReasoningTool:
    """
    AutoGen Reasoning Tool using Gemini for chain-of-thought analysis.
    Synthesizes multiple data points into structured financial insights.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_model
        logger.info("✅ Reasoning Tool initialized")

    def _call_gemini(self, prompt: str, temperature: float = 0.1) -> str:
        """Call Gemini with a prompt and return text response."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=4096,
                ),
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini reasoning error: {e}")
            return f"Reasoning failed: {str(e)}"

    def generate_investment_thesis(
        self,
        symbol: str,
        financial_data: Dict[str, Any],
        analysis_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Generate a complete investment thesis for a stock.

        Args:
            symbol: Stock symbol
            financial_data: Dict from yfinance (ratios, prices, etc.)
            analysis_data: Optional dict of agent analysis results

        Returns:
            Dict with structured investment thesis
        """
        combined_data = {"symbol": symbol, "market_data": financial_data}
        if analysis_data:
            combined_data["agent_analysis"] = analysis_data

        data_str = json.dumps(combined_data, indent=2, default=str)
        prompt = REASONING_PROMPTS["investment_thesis"].format(data=data_str)

        thesis = self._call_gemini(prompt, temperature=0.2)

        return {
            "symbol": symbol,
            "reasoning_type": "investment_thesis",
            "thesis": thesis,
            "model_used": self.model,
        }

    def compare_stocks(
        self,
        stocks_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Compare multiple stocks and recommend allocation.

        Args:
            stocks_data: List of stock info dicts

        Returns:
            Dict with comparison and recommendation
        """
        data_str = json.dumps(stocks_data, indent=2, default=str)
        prompt = REASONING_PROMPTS["compare_stocks"].format(data=data_str)

        comparison = self._call_gemini(prompt, temperature=0.1)

        return {
            "stocks": [s.get("symbol", "N/A") for s in stocks_data],
            "reasoning_type": "compare_stocks",
            "comparison": comparison,
            "model_used": self.model,
        }

    def sector_analysis(
        self,
        sector: str,
        stocks_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Analyze an entire market sector.

        Args:
            sector: Sector name (e.g., 'Banking', 'IT', 'Pharma')
            stocks_data: List of stocks in the sector

        Returns:
            Dict with sector analysis
        """
        data = {"sector": sector, "stocks": stocks_data}
        data_str = json.dumps(data, indent=2, default=str)
        prompt = REASONING_PROMPTS["sector_analysis"].format(data=data_str)

        analysis = self._call_gemini(prompt, temperature=0.1)

        return {
            "sector": sector,
            "reasoning_type": "sector_analysis",
            "analysis": analysis,
            "model_used": self.model,
        }

    def assess_risk(
        self,
        symbol: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Comprehensive risk assessment for a stock.

        Args:
            symbol: Stock symbol
            data: Combined financial and market data

        Returns:
            Dict with risk assessment
        """
        data_str = json.dumps({"symbol": symbol, **data}, indent=2, default=str)
        prompt = REASONING_PROMPTS["risk_assessment"].format(data=data_str)

        assessment = self._call_gemini(prompt, temperature=0.0)

        return {
            "symbol": symbol,
            "reasoning_type": "risk_assessment",
            "assessment": assessment,
            "model_used": self.model,
        }

    def financial_summary(
        self,
        symbol: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Generate a concise financial summary.

        Args:
            symbol: Stock symbol
            data: Financial metrics dict

        Returns:
            Dict with financial summary
        """
        data_str = json.dumps({"symbol": symbol, **data}, indent=2, default=str)
        prompt = REASONING_PROMPTS["financial_summary"].format(data=data_str)

        summary = self._call_gemini(prompt, temperature=0.0)

        return {
            "symbol": symbol,
            "reasoning_type": "financial_summary",
            "summary": summary,
            "model_used": self.model,
        }

    def custom_reasoning(
        self,
        question: str,
        context_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Free-form reasoning on any financial question.

        Args:
            question: The analytical question to answer
            context_data: Any relevant data as context

        Returns:
            Dict with reasoned answer
        """
        data_str = json.dumps(context_data, indent=2, default=str)

        prompt = f"""You are an expert financial analyst for Indian markets.

Context data:
{data_str}

Question: {question}

Provide a thorough, evidence-based answer using the context data above.
Format your response clearly with sections if needed.
Use ₹ Crore for monetary values."""

        answer = self._call_gemini(prompt, temperature=0.2)

        return {
            "question": question,
            "reasoning_type": "custom",
            "answer": answer,
            "model_used": self.model,
        }


# Singleton
_reasoning_tool: Optional[ReasoningTool] = None


def get_reasoning_tool() -> ReasoningTool:
    global _reasoning_tool
    if _reasoning_tool is None:
        _reasoning_tool = ReasoningTool()
    return _reasoning_tool


# ============================================================
# Standalone functions for AutoGen tool registration
# ============================================================
def generate_investment_thesis(
    symbol: str,
    financial_data: Dict[str, Any],
    analysis_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """AutoGen Tool: Generate investment thesis for a stock."""
    return get_reasoning_tool().generate_investment_thesis(symbol, financial_data, analysis_data)


def compare_stocks_reasoning(stocks_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """AutoGen Tool: Compare multiple stocks."""
    return get_reasoning_tool().compare_stocks(stocks_data)


def assess_stock_risk(symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """AutoGen Tool: Risk assessment for a stock."""
    return get_reasoning_tool().assess_risk(symbol, data)


def get_financial_summary(symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """AutoGen Tool: Concise financial summary."""
    return get_reasoning_tool().financial_summary(symbol, data)


def custom_financial_reasoning(question: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """AutoGen Tool: Free-form financial reasoning."""
    return get_reasoning_tool().custom_reasoning(question, context_data)
