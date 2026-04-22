from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_tenant
from backend.services.session import get_session_history
from backend.database.crud import get_session_by_uuid

router = APIRouter(
    prefix="/history",
    tags=["Sohbet Geçmişi"],
)


@router.get("/{session_uuid}")
async def get_history(
    session_uuid: str,
    db: Session = Depends(get_db),
    tenant=Depends(get_current_tenant),
):
    session = get_session_by_uuid(db, session_uuid)
    if not session:
        return []

    if session.tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="Bu oturuma erişim yetkiniz yok.")

    try:
        return get_session_history(db=db, uuid=session_uuid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
