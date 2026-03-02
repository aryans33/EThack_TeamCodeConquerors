from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # -----------------------------------------------
    # App
    # -----------------------------------------------
    app_name: str = "FinAnalysis AI Service"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # -----------------------------------------------
    # Internal API Security (service-to-service)
    # -----------------------------------------------
    internal_api_key: str = "internal_api_key_between_services"

    # -----------------------------------------------
    # Google Gemini
    # -----------------------------------------------
    google_api_key: str = ""                              # Gemini API key
    gemini_model: str = "gemini-2.0-flash"               # For macro agents (latest stable)
    gemini_flash_model: str = "gemini-2.0-flash-lite"    # For micro agents (fast + cheap)
    gemini_embedding_model: str = "text-embedding-004"   # For ChromaDB embeddings

    # -----------------------------------------------
    # Mistral OCR
    # -----------------------------------------------
    mistral_api_key: str = ""
    mistral_ocr_model: str = "mistral-ocr-latest"

    # -----------------------------------------------
    # ChromaDB (Vector Store)
    # -----------------------------------------------
    chroma_persist_directory: str = "./data/chromadb"
    chroma_collection_name: str = "finanalysis_documents"
    chroma_host: str = ""        # If using ChromaDB server mode
    chroma_port: int = 8001

    # -----------------------------------------------
    # MongoDB
    # -----------------------------------------------
    mongodb_uri: str = "mongodb://localhost:27017/finanalysis"
    mongodb_db_name: str = "finanalysis"

    # -----------------------------------------------
    # yfinance / Market Data
    # -----------------------------------------------
    news_api_key: str = ""
    default_exchange_suffix: str = ".NS"  # NSE suffix for yfinance

    # -----------------------------------------------
    # CORS
    # -----------------------------------------------
    allowed_origins: str = "http://localhost:5000,http://localhost:3000"

    # -----------------------------------------------
    # Cache TTL (seconds)
    # -----------------------------------------------
    stock_cache_ttl: int = 300       # 5 minutes
    news_cache_ttl: int = 600        # 10 minutes
    analysis_cache_ttl: int = 3600   # 1 hour

    # -----------------------------------------------
    # AutoGen Settings
    # -----------------------------------------------
    max_agent_turns: int = 10
    agent_timeout_seconds: int = 120

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def allowed_origins_list(self) -> list:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def gemini_llm_config(self) -> dict:
        """LLM config dict for AutoGen agents using Gemini."""
        return {
            "config_list": [
                {
                    "model": self.gemini_model,
                    "api_key": self.google_api_key,
                    "api_type": "google",
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
        }

    @property
    def gemini_flash_llm_config(self) -> dict:
        """Faster, cheaper Gemini Flash config for micro-agents."""
        return {
            "config_list": [
                {
                    "model": self.gemini_flash_model,
                    "api_key": self.google_api_key,
                    "api_type": "google",
                }
            ],
            "temperature": 0.0,
            "max_tokens": 2048,
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
