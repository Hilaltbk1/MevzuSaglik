from __future__ import annotations
import sys
import os

# .env dosyasını yükle (root dizindeki .env'yi bul)
from dotenv import load_dotenv
# Ana dizindeki .env dosyasını bul
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

from backend.utils import create_app
from backend.database.base import Base
from backend.database.db_setup import engine
from backend.dependencies.auth import get_current_tenant
from fastapi import Depends

# Tüm modelleri import et ki Base.metadata.create_all çalışsın
from backend.schemas.tenant_model import TenantModel
from backend.schemas.user_model import UserModel
from backend.schemas.session_model import SessionModel
from backend.schemas.message_model import MessageModel
from backend.schemas.log_model import LogModel

# Qdrant/gRPC patch
def patch_grpc_type_error():
    try:
        import grpc
        if not hasattr(grpc, 'UpdateMode'):
            class MockUpdateMode: pass
            grpc.UpdateMode = MockUpdateMode
    except ImportError:
        pass

patch_grpc_type_error()

print("Tablolar kontrol ediliyor/oluşturuluyor...")
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import socket
socket.setdefaulttimeout(10)  # Global socket timeout

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Database bağlantısı başarılı")
    Base.metadata.create_all(bind=engine)
except OperationalError as e:
    print(f"⚠️  Database bağlantı hatası: {e}")
    print("⚠️  Uygulama database olmadan çalışacak")
except Exception as e:
    print(f"⚠️  Database hatası: {e}")
    print("⚠️  Uygulama database olmadan çalışacak")

from backend.logger import logger

# Environment variable kontrolü
REQUIRED_VARS = ["DATABASE_URL", "GOOGLE_API_KEY", "QDRANT_HOST", "QDRANT_API_KEY", "TENANT_API_KEY"]
missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    logger.warning(f"Eksik environment variable'lar: {', '.join(missing)}")

app = create_app()

# Gradio integration removed - This is a pure FastAPI HTML application.

import csv
from datetime import datetime
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# =========================
# USAGE LOGGING (TÜBİTAK H2.3)
# =========================
LOG_FILE = "usage_logs.csv"

def log_usage(user_id="Anonymous"):
    """Kullanım istatistiklerini KVKK'ya uygun şekilde kaydeder."""
    file_exists = os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "user_id"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id])
    except Exception as e:
        print(f"Loglama hatası: {e}")



# Static files için birden fazla path deneyelim
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except:
    try:
        app.mount("/static", StaticFiles(directory="../frontend"), name="static")
    except:
        print("Static files dizini bulunamadı")

# Test endpoint'i - API key gerektirmez
@app.get("/test")
def test_endpoint():
    return {
        "status": "ok",
        "message": "Backend çalışıyor",
        "cors_test": "Bu endpoint CORS için test edilebilir",
        "collection_name": "mevzu_saglik_docs",  # Yeni kod kontrolü
        "version": "2.0"  # Version kontrolü
    }

# API key test endpoint'i (geçici olarak comment out)
# @app.get("/test-auth")
# def test_auth_endpoint(tenant=Depends(get_current_tenant)):
#     return {
#         "status": "ok",
#         "message": "Authentication başarılı",
#         "tenant": tenant.name if hasattr(tenant, 'name') else "Tenant bilgisi"
#     }

@app.get("/")
def home():
    api_key    = os.getenv("TENANT_API_KEY", "").strip()
    backend_url = os.getenv("BACKEND_URL", "").strip()  # boşsa frontend kendi origin'ini kullanır
    try:
        # Hugging Face'de frontend dosyası nerede?
        frontend_paths = ["frontend/index.html", "../frontend/index.html", "/app/frontend/index.html"]
        html_content = None
        
        for path in frontend_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    print(f"✓ Frontend dosyası bulundu: {path}")
                    break
            except:
                continue
        
        if html_content is None:
            print("✗ Frontend dosyası bulunamadı!")
            return FileResponse("index.html")  # Fallback
        
        inject = (
            f'<script>'
            f'window.__TENANT_API_KEY__ = "{api_key}";'
            + (f'window.__BACKEND_URL__ = "{backend_url}";' if backend_url else '')
            + f'</script>'
        )
        html_content = html_content.replace("<head>", "<head>\n" + inject, 1)
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    except Exception as e:
        print(f"HTML inject hatası: {e}")
        return FileResponse("index.html")

# ASGI uygulamasını export et
__all__ = ["app"]


# Basit test endpoint'i (API key gerekmez)
@app.post("/test-upload")
async def test_upload():
    return {
        "status": "ok", 
        "message": "Upload endpoint çalışıyor",
        "timestamp": datetime.now().isoformat()
    }

# Mailjet API key test endpoint'i
@app.get("/test-mailjet")
def test_mailjet():
    """Mailjet API key'lerini test eder"""
    import os
    from mailjet_rest import Client
    
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    
    if not api_key or not api_secret:
        return {
            "status": "error",
            "message": "MAILJET_API_KEY veya MAILJET_API_SECRET eksik",
            "check_env": True
        }
    
    # Key format kontrolü (Mailjet key'leri genellikle 32 karakter)
    if len(api_key) < 20:
        return {
            "status": "error",
            "message": "API key çok kısa, doğru formatta olmalı",
            "key_length": len(api_key)
        }
    
    try:
        # Sadece connection testi yap (gerçek e-posta göndermeden)
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        result = mailjet.sender.list()
        
        if result.status_code == 200:
            return {
                "status": "success",
                "message": "Mailjet API bağlantısı başarılı",
                "key_format": "valid",
                "response": result.json()
            }
        else:
            return {
                "status": "error",
                "message": f"Mailjet hatası: {result.status_code}",
                "details": result.json()
            }
    except Exception as e:
        return {
            "status": "error",
            "message": "Bağlantı hatası",
            "error": str(e)
        }