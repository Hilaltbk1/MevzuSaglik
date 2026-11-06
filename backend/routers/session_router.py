from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_user, PLAN_LIMITS
from backend.schemas.message_model import MessageModel
from backend.schemas.session_model import SessionModel
from backend.schemas.tenant_model import TenantModel

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
    current_user=Depends(get_current_user),
):
    """Token'daki kullanıcı adıyla yeni oturum oluşturur. Body'deki user_name dikkate alınmaz."""
    new_session = crud.create_session(
        db,
        user_name=current_user.username,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    return {"id": new_session.id, "session_uuid": new_session.session_uuid}


@router.get("/sessions")
@limiter.limit("30/minute")
async def get_user_sessions_api(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Token'daki kullanıcıya ait oturumları döndürür. URL'de user_name yok."""
    sessions = crud.read_user_sessions(db, user_id=current_user.id)
    result = []
    for s in sessions:
        if not s.messages:
            continue
        content_obj = next(
            (m.content for m in s.messages if m.sender_type == "human"),
            "Yeni Sohbet",
        )
        first_message = str(content_obj)
        title = f"{first_message[:30]}..." if len(first_message) > 30 else first_message
        result.append(
            {
                "session_uuid": s.session_uuid,
                "title": title,
                "created_at": s.created_at,
            }
        )
    return result


@router.get("/user_quota")
@limiter.limit("30/minute")
async def get_user_quota_api(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Token'daki kullanıcının günlük kota kullanımını döndürür."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    tenant = db.query(TenantModel).filter_by(id=current_user.tenant_id).first()

    bugunun_sorulari = (
        db.query(func.count(MessageModel.id))
        .join(MessageModel.session)
        .filter(
            SessionModel.tenant_id == tenant.id,
            SessionModel.user_name == current_user.username,
            MessageModel.sender_type == "human",
            MessageModel.created_at >= today_start,
        )
        .scalar()
    )

    plan_key = tenant.plan if isinstance(tenant.plan, str) else tenant.plan.value
    limit = PLAN_LIMITS[plan_key]["requests_per_day"]
    return {"used": bugunun_sorulari, "total": limit}


@router.get("/user_plan")
@limiter.limit("30/minute")
async def get_user_plan_api(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Token'daki kullanıcının plan bilgisini döndürür."""
    tenant = db.query(TenantModel).filter_by(id=current_user.tenant_id).first()
    plan_key = tenant.plan if isinstance(tenant.plan, str) else tenant.plan.value
    return {"plan": plan_key}
