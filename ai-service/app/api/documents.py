"""
FastAPI Router — Document Ingestion Pipeline
POST /api/v1/documents/upload
  1. Receive PDF file
  2. Mistral OCR → JSON chunks
  3. Store chunks in MongoDB
  4. Gemini embeddings → ChromaDB
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import logging
import asyncio

from app.services.ocr.mistral_ocr import get_ocr_service
from app.services.vector_store.chroma_service import get_vector_store
from app.services.mongo.mongo_service import get_mongo_service
from app.middleware.auth import verify_internal_api_key

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


ALLOWED_DOC_TYPES = ["annual_report", "concall", "fund_report", "investor_presentation", "quarterly_results"]
MAX_FILE_SIZE_MB = 50


# ============================================================
# BACKGROUND TASK: Full ingestion pipeline
# ============================================================
async def ingest_document_pipeline(
    doc_id: str,
    symbol: str,
    doc_type: str,
    pdf_bytes: bytes,
    filename: str,
):
    """
    Background task that runs the full ingestion pipeline:
    PDF bytes → Mistral OCR → MongoDB → ChromaDB
    """
    mongo = await get_mongo_service()

    try:
        # Step 1: Update status to processing
        await mongo.update_document_status(doc_id, "processing")
        logger.info(f"[{doc_id}] Starting OCR for {symbol} / {doc_type}")

        # Step 2: Mistral OCR
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.process_pdf_bytes(
            pdf_bytes=pdf_bytes,
            doc_id=doc_id,
            symbol=symbol,
            doc_type=doc_type,
        )

        chunks = ocr_result["chunks"]
        logger.info(f"[{doc_id}] OCR complete: {len(chunks)} chunks, {ocr_result['total_pages']} pages")

        # Step 3: Store chunks in MongoDB
        await mongo.store_document_chunks(
            symbol=symbol,
            doc_id=doc_id,
            chunks=chunks,
            doc_type=doc_type,
        )

        # Step 4: Vectorize and store in ChromaDB
        vector_store = get_vector_store()

        # Prepare data for ChromaDB
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]

        if documents:
            added = vector_store.add_documents(
                symbol=symbol,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"[{doc_id}] ChromaDB: {added} vectors stored")

        # Step 5: Mark as complete
        await mongo.update_document_status(
            doc_id, "vectorized", chunk_count=len(chunks)
        )
        logger.info(f"✅ [{doc_id}] Pipeline complete for {symbol}")

    except Exception as e:
        logger.error(f"❌ [{doc_id}] Pipeline failed: {e}")
        await mongo.update_document_status(doc_id, "failed", error=str(e))


# ============================================================
# ROUTES
# ============================================================

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    symbol: str = Form(...),
    doc_type: str = Form(default="annual_report"),
    user_id: Optional[str] = Form(default=None),
):
    """
    Upload a PDF document for OCR and vectorization.

    - **file**: PDF file (max 50MB)
    - **symbol**: Indian stock symbol (e.g., RELIANCE, TCS)
    - **doc_type**: Type of document (annual_report, concall, fund_report, etc.)

    The pipeline runs in the background:
    1. Mistral OCR extracts text
    2. Chunks stored in MongoDB
    3. Gemini embeddings → ChromaDB
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Validate doc_type
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doc_type. Allowed: {ALLOWED_DOC_TYPES}"
        )

    # Read file bytes
    pdf_bytes = await file.read()
    file_size_mb = len(pdf_bytes) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size_mb:.1f}MB). Max: {MAX_FILE_SIZE_MB}MB"
        )

    # Create document record in MongoDB
    mongo = await get_mongo_service()
    doc_id = await mongo.create_document_record(
        symbol=symbol.upper(),
        filename=file.filename,
        doc_type=doc_type,
        user_id=user_id,
    )

    # Start background ingestion pipeline
    background_tasks.add_task(
        ingest_document_pipeline,
        doc_id=doc_id,
        symbol=symbol.upper(),
        doc_type=doc_type,
        pdf_bytes=pdf_bytes,
        filename=file.filename,
    )

    return JSONResponse(
        status_code=202,
        content={
            "success": True,
            "message": "Document uploaded. Processing started in background.",
            "doc_id": doc_id,
            "symbol": symbol.upper(),
            "doc_type": doc_type,
            "filename": file.filename,
            "file_size_mb": round(file_size_mb, 2),
            "status": "processing",
            "check_status_url": f"/api/v1/documents/{doc_id}/status",
        }
    )


@router.get("/{doc_id}/status")
async def get_document_status(doc_id: str):
    """Check the processing status of an uploaded document."""
    mongo = await get_mongo_service()
    docs = await mongo.documents.find_one({"_id": __import__("bson").ObjectId(doc_id)})
    if not docs:
        raise HTTPException(status_code=404, detail="Document not found.")
    docs["_id"] = str(docs["_id"])
    return {"success": True, "document": docs}


@router.get("/symbol/{symbol}")
async def get_documents_for_symbol(symbol: str):
    """List all documents uploaded for a company symbol."""
    mongo = await get_mongo_service()
    docs = await mongo.get_documents_for_symbol(symbol.upper())
    vector_store = get_vector_store()
    stats = vector_store.get_collection_stats(symbol)

    return {
        "success": True,
        "symbol": symbol.upper(),
        "documents": docs,
        "total_documents": len(docs),
        "vector_store": stats,
    }


@router.get("/symbol/{symbol}/chunks")
async def get_chunks_preview(symbol: str, limit: int = 20):
    """Preview stored chunks for a company (for debugging)."""
    mongo = await get_mongo_service()
    chunks = await mongo.get_chunks_for_symbol(symbol.upper(), limit=limit)
    return {
        "success": True,
        "symbol": symbol.upper(),
        "chunks": chunks,
        "count": len(chunks),
    }
