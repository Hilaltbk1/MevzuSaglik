from __future__ import annotations
import traceback
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
        # !!! BURASI KRİTİK: Hatayı Render loglarına detaylıca basar
        error_trace = traceback.format_exc()
        print(f"--- RAG HATASI DETAYI ---\n{error_trace}")

        # Kullanıcıya daha açıklayıcı bir hata dönelim
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "trace": error_trace.splitlines()[-3:]  # Son birkaç satırı JSON'da da gör
            }
        )
