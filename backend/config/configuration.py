from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # Tüm değişkenleri temizleyerek alıyoruz
        self.DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
        self.GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
        self.QDRANT_HOST = os.environ.get("QDRANT_HOST", "").strip()
        self.QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "").strip()

        # Dosya yolu ve model isimleri
        self.DOCUMENT_PATH = os.environ.get("DOCUMENT_PATH", "./Data/Json/mevzuat_verileri.json")
        self.LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gemini-1.5-flash")

        # Kontrol Logu
        if not self.DATABASE_URL:
            print("--- KRİTİK HATA: DATABASE_URL SİSTEMDE BULUNAMADI! ---")
            print(f"Sistemdeki Mevcut Anahtarlar: {list(os.environ.keys())}")
        else:
            print(f"BAŞARI: DATABASE_URL yüklendi (Karakter Sayısı: {len(self.DATABASE_URL)})")


# DİĞER DOSYALARIN BU NESNEYİ KULLANMASI İÇİN:
settings = Settings()