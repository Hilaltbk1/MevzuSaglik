from __future__ import annotations
import os,secrets
from fastapi import APIRouter,Depends,HTTPException,Header
from sqlalchemy.orm import Session
from backend.database.db_setup import get_db
from backend.schemas import SessionModel
from backend.schemas.tenant_model import TenantModel,PlanType
from backend.database import crud

router=APIRouter(prefix="/admin",tags=["admin"])
ADMIN_SECRET = os.getenv("ADMIN_SECRET","")

def check_admin(x_admin_secret: str = Header(...)) -> None:  # ← dönüş tipi eklendi
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Yetkisiz")

@router.post("/tenant/create")
def tenant_create(
    name: str,
    plan: PlanType = PlanType.free,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),  # ← _None değil, _: None olmalı
):
    api_key = secrets.token_hex(32)
    tenant  = crud.create_tenant(db, name, plan, api_key)  # ← crud. ile çağır
    return {"tenant_id": tenant.id, "api_key": api_key}

@router.delete("/tenant/{tenant_id}/data")
def delete_tenant_data(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    sessions = db.query(SessionModel).filter_by(tenant_id=tenant_id).all()
    for s in sessions:
        db.delete(s)
    db.query(TenantModel).filter_by(id=tenant_id).delete()
    db.commit()
    return {"silindi": True, "tenant_id": tenant_id}