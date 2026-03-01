from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import crud
from database.db_setup import get_db
from services import session as session_service
from services.session import get_session_history

router=APIRouter(
    prefix="/history",
    tags=["Sohbet Geçmişi işlemleri"],
)
#tüm geçmiş mesaj metnini gösteren endpoınt tanımlanacak
"""

@router.get("/allHistory")
async def read_history(db: Session = Depends(get_db)):
#bi fonk olusturduk async bu ıle tum sessıonlardakı mesajlara ulasacagız
    try:
        all_history=session_service.get_all_history(db=db)
        return all_history
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Herhangi bir sohbet geçmişi bulunmamaktadır.{str(e)}")

@router.get("/{session_name}")
async def read_user_messages(session_name: str,db: Session = Depends(get_db)):
    try:
        temp=session_service.get_user_history(session_name=session_name,db=db)
        return temp
    except HTTPException as e:
        raise e
    except Exception as e:
        # Beklenmedik hatalar için
        raise HTTPException(status_code=500, detail=f"Bir hata oluştu: {str(e)}")
"""
# Tüm geçmişi getir

@router.get("/{session_uuid}")
async def get_history(session_uuid: str, db: Session = Depends(get_db)):

    try:
        all_history=get_session_history(db=db,uuid =session_uuid)
        if not all_history:
            return []

        return all_history

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






