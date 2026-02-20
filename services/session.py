from fastapi import Depends
from langchain_core.messages import HumanMessage,AIMessage
from database.db_setup import get_db
from schemas.query_model import QueryRequest, QueryResponse
from services.Retrievers import retrieval_chain
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database import crud

_chain = None  # Başta boş bırakıyoruz

def get_chain():
    """Zinciri sadece ihtiyaç duyulduğunda (ilk soruda) oluşturur."""
    global _chain
    if _chain is None:
        print("⛓️ RAG Zinciri ilk kez oluşturuluyor, bu biraz zaman alabilir...")
        _chain = retrieval_chain()
    return _chain
    #fonk chaın degıskenıne atadık
#sorgu yapacağız
def ask_question(db:Session, request:QueryRequest) ->QueryResponse:
    #bana bu ısımdekı kullanıcının tum bılgılerını getır
    user_session_satiri=crud.read_session(db, session_name=request.user_name)

    if not user_session_satiri:
        user_session_satiri=crud.create_session(db,user_name=request.user_name)
        db_messages=[]
    else:
        db_messages = crud.read_message(db, user_session_satiri.id)
    #geçmişi getir ve AI formatına çevir
    #session.id gönderiyoruz

    chat_history=[]
    for msg in db_messages:
        if msg.sender_type == "human":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))

    #kullanıcı mesajını kayder
    human_message=crud.create_message(db,user_session_satiri.id,request.query,"human")

    #ai ya sor
    current_chain = get_chain()

    # 3. response kısmında current_chain kullanıyoruz
    response = current_chain.full_chain.invoke({"input": request.query, "chat_history": chat_history})

    answer=response.get("answer","Üzgünüm cevap oluşturulamadı")

    raw_docs = response.get("context",[])

    sources = [f"{doc.metadata.get('Mevzuat Adı','Bilinmeyen Mevzuat')} - {doc.metadata.get('Mevzuat Türü','Bilinmeyen')}" for doc in raw_docs] if raw_docs else []

    #tekrar olmasın
    sources=list(set(sources))


    #ai mesajini kaydet
    crud.create_message(db,user_session_satiri.id,answer,"ai")

    #logla
    crud.create_log(db,200,request.query,answer,None,human_message.id)

    return QueryResponse(
        query=request.query,
        answer=answer,
        sources=sources,
        status="success"
    )

#sadece istenilen kullanıcının mesajları
def get_user_history(session_name:str,db:Session):
    try:
        session_obj = crud.read_session(db,session_name)
        if not session_obj:
            raise HTTPException(status_code=404, detail="Kullanıcı oturumu bulunamadı.")
        list_of_messages : List = crud.read_message(db,session_obj.id)
        temp = []
        for msj in list_of_messages:
            temp.append({
                "id":msj.id,
                "sender":msj.sender_type,
                "content":msj.content,
                "created_at":msj.created_at,
                "is_user": True if msj.sender_type == "human" else False
            })
        return temp
    except HTTPException as e:
        raise e

#tüm sohbet geçmisi kullanıcıların altında tum mesajlar olacak
def get_all_history(db: Session = Depends(get_db)):
    try:
        sesion_obj_list=crud.read_all_sessions(db)
        temp_history=[]

        for session_obj in sesion_obj_list:
            session_id=session_obj.id
            messages=crud.read_message(db,session_id)
            user_package = {
                "user_name":session_obj.user_name,
                "messages": [{
                    "content":m.content,
                    "role":m.sender_type,
                    "date":m.created_at,
                } for m in messages]
            }
            temp_history.append(user_package)
        return temp_history
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Herhangi bir sohbet geçmişi bulunmamaktadır.{str(e)}")
