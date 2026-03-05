
import os
from dotenv import load_dotenv

load_dotenv()
class Settings:
    def __init__(self):
        # strip() ekleyerek görünmez boşlukları temizliyoruz
        raw_db_url = os.environ.get("DATABASE_URL", "").strip()

        # Sadece var olup olmadığına değil, uzunluğuna da bakıyoruz
        if len(raw_db_url) < 10:
            print(f"KRİTİK UYARI: DATABASE_URL bulundu ama çok kısa veya boş! Gelen: '{raw_db_url}'")
            # Eğer boşsa veya hatalıysa, sistemin çökmemesi için geçici bir kontrol
            self.DATABASE_URL = None
        else:
            self.DATABASE_URL = raw_db_url
            print("DATABASE_URL başarıyla yüklendi (Uzunluk kontrolü tamam).")
    print(f"Sistemdeki Mevcut Değişkenler: {list(os.environ.keys())}")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    # Dosya Yolları
    DOCUMENT_PATH = os.getenv("DOCUMENT_PATH", "./Data/Json/mevzuat_verileri.json")
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
    LLM_MODEL_NAME = os.getenv(
        "LLM_MODEL_NAME","gemini-1.5-flash"
    )
    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME","gemini-embedding-001"
    )

    VECTOR_DB_COLLECTION = "mevzu_saglik_docs"
    TEMPERATURE = 0
    MAX_TOKENS = 1000


