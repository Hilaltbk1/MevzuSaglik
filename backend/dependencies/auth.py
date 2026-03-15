from __future__ import annotations
from fastapi import HTTPException,Security,Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from backend.schemas.tenant_model import TenantModel
from backend.database.db_setup import get_db

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

PLAN_LIMITS={
    "free":{"requests_per_day":20,"max_sessions":3},
    "pro":{"requests_per_day":500,"max_sessions":50},
    "enterprise":{"requests_per_day":-1,"max_sessions":-1},
}

def get_current_tenant(
        api_key :str =Security(api_key_header),
        db:Session=Depends(get_db),
) -> TenantModel:
    if not api_key:
        raise HTTPException(status_code=401, detail="API anahtari gerekli")
    tenant = db.query(TenantModel).filter_by(api_key=api_key, is_active=True).first()
    if not tenant:
        raise HTTPException(status_code=403, detail="Geçersiz API anahtarı")
    return tenant