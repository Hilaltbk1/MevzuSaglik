import os
from dotenv import load_dotenv
from pathlib import Path

# PROJE KÖKÜNÜ ZORLA BUL 2 parents yukarı
BASE_DIR = Path(__file__).resolve().parents[1]
#kökünde .env olmalı
env_path = BASE_DIR / ".env"

if not env_path.exists():
    raise FileNotFoundError(f".env bulunamadı: {env_path}")
#env dosyasını oku her seyı os.environ içine koy  DOCUMENT_PATH=abc   os.envıron["DOCUMENT_PATH"] == "abc"

load_dotenv(env_path)


class Settings:
    DOCUMENT_PATH = os.getenv("DOCUMENT_PATH")
    API_KEY = os.getenv("API_KEY")


settings = Settings()
#nesne olusturma settings.DOCUMENT_PATH