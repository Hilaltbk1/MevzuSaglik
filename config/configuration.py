import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

    DOCUMENT_PATH = os.getenv("DOCUMENT_PATH", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    LLM_MODEL_NAME = os.getenv(
        "LLM_MODEL_NAME", "gpt-4o-mini"
    )
    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME","all-MiniLM-L6-v2"
    )

    VECTOR_DB_COLLECTION = "mevzu_saglik_docs"
    TEMPERATURE = 0
    MAX_TOKENS = 1000
