from __future__ import annotations
import traceback
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_tenant
from backend.dependencies.quota import check_daily_quota
from backend.logger import logger
from backend.schemas.query_model import QueryResponse, QueryRequest
from backend.services.session import ask_question

router = APIRouter(prefix="/search", tags=["Soru Sorma İşlemleri"])


class ChatRequest(BaseModel):
    message: str
    user_name: str
    session_uuid: str
    user_id: str = "Anonymous"


@router.post("/ask", response_model=QueryResponse)
async def create_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
):
    check_daily_quota(tenant, request.user_name, db)
    try:
        result = ask_question(db, request, tenant_id=tenant.id)
        if not result:
            raise HTTPException(status_code=400, detail="Cevap üretilemedi.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG hatası: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Sunucu hatası oluştu.")


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
):
    """API key ile korunan chat endpoint'i"""
    from backend.services.Retrievers import retrieval_chain
    
    user_input = request.message
    user_id = request.user_id
    
    if not user_input:
        raise HTTPException(status_code=400, detail="Mesaj gerekli")
    
    # Kullanımı logla
    import csv
    from datetime import datetime
    import os
    LOG_FILE = "usage_logs.csv"
    file_exists = os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "user_id"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id])
    except Exception as e:
        logger.error(f"Loglama hatası: {e}")
    
    try:
        # RAG zincirini çalıştır
        container = retrieval_chain()
        response = container.full_chain.invoke({"input": user_input, "chat_history": []})
        return {"response": response["answer"]}
    except Exception as e:
        logger.error(f"Chat hatası: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Sunucu hatası oluştu.")
