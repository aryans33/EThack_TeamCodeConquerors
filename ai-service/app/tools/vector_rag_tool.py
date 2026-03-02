"""
AutoGen Tools — Vector RAG Tool
Performs semantic search over ChromaDB and synthesizes answers using Gemini.
This is the core RAG (Retrieval Augmented Generation) pipeline.
"""
from google import genai
from typing import Dict, Any, Optional, List
import logging

from app.config.settings import get_settings
from app.services.vector_store.chroma_service import get_vector_store

settings = get_settings()
logger = logging.getLogger(__name__)


class VectorRAGTool:
    """
    AutoGen RAG Tool:
    1. Retrieves relevant chunks from ChromaDB (semantic search)
    2. Passes context to Gemini 1.5 Pro for answer synthesis
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model_name = settings.gemini_model
        self.vector_store = get_vector_store()
        logger.info("✅ Vector RAG Tool initialized")

    def query(
        self,
        symbol: str,
        question: str,
        n_context_chunks: int = 5,
        doc_type_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Answer a question about a company using RAG.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            question: Natural language question
            n_context_chunks: Number of relevant chunks to retrieve
            doc_type_filter: Filter by doc type ('annual_report', 'concall', etc.)

        Returns:
            Dict with answer, sources, and retrieved context
        """
        try:
            # Step 1: Retrieve relevant chunks from ChromaDB
            filter_meta = None
            if doc_type_filter:
                filter_meta = {"doc_type": {"$eq": doc_type_filter}}

            search_results = self.vector_store.query(
                symbol=symbol,
                query_text=question,
                n_results=n_context_chunks,
                filter_metadata=filter_meta,
            )

            # Check if we have any context
            if not search_results["results"]:
                return {
                    "answer": f"No documents found for {symbol}. Please upload annual reports or concall transcripts first.",
                    "sources": [],
                    "context_used": 0,
                    "symbol": symbol,
                }

            # Step 2: Build context from retrieved chunks
            context_parts = []
            sources = []
            for i, result in enumerate(search_results["results"]):
                context_parts.append(
                    f"[Source {i+1} | Page {result['metadata'].get('page', 'N/A')} | "
                    f"Type: {result['metadata'].get('source', 'document')}]\n"
                    f"{result['text']}"
                )
                sources.append({
                    "chunk_index": i + 1,
                    "page": result["metadata"].get("page"),
                    "doc_type": result["metadata"].get("source"),
                    "relevance_score": result["relevance_score"],
                })

            context = "\n\n---\n\n".join(context_parts)

            # Step 3: Generate answer using Gemini 1.5 Pro
            prompt = f"""You are a senior financial analyst specializing in Indian stock markets.
            
You have access to the following excerpts from {symbol}'s financial documents:

{context}

---

Based ONLY on the above document excerpts, answer the following question:
**{question}**

Instructions:
- If the answer is not found in the documents, say "This information is not available in the provided documents."
- Cite the source number (e.g., [Source 1]) when referencing specific data.
- Provide numbers in Indian format (₹ Crores, Lakhs) where applicable.
- Be precise and analytical.

Answer:"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            answer = response.text.strip()

            return {
                "symbol": symbol,
                "question": question,
                "answer": answer,
                "sources": sources,
                "context_used": len(search_results["results"]),
                "model_used": settings.gemini_model,
            }

        except Exception as e:
            logger.error(f"Vector RAG query error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "question": question,
                "answer": f"RAG query failed: {str(e)}",
                "sources": [],
                "context_used": 0,
                "error": str(e),
            }

    def extract_financial_data(
        self,
        symbol: str,
        data_points: List[str],
    ) -> Dict[str, Any]:
        """
        AutoGen Tool: Extract specific financial data points from documents.
        E.g., extract ["revenue", "ebitda", "net_profit"] for last 3 years.

        Args:
            symbol: Stock symbol
            data_points: List of financial metrics to extract

        Returns:
            Dict with extracted values per metric
        """
        query = f"What are the values for: {', '.join(data_points)} from the financial statements? Provide year-wise data."

        result = self.query(symbol=symbol, question=query, n_context_chunks=8)

        return {
            "symbol": symbol,
            "requested_metrics": data_points,
            "extracted_data": result.get("answer", ""),
            "sources": result.get("sources", []),
        }


# Singleton
_rag_tool: Optional[VectorRAGTool] = None


def get_rag_tool() -> VectorRAGTool:
    global _rag_tool
    if _rag_tool is None:
        _rag_tool = VectorRAGTool()
    return _rag_tool


# Standalone functions for AutoGen tool registration
def rag_query(symbol: str, question: str, n_context_chunks: int = 5) -> Dict[str, Any]:
    """AutoGen-compatible function: RAG query for a company."""
    return get_rag_tool().query(symbol, question, n_context_chunks)


def rag_extract_financials(symbol: str, data_points: List[str]) -> Dict[str, Any]:
    """AutoGen-compatible function: Extract specific financial metrics."""
    return get_rag_tool().extract_financial_data(symbol, data_points)
