"""
FastAPI Router — Agent Analysis
Run macro agents, micro agents, and RAG queries.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import asyncio

from app.agents.macro.macro_agents import run_macro_analysis
from app.agents.micro.micro_agents import run_micro_agent, run_all_micro_agents, MICRO_AGENT_FACTORY
from app.tools.vector_rag_tool import rag_query
from app.services.mongo.mongo_service import get_mongo_service

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])
logger = logging.getLogger(__name__)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================
class RAGQueryRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol e.g. RELIANCE")
    question: str = Field(..., description="Natural language question about the company")
    n_context_chunks: int = Field(default=5, ge=1, le=15)
    doc_type_filter: Optional[str] = Field(default=None)


class MicroAgentRequest(BaseModel):
    symbol: str
    agent_type: str = Field(..., description=f"One of: {list(MICRO_AGENT_FACTORY.keys())}")
    question: Optional[str] = None


class MacroAnalysisRequest(BaseModel):
    symbol: str
    context: Optional[str] = None


# ============================================================
# RAG QUERY (Document Q&A)
# ============================================================
@router.post("/rag-query")
async def run_rag_query(request: RAGQueryRequest):
    """
    Ask any question about a company's documents using Gemini RAG.

    The system retrieves relevant chunks from ChromaDB and generates
    an answer using Gemini 1.5 Pro.

    **Example questions:**
    - "What is the revenue guidance for FY25?"
    - "What are the key risks mentioned in the annual report?"
    - "What is the total debt and interest coverage ratio?"
    """
    result = rag_query(
        symbol=request.symbol,
        question=request.question,
        n_context_chunks=request.n_context_chunks,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {"success": True, **result}


# ============================================================
# MICRO AGENTS
# ============================================================
@router.post("/micro/{agent_type}")
async def run_single_micro_agent(agent_type: str, symbol: str, question: Optional[str] = None):
    """
    Run a single micro-agent for a stock symbol.

    **Available agent types:**
    valuation, profitability, liquidity, leverage, efficiency,
    news, historical, guidance, sentiment, financial_metrics
    """
    if agent_type not in MICRO_AGENT_FACTORY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent type. Available: {list(MICRO_AGENT_FACTORY.keys())}"
        )

    result = await run_micro_agent(agent_type=agent_type, symbol=symbol, question=question)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))

    return {"success": True, **result}


@router.post("/micro/all/{symbol}")
async def run_all_micro(symbol: str):
    """
    Run ALL 10 micro-agents concurrently for a company.
    This is the comprehensive micro-analysis endpoint.
    Returns Valuation, Profitability, Liquidity, Leverage,
    Efficiency, News, Historical, Guidance, Sentiment, Financial Metrics.
    """
    result = await run_all_micro_agents(symbol=symbol)
    return {"success": True, **result}


# ============================================================
# MACRO AGENTS
# ============================================================
@router.post("/macro/{symbol}")
async def run_macro(symbol: str, context: Optional[str] = None):
    """
    Run all 4 macro agents (Business, Financial, Market, Risk)
    for a comprehensive company analysis.

    Uses Gemini 1.5 Pro for deep analysis.
    """
    result = await run_macro_analysis(symbol=symbol, context=context)
    return {"success": True, **result}


# ============================================================
# FULL ANALYSIS (Macro + Micro together)
# ============================================================
@router.post("/full/{symbol}")
async def run_full_analysis(symbol: str):
    """
    Run the COMPLETE analysis suite:
    - All 4 Macro Agents
    - All 10 Micro Agents
    - Cache the result in MongoDB

    This is the most comprehensive and time-intensive endpoint.
    """
    logger.info(f"🚀 Full analysis started for {symbol}")

    # Run macro and micro agents concurrently
    macro_task = run_macro_analysis(symbol=symbol)
    micro_task = run_all_micro_agents(symbol=symbol)

    macro_result, micro_result = await asyncio.gather(macro_task, micro_task)

    full_result = {
        "symbol": symbol.upper(),
        "macro_analysis": macro_result.get("macro_analysis", {}),
        "micro_analysis": micro_result.get("micro_analysis", {}),
        "summary": {
            "macro_agents_run": len(macro_result.get("completed_agents", [])),
            "micro_agents_run": micro_result.get("successful", 0),
            "total_agents": 14,
        },
    }

    # Cache in MongoDB
    try:
        mongo = await get_mongo_service()
        await mongo.cache_analysis(symbol, "full_analysis", full_result)
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")

    return {"success": True, **full_result}


# ============================================================
# GET CACHED ANALYSIS
# ============================================================
@router.get("/cache/{symbol}/{analysis_type}")
async def get_cached_analysis_result(symbol: str, analysis_type: str):
    """Retrieve cached analysis result from MongoDB."""
    mongo = await get_mongo_service()
    cached = await mongo.get_cached_analysis(symbol, analysis_type)
    if not cached:
        raise HTTPException(status_code=404, detail="No cached analysis found.")
    return {"success": True, "cached": True, **cached}
