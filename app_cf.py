"""
Cloudflare Workers/Pages için FastAPI uygulaması
Python 3.9 uyumlu basit versiyon
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import csv
from datetime import datetime

app = FastAPI(title="MevzuSağlık AI - Cloudflare")

# CORS middleware - Cloudflare için
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mevzusaglik.com.tr",
        "https://www.mevzusaglik.com.tr",
        "https://*.pages.dev",
        "https://*.workers.dev",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# =========================
# USAGE LOGGING
# =========================
LOG_FILE = "usage_logs.csv"

def log_usage(user_id="Anonymous"):
    """Kullanım istatistiklerini kaydeder."""
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
async def root():
    return {
        "message": "MevzuSağlık API Cloudflare'de çalışıyor",
        "status": "ok",
        "deployment": "Cloudflare Workers/Pages"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "deployment": "Cloudflare",
        "endpoints": ["/", "/health", "/chat", "/session/create_session"]
    }

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    user_id = data.get("user_id", "Anonymous")
    
    # Kullanımı logla
    log_usage(user_id)
    
    # Cloudflare için basit yanıt
    return {
        "response": f"Merhaba! '{user_input}' sorusunu aldım. Cloudflare üzerinde çalışıyorum.",
        "deployment": "Cloudflare",
        "user_id": user_id
    }

# Diğer endpoint'ler
@app.get("/session/create_session")
async def create_session(user_name: str = "Misafir"):
    return {
        "session_uuid": "cf-session-123",
        "user_name": user_name,
        "title": "Cloudflare Sohbet",
        "deployment": "Cloudflare"
    }

@app.get("/session/sessions/{user_name}")
async def get_sessions(user_name: str):
    return [
        {
            "session_uuid": "cf-session-123",
            "title": "Cloudflare Sohbet",
            "user_name": user_name,
            "deployment": "Cloudflare"
        }
    ]

@app.get("/history/{session_uuid}")
async def get_history(session_uuid: str):
    return [{
        "messages": [
            {"content": "Cloudflare Workers'a hoş geldiniz!", "sender": "ai"},
            {"content": "MevzuSağlık AI asistanı Cloudflare üzerinde çalışıyor.", "sender": "ai"}
        ]
    }]

# Cloudflare için başlangıç
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)