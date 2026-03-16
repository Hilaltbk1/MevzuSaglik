from __future__ import annotations
from fastapi import APIRouter,Depends
from backend.database import crud
from backend.database.db_setup import get_db
from sqlalchemy.orm import Session

from backend.dependencies.auth import get_current_tenant

router = APIRouter(
    prefix="/session",
    tags=["Oturum İşlemleri"],
)


@router.post("/create_session")
async def create_new_session_api(
        request:dict ,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant)
):
    new_session=crud.create_session(
        db,request.get("user_name","Anonim"),tenant.id,
    )
    return {"id":new_session.id,"session_uuid":new_session.session_uuid}

@router.get("/sessions/{user_name}")
async def get_user_session_api(user_name:str,db:Session = Depends(get_db)):
    sessions = crud.read_user_sessions(db, user_name)
    result = []
    for s in sessions:
        content_obj = next((m.content for m in s.messages if m.sender_type == "human"), "Yeni Sohbet")
        first_message = str(content_obj)
        title = f"{first_message:.30}..." if len(first_message) > 30 else first_message
        result.append({
            "session_uuid": s.session_uuid,
            "title": title,
            "created_at": s.created_at
        })
    return result
