from __future__ import annotations
from fastapi import APIRouter,Depends, HTTPException
from backend.database.db_setup import get_db
from backend.schemas.query_model import QueryResponse, QueryRequest
from backend.services.session import ask_question
from sqlalchemy.orm import Session


#router i tanımla
router = APIRouter(
    prefix="/search", # tüm yollar /search ile başlar
    tags=["Soru Sorma İşlemleri"],  #swagger de görünecek başlık
)

#endpointleri tanımlama
#soru sor yanıt uret
@router.post("/ask",response_model=QueryResponse)
async def create_query(request: QueryRequest, db:Session=Depends(get_db)):
    try:
        result=ask_question(db,request)
        if not result:
            raise HTTPException(status_code=400,detail="Cevap Üretilemedi")
        return result
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"AI HATASI : {str(e)}")

