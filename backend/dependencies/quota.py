from __future__ import annotations
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.schemas.message_model import MessageModel
from backend.schemas.session_model import SessionModel
from backend.dependencies.auth import PLAN_LIMITS


def check_daily_quota(tenant, user_name: str, db: Session):
    limit=PLAN_LIMITS[tenant.plan]["requests_per_day"]
    if limit == -1:
        return
    kullanici_toplam_sayi = (
        db.query(func.count(MessageModel.id))
        .join(MessageModel.session)
        .filter(
            SessionModel.tenant_id == tenant.id,
            SessionModel.user_name == user_name,
            MessageModel.sender_type == "human"
        ).scalar()
    )

    if kullanici_toplam_sayi >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Toplam ücretsiz {limit} soru sorma hakkınızı doldurdunuz.",
        )

