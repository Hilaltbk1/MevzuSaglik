from __future__ import annotations
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer
from sqlalchemy.orm import Session
from backend.schemas.tenant_model import TenantModel
from backend.database.db_setup import get_db
from backend.utils.jwt_utils import decode_access_token
from backend.schemas.login_session import LoginSessionModel
from backend.schemas.user_model import UserModel, UserRole
from backend.database import timeutil
import uuid as uuid_mod

security       = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

PLAN_LIMITS = {
    "free":       {"requests_per_day": 20,  "max_sessions": 3},
    "pro":        {"requests_per_day": 500, "max_sessions": 50},
    "enterprise": {"requests_per_day": -1,  "max_sessions": -1},
}


def get_current_user(credentials=Depends(security), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Giriş gerekli",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token geçersiz")

    sid = payload.get("sid")
    if not sid:
        raise HTTPException(status_code=401, detail="Session ID yok")

    try:
        sid_uuid = uuid_mod.UUID(sid)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Geçersiz session ID formatı")

    login_session = db.query(LoginSessionModel).filter_by(id=sid_uuid, revoked=False).first()
    if not login_session or login_session.expires_at < timeutil.utcnow():
        raise HTTPException(status_code=401, detail="Session geçersiz veya süresi dolmuş")

    user = db.query(UserModel).filter_by(id=login_session.user_id, is_active=True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")

    return user


def require_admin(user: UserModel = Depends(get_current_user)) -> UserModel:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Bu işlem için yönetici yetkisi gerekir.")
    return user


def get_current_tenant(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db),
) -> TenantModel:
    if not api_key:
        raise HTTPException(status_code=401, detail="API anahtarı bulunamadı.")
    tenant = db.query(TenantModel).filter_by(api_key=api_key, is_active=True).first()
    if not tenant:
        raise HTTPException(status_code=403, detail="Geçersiz veya süresi dolmuş API anahtarı.")
    return tenant
