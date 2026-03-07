from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db_setup import get_db
from backend.services.session import get_session_history

router=APIRouter(
    prefix="/history",
    tags=["Sohbet Geçmişi işlemleri"],
)


@router.get("/{session_uuid}")
async def get_history(session_uuid: str, db: Session = Depends(get_db)):

    try:
        all_history=get_session_history(db=db,uuid =session_uuid)
        if not all_history:
            return []

        return all_history

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






