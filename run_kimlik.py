"""
kimlik_duzelt.py icin dotenv yukleyici wrapper.
Kullanim:
  python run_kimlik.py          -> rapor
  python run_kimlik.py --dene   -> 1 belge test
  python run_kimlik.py --yaz    -> tum belgeler
"""
import os, sys
from dotenv import load_dotenv

load_dotenv()

# QDRANT_URL yoksa QDRANT_HOST'tan tureт
if not os.getenv("QDRANT_URL") and os.getenv("QDRANT_HOST"):
    os.environ["QDRANT_URL"] = os.getenv("QDRANT_HOST", "").strip()

# Kontrol
missing = [v for v in ["DATABASE_URL", "QDRANT_URL", "QDRANT_API_KEY"] if not os.getenv(v)]
if missing:
    print("HATA: Eksik env var:", missing)
    sys.exit(1)

print("ENV OK — kimlik_duzelt calistiriliyor...")

# kimlik_duzelt.py'yi ayni process'te calistir
import importlib.util
spec = importlib.util.spec_from_file_location("kimlik_duzelt", "kimlik_duzelt.py")
mod  = importlib.util.module_from_spec(spec)
sys.argv = ["kimlik_duzelt.py"] + sys.argv[1:]
spec.loader.exec_module(mod)
