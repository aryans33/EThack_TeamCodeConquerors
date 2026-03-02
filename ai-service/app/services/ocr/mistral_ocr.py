"""
Mistral OCR Service
Extracts text from PDF documents using Mistral's OCR capabilities.
Output is structured JSON chunks ready for MongoDB storage and ChromaDB vectorization.
"""
from mistralai import Mistral
import base64
import hashlib
import uuid
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Chunk size tuning
CHUNK_SIZE = 1000        # characters per chunk
CHUNK_OVERLAP = 150      # overlap between chunks for context continuity


class MistralOCRService:
    """
    Handles PDF to text extraction using Mistral OCR.
    Produces structured JSON chunks ready for:
      1. Storage in MongoDB (document_chunks collection)
      2. Vectorization via Gemini + ChromaDB
    """

    def __init__(self):
        if not settings.mistral_api_key:
            logger.warning("⚠️  MISTRAL_API_KEY not set — OCR will not work")
            self.client = None
        else:
            self.client = Mistral(api_key=settings.mistral_api_key)
            logger.info("✅ Mistral OCR client initialized")

    def _pdf_to_base64(self, pdf_path: str) -> str:
        """Convert PDF file to base64 string."""
        with open(pdf_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _chunk_text(
        self,
        text: str,
        page_number: int,
        doc_id: str,
        doc_type: str,
        symbol: str,
    ) -> List[Dict[str, Any]]:
        """
        Split a page's text into overlapping chunks.
        Returns list of chunk dicts with metadata.
        """
        chunks = []
        text = text.strip()
        if not text:
            return chunks

        words = text.split()
        current_chunk = []
        current_length = 0
        chunk_index = 0

        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1

            if current_length >= CHUNK_SIZE:
                chunk_text = " ".join(current_chunk)
                chunk_id = f"{doc_id}_p{page_number}_c{chunk_index}"

                chunks.append({
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "page": page_number,
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "symbol": symbol.upper(),
                    "char_count": len(chunk_text),
                    "word_count": len(current_chunk),
                    "metadata": {
                        "source": doc_type,
                        "page": page_number,
                        "symbol": symbol.upper(),
                        "chunk_index": chunk_index,
                    },
                })

                # Overlap: keep last N words
                overlap_words = current_chunk[-int(CHUNK_OVERLAP / 5):]
                current_chunk = overlap_words
                current_length = sum(len(w) + 1 for w in overlap_words)
                chunk_index += 1

        # Last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_id = f"{doc_id}_p{page_number}_c{chunk_index}"
            chunks.append({
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "text": chunk_text,
                "page": page_number,
                "doc_id": doc_id,
                "doc_type": doc_type,
                "symbol": symbol.upper(),
                "char_count": len(chunk_text),
                "word_count": len(current_chunk),
                "metadata": {
                    "source": doc_type,
                    "page": page_number,
                    "symbol": symbol.upper(),
                    "chunk_index": chunk_index,
                },
            })

        return chunks

    def process_pdf(
        self,
        pdf_path: str,
        doc_id: str,
        symbol: str,
        doc_type: str = "annual_report",
    ) -> Dict[str, Any]:
        """
        Process a PDF file through Mistral OCR.

        Args:
            pdf_path: Absolute path to the PDF file
            doc_id: Unique document identifier
            symbol: Stock symbol (e.g., 'RELIANCE')
            doc_type: Type of document (annual_report, concall, fund_report)

        Returns:
            Dict with:
              - total_pages: int
              - total_chunks: int
              - chunks: List of chunk dicts
              - raw_text: Full extracted text
        """
        if not self.client:
            raise RuntimeError("Mistral client not initialized. Set MISTRAL_API_KEY.")

        logger.info(f"🔍 Starting Mistral OCR for {symbol} / {doc_type}: {pdf_path}")

        try:
            # Encode PDF to base64
            pdf_b64 = self._pdf_to_base64(pdf_path)

            # Call Mistral OCR API
            ocr_response = self.client.ocr.process(
                model=settings.mistral_ocr_model,
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{pdf_b64}",
                }
            )

            all_chunks = []
            full_text_parts = []
            page_num = 0

            # Parse OCR response pages
            for page in ocr_response.pages:
                page_num += 1
                page_text = page.markdown or ""
                full_text_parts.append(page_text)

                # Chunk this page's text
                page_chunks = self._chunk_text(
                    text=page_text,
                    page_number=page_num,
                    doc_id=doc_id,
                    doc_type=doc_type,
                    symbol=symbol,
                )
                all_chunks.extend(page_chunks)

            full_text = "\n\n".join(full_text_parts)

            result = {
                "doc_id": doc_id,
                "symbol": symbol.upper(),
                "doc_type": doc_type,
                "total_pages": page_num,
                "total_chunks": len(all_chunks),
                "chunks": all_chunks,
                "raw_text": full_text,
                "status": "success",
            }

            logger.info(
                f"✅ Mistral OCR complete: {page_num} pages, {len(all_chunks)} chunks"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Mistral OCR error: {e}")
            raise

    def process_pdf_bytes(
        self,
        pdf_bytes: bytes,
        doc_id: str,
        symbol: str,
        doc_type: str = "annual_report",
    ) -> Dict[str, Any]:
        """
        Process PDF from raw bytes (for FastAPI UploadFile).
        Same output as process_pdf().
        """
        if not self.client:
            raise RuntimeError("Mistral client not initialized. Set MISTRAL_API_KEY.")

        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        logger.info(f"🔍 Starting Mistral OCR (from bytes) for {symbol} / {doc_type}")

        try:
            ocr_response = self.client.ocr.process(
                model=settings.mistral_ocr_model,
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{pdf_b64}",
                }
            )

            all_chunks = []
            full_text_parts = []
            page_num = 0

            for page in ocr_response.pages:
                page_num += 1
                page_text = page.markdown or ""
                full_text_parts.append(page_text)
                page_chunks = self._chunk_text(
                    text=page_text,
                    page_number=page_num,
                    doc_id=doc_id,
                    doc_type=doc_type,
                    symbol=symbol,
                )
                all_chunks.extend(page_chunks)

            full_text = "\n\n".join(full_text_parts)

            return {
                "doc_id": doc_id,
                "symbol": symbol.upper(),
                "doc_type": doc_type,
                "total_pages": page_num,
                "total_chunks": len(all_chunks),
                "chunks": all_chunks,
                "raw_text": full_text,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"❌ Mistral OCR (bytes) error: {e}")
            raise


# Singleton
_ocr_service: Optional[MistralOCRService] = None


def get_ocr_service() -> MistralOCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = MistralOCRService()
    return _ocr_service
