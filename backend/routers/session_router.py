from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_tenant, PLAN_LIMITS
from backend.schemas.message_model import MessageModel
from backend.schemas.session_model import SessionModel

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/session",
    tags=["Oturum İşlemleri"],
)


@router.post("/create_session")
@limiter.limit("20/minute")
async def create_new_session_api(
    request: Request,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
):
    body = await request.json()
    new_session = crud.create_session(db, body.get("user_name", "Anonim"), tenant.id)
    return {"id": new_session.id, "session_uuid": new_session.session_uuid}


@router.get("/sessions/{user_name}")
async def get_user_session_api(user_name: str, db: Session = Depends(get_db)):
    sessions = crud.read_user_sessions(db, user_name)
    result = []
    for s in sessions:
        if not s.messages:
            continue
        content_obj   = next((m.content for m in s.messages if m.sender_type == "human"), "Yeni Sohbet")
        first_message = str(content_obj)
        title         = f"{first_message[:30]}..." if len(first_message) > 30 else first_message
        result.append({
            "session_uuid": s.session_uuid,
            "title":        title,
            "created_at":   s.created_at,
        })
    return result


@router.get("/user_quota/{user_name}")
async def get_user_quota_api(
    user_name: str,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    bugunun_sorulari = (
        db.query(func.count(MessageModel.id))
        .join(MessageModel.session)
        .filter(
            SessionModel.tenant_id == tenant.id,
            SessionModel.user_name == user_name,
            MessageModel.sender_type == "human",
            MessageModel.created_at >= today_start,
        ).scalar()
    )
    limit = PLAN_LIMITS[tenant.plan]["requests_per_day"]
    return {"used": bugunun_sorulari, "total": limit}


@router.get("/user_plan/{user_name}")
async def get_user_plan_api(
    user_name: str,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
):
    """Kullanıcının plan bilgisini döndürür"""
    return {"plan": tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan}
