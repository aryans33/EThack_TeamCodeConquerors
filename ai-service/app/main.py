from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.config.settings import get_settings
from app.api import health
from app.api import stocks
from app.api import documents
from app.api import analysis
from app.api import reasoning

# ============================================
# Setup Logging
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================
# Create FastAPI App
# ============================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## 🤖 FinAnalysis AI Service

AI-powered financial analysis for Indian stock markets.

### Tech Stack:
- **AutoGen v0.7** — Multi-agent orchestration
- **Gemini 1.5 Pro / Flash** — LLM backbone
- **ChromaDB** — Vector store (Gemini embeddings)
- **Mistral OCR** — PDF text extraction  
- **MongoDB** — Document chunk storage
- **yfinance** — Live market data (NSE/BSE)

### Architecture:
```
PDFs → Mistral OCR → MongoDB (chunks) → Gemini Embeddings → ChromaDB
yfinance → Live stock data
ChromaDB + yfinance → AutoGen Tools → Macro/Micro Agents → Analysis
```

### Agents:
- **Macro**: Business, Financial, Market, Risk
- **Micro**: Valuation, Profitability, Liquidity, Leverage, Efficiency,
  News, Historical, Guidance, Sentiment, Financial Metrics
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================
# CORS MIDDLEWARE
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============================================
# REQUEST TIMING MIDDLEWARE
# ============================================
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    if request.url.path != "/health":
        logger.info(f"{request.method} {request.url.path} — {response.status_code} ({process_time:.2f}s)")
    return response

# ============================================
# GLOBAL EXCEPTION HANDLER
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error" if settings.environment == "production" else str(exc),
        },
    )

# ============================================
# STARTUP EVENT — Initialize services
# ============================================
@app.on_event("startup")
async def startup_event():
    logger.info(f"""
╔═══════════════════════════════════════════════════╗
║   🤖 FinAnalysis AI Service                       ║
║   🔧 Stack : AutoGen v0.7 + Gemini + ChromaDB     ║
║   📡 Port  : {settings.port}                             ║
║   🌍 Env   : {settings.environment}                      ║
║   📖 Docs  : http://localhost:{settings.port}/docs        ║
╚═══════════════════════════════════════════════════╝
    """)

    # Initialize MongoDB indexes
    try:
        from app.services.mongo.mongo_service import get_mongo_service
        mongo = await get_mongo_service()
        logger.info("✅ MongoDB service initialized")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB init error: {e}")

    # Initialize ChromaDB
    try:
        from app.services.vector_store.chroma_service import get_vector_store
        vs = get_vector_store()
        logger.info("✅ ChromaDB service initialized")
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB init error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AI Service shutting down...")

# ============================================
# INCLUDE ROUTERS
# ============================================
app.include_router(health.router, tags=["Health"])
app.include_router(stocks.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(reasoning.router)

# ============================================
# ROOT ROUTE
# ============================================
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "🤖 FinAnalysis AI Service",
        "stack": "AutoGen v0.7 + Gemini 1.5 + ChromaDB + MongoDB + yfinance",
        "docs": "/docs",
        "health": "/health",
        "version": settings.app_version,
        "endpoints": {
            "stocks": "/api/v1/stocks/{symbol}",
            "documents": "/api/v1/documents/upload",
            "analysis_rag": "/api/v1/analysis/rag-query",
            "analysis_micro": "/api/v1/analysis/micro/{agent_type}",
            "analysis_macro": "/api/v1/analysis/macro/{symbol}",
            "analysis_full": "/api/v1/analysis/full/{symbol}",
            "reasoning_thesis": "/api/v1/reasoning/investment-thesis/{symbol}",
            "reasoning_compare": "/api/v1/reasoning/compare",
            "reasoning_sector": "/api/v1/reasoning/sector",
            "reasoning_risk": "/api/v1/reasoning/risk/{symbol}",
            "reasoning_summary": "/api/v1/reasoning/summary/{symbol}",
            "reasoning_ask": "/api/v1/reasoning/ask",
        }
    }
