from __future__ import annotations
import traceback

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_user
from backend.dependencies.quota import check_daily_quota
from backend.logger import logger
from backend.schemas.query_model import QueryResponse, QueryRequest
from backend.services.session import ask_question

router = APIRouter(prefix="/search", tags=["Soru Sorma İşlemleri"])


class ChatRequest(BaseModel):
    message: str
    session_uuid: str


@router.post("/ask", response_model=QueryResponse)
async def create_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from backend.schemas.tenant_model import TenantModel
    tenant = db.query(TenantModel).filter_by(id=current_user.tenant_id).first()
    check_daily_quota(tenant, current_user.username, db)
    try:
        result = ask_question(
            db,
            request,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
        )
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
    current_user=Depends(get_current_user),
):
    from backend.services.Retrievers import retrieval_chain
    from backend.schemas.tenant_model import TenantModel
    tenant = db.query(TenantModel).filter_by(id=current_user.tenant_id).first()
    check_daily_quota(tenant, current_user.username, db)
    user_input = request.message    
    if not user_input:
        raise HTTPException(status_code=400, detail="Mesaj gerekli")

    import csv
    import os
    from datetime import datetime

    LOG_FILE    = "usage_logs.csv"
    file_exists = os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "user_id"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_user.username])
    except Exception as e:
        logger.error(f"Loglama hatası: {e}")

    try:
        container = retrieval_chain()
        response  = container.full_chain.invoke({
            "input":           user_input,
            "chat_history":    [],
            "current_user_id": current_user.id,
        })
        return {"response": response["answer"]}
    except Exception as e:
        logger.error(f"Chat hatası: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Sunucu hatası: {str(e)}")
