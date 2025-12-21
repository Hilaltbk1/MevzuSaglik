import os
from dotenv import load_dotenv
from pathlib import Path

# PROJE KÖKÜNÜ ZORLA BUL 2 parents yukarı
BASE_DIR = Path(__file__).resolve().parents[1]
#kökünde .env olmalı
env_path = BASE_DIR / ".env"

if not env_path.exists():
    # Burada uyarı vermek yerine varsayılan bir yol denenebilir veya hata fırlatılır
    load_dotenv()
else:
    load_dotenv(env_path)

class Settings:

        # self kullanarak tanımlamak "sarı çizgileri" (static member uyarısını) siler
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    DOCUMENT_PATH = os.getenv("DOCUMENT_PATH", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

