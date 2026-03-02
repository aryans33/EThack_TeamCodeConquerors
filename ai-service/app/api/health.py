from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """Main health check endpoint."""
    return {
        "success": True,
        "service": "FinAnalysis AI Service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.get("/detailed")
async def detailed_health():
    """Detailed health with system metrics."""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return {
            "success": True,
            "service": "FinAnalysis AI Service",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total_mb": round(memory.total / (1024 ** 2), 2),
                "memory_used_mb": round(memory.used / (1024 ** 2), 2),
                "memory_percent": memory.percent,
            },
        }
    except Exception as e:
        return {
            "success": True,
            "service": "FinAnalysis AI Service",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "System metrics unavailable",
        }
