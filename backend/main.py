from __future__ import annotations
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

from backend.utils import create_app
from backend.database.base import Base
from backend.database.db_setup import engine

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
Base.metadata.create_all(bind=engine)

app = create_app()

# Gradio Arayüzünü FastAPI'ye bağla (Opsiyonel ama Render için önerilir)
try:
    import gradio as gr
    from frontend.app import demo
    app = gr.mount_gradio_app(app, demo, path="/chat")
    print("✅ Gradio arayüzü /chat yoluna bağlandı.")
except Exception as e:
    print(f"⚠️ Gradio bağlama hatası: {e}")

import csv
from datetime import datetime
from fastapi import Request
from fastapi.staticfiles import StaticFiles

from fastapi.responses import FileResponse
from backend.utils import retrieval_chain

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

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")
    user_id = data.get("user_id", "Anonymous") # Kullanıcı kodunu al
    
    # Kullanımı logla (H2.3 için)
    log_usage(user_id)
    
    # RAG zincirini çalıştır
    container = retrieval_chain()
    response = container.full_chain.invoke({"input": user_input, "chat_history": []})
    
    return {"response": response["answer"]}

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def home():
    return FileResponse("frontend/index.html")