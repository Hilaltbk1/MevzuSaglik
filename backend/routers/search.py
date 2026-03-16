from __future__ import annotations
import traceback
from fastapi import APIRouter,Depends, HTTPException
from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_tenant
from backend.dependencies.quota import check_daily_quota
from backend.schemas.query_model import QueryResponse, QueryRequest
from backend.services.session import ask_question
from sqlalchemy.orm import Session



router = APIRouter(
    prefix="/search",
    tags=["Soru Sorma İşlemleri"],
)

@router.post("/ask",response_model=QueryResponse)
async def create_query(
        request: QueryRequest,
        db:Session=Depends(get_db),
        tenant=Depends(get_current_tenant),
):
    check_daily_quota(tenant, request.user_name, db)
    try:
        result=ask_question(db,request,tenant_id=tenant.id)
        if not result:
            raise HTTPException(status_code=400,detail="Cevap Üretilemedi")
        return result
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"--- RAG HATASI ---\n{error_trace}")
        raise HTTPException(status_code=500, detail={"error": str(e)})
