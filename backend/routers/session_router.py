from fastapi import APIRouter,Depends
from backend.database import crud
from backend.database.db_setup import get_db
from sqlalchemy.orm import Session


#router tanımlama
router = APIRouter(
    prefix="/session",
    tags=["Oturum İşlemleri"],
)

#endpooinr tanımlama
@router.post("/create_session")
async def create_new_session_api(request:dict , db: Session = Depends(get_db)):
    user_name = request.get("user_name", "Anonim")

    new_session_obj= crud.create_session(db, user_name)
    return {
        "id": new_session_obj.id,
        "session_uuid":new_session_obj.session_uuid,
    }

@router.get("/sessions/{user_name}")
async def get_user_session_api(user_name:str,db:Session = Depends(get_db)):
    sessions= crud.read_user_sessions(db, user_name)
    return sessions
