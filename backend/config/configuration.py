from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()
class Settings:

    print(f"Sistemdeki Mevcut Değişkenler: {list(os.environ.keys())}")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    # Dosya Yolları
    DOCUMENT_PATH = os.getenv("DOCUMENT_PATH", "./data/Json/mevzuat_verileri.json")
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
    LLM_MODEL_NAME = os.getenv(
        "LLM_MODEL_NAME","gemini-3.8-flash"
    )
    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME","gemini-embedding-001"
    )

    VECTOR_DB_COLLECTION = "mevzu_saglik_docs"
    TEMPERATURE = 0
    MAX_TOKENS = 1000

    JWT_SECRET = os.getenv("JWT_SECRET","")
    JWT_ALGORITHM= "HS256"
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES","480"))

    # Hybrid / RRF
    RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "hybrid").strip().lower()
    VECTOR_FETCH_K = int(os.getenv("VECTOR_FETCH_K", "30"))
    BM25_FETCH_K = int(os.getenv("BM25_FETCH_K", "30"))
    RRF_K = int(os.getenv("RRF_K", "60"))
    HYBRID_TOP_N = int(os.getenv("HYBRID_TOP_N", "20"))
    VECTOR_WEIGHT = float(os.getenv("VECTOR_WEIGHT", "1.0"))
    BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "1.0"))
    ENABLE_RERANK = os.getenv("ENABLE_RERANK", "false").strip().lower() in ("1", "true", "yes")


settings = Settings()