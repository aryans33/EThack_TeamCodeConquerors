"""
MongoDB Service
Handles storage and retrieval of:
  - JSON chunks from OCR (raw document data)
  - Document metadata (upload history, processing status)
  - Analysis reports cache
"""
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING, IndexModel
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class MongoService:
    """
    Async MongoDB service using Motor.
    Manages collections:
      - document_chunks  : OCR'd text chunks with metadata
      - documents        : Document upload/processing records
      - analysis_cache   : Cached analysis reports
    """

    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.mongodb_db_name]

        # Collections
        self.document_chunks = self.db["document_chunks"]
        self.documents = self.db["documents"]
        self.analysis_cache = self.db["analysis_cache"]

    async def initialize_indexes(self):
        """Create indexes for performance. Call on app startup."""
        try:
            # document_chunks indexes
            await self.document_chunks.create_indexes([
                IndexModel([("symbol", ASCENDING)]),
                IndexModel([("doc_id", ASCENDING)]),
                IndexModel([("doc_type", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
            ])

            # documents indexes
            await self.documents.create_indexes([
                IndexModel([("symbol", ASCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("upload_date", DESCENDING)]),
                IndexModel([("user_id", ASCENDING)]),
            ])

            # analysis_cache: TTL index (auto-delete after ANALYSIS_CACHE_TTL seconds)
            await self.analysis_cache.create_indexes([
                IndexModel([("symbol", ASCENDING), ("analysis_type", ASCENDING)]),
                IndexModel(
                    [("created_at", ASCENDING)],
                    expireAfterSeconds=settings.analysis_cache_ttl
                ),
            ])

            logger.info("✅ MongoDB indexes created")
        except Exception as e:
            logger.error(f"MongoDB index creation error: {e}")

    # ====================================================
    # DOCUMENT CHUNKS (JSON chunks from Mistral OCR)
    # ====================================================
    async def store_document_chunks(
        self,
        symbol: str,
        doc_id: str,
        chunks: List[Dict[str, Any]],
        doc_type: str = "annual_report",
    ) -> int:
        """
        Store OCR'd JSON chunks for a document in MongoDB.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            doc_id: Unique document ID
            chunks: List of chunk dicts [{"text": ..., "page": ..., "chunk_index": ...}]
            doc_type: Type of document (annual_report, concall, fund_report, etc.)

        Returns:
            Number of chunks stored
        """
        records = []
        for i, chunk in enumerate(chunks):
            records.append({
                "symbol": symbol.upper(),
                "doc_id": doc_id,
                "doc_type": doc_type,
                "chunk_index": chunk.get("chunk_index", i),
                "page_number": chunk.get("page", None),
                "text": chunk.get("text", ""),
                "char_count": len(chunk.get("text", "")),
                "metadata": chunk.get("metadata", {}),
                "created_at": datetime.utcnow(),
            })

        if records:
            await self.document_chunks.insert_many(records, ordered=False)
            logger.info(f"✅ Stored {len(records)} chunks for {symbol} doc_id={doc_id}")

        return len(records)

    async def get_chunks_for_document(self, doc_id: str) -> List[Dict]:
        """Retrieve all chunks for a specific document."""
        cursor = self.document_chunks.find(
            {"doc_id": doc_id},
            sort=[("chunk_index", ASCENDING)]
        )
        chunks = await cursor.to_list(length=None)
        for c in chunks:
            c["_id"] = str(c["_id"])
        return chunks

    async def get_chunks_for_symbol(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Retrieve latest chunks for a company symbol."""
        cursor = self.document_chunks.find(
            {"symbol": symbol.upper()},
            sort=[("created_at", DESCENDING)],
            limit=limit
        )
        chunks = await cursor.to_list(length=limit)
        for c in chunks:
            c["_id"] = str(c["_id"])
        return chunks

    # ====================================================
    # DOCUMENTS (Upload & processing records)
    # ====================================================
    async def create_document_record(
        self,
        symbol: str,
        filename: str,
        doc_type: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Create a document record on upload. Returns doc_id."""
        doc = {
            "symbol": symbol.upper(),
            "filename": filename,
            "doc_type": doc_type,
            "user_id": user_id,
            "status": "uploaded",   # uploaded → processing → vectorized → failed
            "chunk_count": 0,
            "upload_date": datetime.utcnow(),
            "processed_at": None,
            "error": None,
        }
        result = await self.documents.insert_one(doc)
        doc_id = str(result.inserted_id)
        logger.info(f"Created document record {doc_id} for {symbol}")
        return doc_id

    async def update_document_status(
        self,
        doc_id: str,
        status: str,
        chunk_count: int = 0,
        error: Optional[str] = None,
    ):
        """Update processing status of a document."""
        update = {
            "$set": {
                "status": status,
                "chunk_count": chunk_count,
                "processed_at": datetime.utcnow() if status in ["vectorized", "failed"] else None,
                "error": error,
            }
        }
        await self.documents.update_one({"_id": ObjectId(doc_id)}, update)

    async def get_documents_for_symbol(self, symbol: str) -> List[Dict]:
        """Get all documents uploaded for a company symbol."""
        cursor = self.documents.find(
            {"symbol": symbol.upper()},
            sort=[("upload_date", DESCENDING)]
        )
        docs = await cursor.to_list(length=50)
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    # ====================================================
    # ANALYSIS CACHE
    # ====================================================
    async def cache_analysis(
        self,
        symbol: str,
        analysis_type: str,
        data: Dict[str, Any],
    ):
        """Cache an analysis result (TTL-based via MongoDB TTL index)."""
        await self.analysis_cache.update_one(
            {"symbol": symbol.upper(), "analysis_type": analysis_type},
            {
                "$set": {
                    "symbol": symbol.upper(),
                    "analysis_type": analysis_type,
                    "data": data,
                    "created_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    async def get_cached_analysis(
        self,
        symbol: str,
        analysis_type: str,
    ) -> Optional[Dict]:
        """Get cached analysis if within TTL."""
        result = await self.analysis_cache.find_one(
            {"symbol": symbol.upper(), "analysis_type": analysis_type}
        )
        if result:
            result["_id"] = str(result["_id"])
            return result
        return None

    async def close(self):
        self.client.close()


# Singleton
_mongo_service: Optional[MongoService] = None


async def get_mongo_service() -> MongoService:
    global _mongo_service
    if _mongo_service is None:
        _mongo_service = MongoService()
        await _mongo_service.initialize_indexes()
    return _mongo_service
