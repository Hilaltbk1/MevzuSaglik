from __future__ import annotations
import traceback
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_tenant
from backend.dependencies.quota import check_daily_quota
from backend.logger import logger
from backend.schemas.query_model import QueryResponse, QueryRequest
from backend.services.session import ask_question

router = APIRouter(prefix="/search", tags=["Soru Sorma İşlemleri"])


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
