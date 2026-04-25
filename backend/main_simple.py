"""
Simple FastAPI app for Python 3.9 compatibility.
This avoids all problematic imports.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import csv
from datetime import datetime

app = FastAPI(title="MevzuSaglik Simple")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

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

@app.get("/")
def root():
    return {"message": "MevzuSaglik API is running", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy", "python_version": "3.9.0"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    user_id = data.get("user_id", "Anonymous")
    
    # Kullanımı logla (H2.3 için)
    log_usage(user_id)
    
    # Basit bir yanıt
    return {"response": f"Merhaba! '{user_input}' sorusunu aldım. Python 3.9 sürümünde çalışıyorum. Tam RAG fonksiyonelliği için Python 3.10+ gerekiyor."}

# Diğer endpoint'ler
@app.get("/session/create_session")
async def create_session(user_name: str = "Misafir"):
    return {"session_uuid": "test-session-123", "user_name": user_name, "title": "Yeni Sohbet"}

@app.get("/session/sessions/{user_name}")
async def get_sessions(user_name: str):
    return [
        {"session_uuid": "test-session-123", "title": "Yeni Sohbet", "user_name": user_name},
        {"session_uuid": "test-session-456", "title": "Önceki Sohbet", "user_name": user_name}
    ]

@app.get("/history/{session_uuid}")
async def get_history(session_uuid: str):
    return [{
        "messages": [
            {"content": "Merhaba", "sender": "human"},
            {"content": "Merhaba! Size nasıl yardımcı olabilirim?", "sender": "ai"}
        ]
    }]

# Export for ASGI
__all__ = ["app"]