from __future__ import annotations
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.schemas.message_model import MessageModel
from backend.schemas.session_model import SessionModel
from backend.dependencies.auth import PLAN_LIMITS


def check_daily_quota(tenant,db:Session):
    limit=PLAN_LIMITS[tenant.plan]["requests_per_day"]
    if limit == -1:
        return
    bugunki_sayi = (
        db.query(func.count(MessageModel.id))
        .join(MessageModel.session)
        .filter(
            SessionModel.tenant_id == tenant.id,
            MessageModel.sender_type == "human",
            func.date(MessageModel.created_at) == date.today(),
        ).scalar()
    )

    if bugunki_sayi >=limit:
        raise HTTPException(
            status_code=429,
            detail=f"Günlük {limit} istek limitine ulaştınız.Planınızı yükseltiniz",
        )

