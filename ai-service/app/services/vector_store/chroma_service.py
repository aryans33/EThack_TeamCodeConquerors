"""
ChromaDB Vector Store Service
Handles document storage, retrieval, and semantic search using ChromaDB.
Embeddings are generated via Gemini Text Embedding API.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb import Documents, EmbeddingFunction, Embeddings
from google import genai
from google.genai import types as genai_types
from typing import List, Dict, Any, Optional
import logging
import os

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# ============================================================
# Gemini Embedding Function (custom ChromaDB EmbeddingFunction)
# ============================================================
class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom ChromaDB EmbeddingFunction that uses Gemini text-embedding-004.
    """

    def __init__(self, task_type: str = "RETRIEVAL_DOCUMENT"):
        self.task_type = task_type
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_embedding_model

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            try:
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config=genai_types.EmbedContentConfig(task_type=self.task_type),
                )
                embeddings.append(result.embeddings[0].values)
            except Exception as e:
                logger.error(f"Gemini embedding error: {e}")
                embeddings.append([0.0] * 768)
        return embeddings


# ============================================================
# ChromaDB Vector Store Service
# ============================================================
class VectorStoreService:
    """
    Manages ChromaDB vector store for company financial documents.
    Each company gets its own collection keyed by symbol.
    """

    def __init__(self):
        persist_dir = settings.chroma_persist_directory
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        self._doc_embedding_fn = GeminiEmbeddingFunction(task_type="RETRIEVAL_DOCUMENT")
        self._query_embedding_fn = GeminiEmbeddingFunction(task_type="RETRIEVAL_QUERY")
        logger.info(f"✅ ChromaDB initialized at: {persist_dir}")

    def _collection_name(self, symbol: str) -> str:
        """
        Each company gets its own ChromaDB collection.
        e.g., RELIANCE → finanalysis_RELIANCE
        ChromaDB collection names must be 3-63 chars, alphanumeric + underscores/hyphens.
        """
        clean = symbol.upper().replace(".", "_").replace("-", "_")
        return f"finanalysis_{clean}"

    def get_or_create_collection(self, symbol: str):
        """Get or create a ChromaDB collection for a company symbol."""
        name = self._collection_name(symbol)
        collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self._doc_embedding_fn,
            metadata={"symbol": symbol.upper(), "hnsw:space": "cosine"},
        )
        return collection

    def add_documents(
        self,
        symbol: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> int:
        """
        Add document chunks to ChromaDB for a given company.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            documents: List of text chunks
            metadatas: List of metadata dicts (source, page, doc_type, etc.)
            ids: Unique IDs for each chunk

        Returns:
            Number of documents added
        """
        try:
            collection = self.get_or_create_collection(symbol)

            # ChromaDB upsert handles duplicates gracefully
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"✅ Added {len(documents)} chunks to ChromaDB for {symbol}")
            return len(documents)

        except Exception as e:
            logger.error(f"ChromaDB add_documents error for {symbol}: {e}")
            raise

    def query(
        self,
        symbol: str,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Semantic search in ChromaDB for a company's documents.

        Args:
            symbol: Stock symbol
            query_text: Natural language query
            n_results: Number of results to return
            filter_metadata: Optional ChromaDB where filter

        Returns:
            Dict with documents, distances, metadatas
        """
        try:
            # Use RETRIEVAL_QUERY embedding for queries
            collection = self.client.get_or_create_collection(
                name=self._collection_name(symbol),
                embedding_function=self._query_embedding_fn,
            )

            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_metadata,
                include=["documents", "distances", "metadatas"],
            )

            # Format results
            formatted = []
            docs = results.get("documents", [[]])[0]
            distances = results.get("distances", [[]])[0]
            metas = results.get("metadatas", [[]])[0]

            for doc, dist, meta in zip(docs, distances, metas):
                formatted.append({
                    "text": doc,
                    "relevance_score": round(1 - dist, 4),  # cosine distance → similarity
                    "metadata": meta,
                })

            return {
                "symbol": symbol,
                "query": query_text,
                "results": formatted,
                "total_found": len(formatted),
            }

        except Exception as e:
            logger.error(f"ChromaDB query error for {symbol}: {e}")
            return {"symbol": symbol, "query": query_text, "results": [], "total_found": 0}

    def get_collection_stats(self, symbol: str) -> Dict[str, Any]:
        """Get stats about a company's vector collection."""
        try:
            collection = self.get_or_create_collection(symbol)
            count = collection.count()
            return {
                "symbol": symbol,
                "collection_name": self._collection_name(symbol),
                "document_chunks": count,
                "status": "ready" if count > 0 else "empty",
            }
        except Exception as e:
            return {"symbol": symbol, "status": "error", "error": str(e)}

    def delete_collection(self, symbol: str) -> bool:
        """Delete all vectors for a company (use with caution)."""
        try:
            self.client.delete_collection(self._collection_name(symbol))
            logger.info(f"Deleted ChromaDB collection for {symbol}")
            return True
        except Exception as e:
            logger.error(f"ChromaDB delete error for {symbol}: {e}")
            return False

    def list_collections(self) -> List[str]:
        """List all companies with vector data."""
        collections = self.client.list_collections()
        return [c.name for c in collections]


# Singleton instance
_vector_store: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
