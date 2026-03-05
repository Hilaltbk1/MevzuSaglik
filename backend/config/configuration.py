import os
from dotenv import load_dotenv



load_dotenv()


class Settings:
    # os.getenv'in ikinci parametresini None yapalım ki eksik olduğunu anlayalım
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Diğerleri kalsın...

    def __init__(self):
        # Uygulama başlarken kontrol et
        if not self.DATABASE_URL:
            raise ValueError(
                "!!! KRİTİK HATA: DATABASE_URL Environment Variable bulunamadı veya boş. Render panelini kontrol et !!!")


    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    # Dosya Yolları
    DOCUMENT_PATH = os.getenv("DOCUMENT_PATH", "./Data/Json/mevzuat_verileri.json")
    LLM_MODEL_NAME = os.getenv(
        "LLM_MODEL_NAME","gemini-1.5-flash"
    )
    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME","gemini-embedding-001"
    )

    VECTOR_DB_COLLECTION = "mevzu_saglik_docs"
    TEMPERATURE = 0
    MAX_TOKENS = 1000
