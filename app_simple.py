"""
Hugging Face Spaces için basit FastAPI uygulaması
Langchain olmadan, Python 3.12 uyumlu
"""
import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import csv
from datetime import datetime

app = FastAPI(title="MevzuSağlık AI - Hugging Face")

# CORS middleware - Domain'iniz için
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mevzusaglik.com.tr",
        "https://www.mevzusaglik.com.tr",
        "https://*.hf.space",
        "https://huggingface.co",
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
        "message": "MevzuSağlık API çalışıyor", 
        "status": "ok", 
        "environment": "Hugging Face Spaces",
        "domain": "mevzusaglik.com.tr",
        "python_version": sys.version
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "python_version": sys.version,
        "endpoints": ["/", "/health", "/chat"],
        "cors_allowed": ["mevzusaglik.com.tr", "www.mevzusaglik.com.tr"]
    }

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    user_id = data.get("user_id", "Anonymous")
    
    # Kullanımı logla
    log_usage(user_id)
    
    # Basit yanıt (langchain olmadan)
    return {
        "response": f"Merhaba! '{user_input}' sorusunu aldım. mevzusaglik.com.tr domain'inden erişiyorsunuz. Python {sys.version_info.major}.{sys.version_info.minor} ile çalışıyorum.",
        "domain": "mevzusaglik.com.tr",
        "deployment": "Hugging Face Spaces",
        "user_id": user_id
    }

# Diğer endpoint'ler
@app.get("/session/create_session")
async def create_session(user_name: str = "Misafir"):
    return {
        "session_uuid": "hf-simple-session",
        "user_name": user_name,
        "title": "Basit Sohbet",
        "status": "active"
    }

@app.get("/session/sessions/{user_name}")
async def get_sessions(user_name: str):
    return [
        {
            "session_uuid": "hf-simple-session",
            "title": "Basit Sohbet",
            "user_name": user_name
        }
    ]

@app.get("/history/{session_uuid}")
async def get_history(session_uuid: str):
    return [{
        "messages": [
            {"content": "Hugging Face Spaces'e hoş geldiniz!", "sender": "ai"},
            {"content": "MevzuSağlık AI basit demo sürümü çalışıyor.", "sender": "ai"}
        ]
    }]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)