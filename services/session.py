from langchain_core.messages import HumanMessage,AIMessage
from database import crud
from models.query_model import QueryRequest, QueryResponse
from sqlalchemy.orm import Session
import datetime
from services.Retrievers import retrieval_chain
#

chain=retrieval_chain() #fonk chaın degıskenıne atadık
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
    response = chain.full_chain.invoke({"input":request.query,"chat_history":chat_history})

    answer=response.get("answer","Üzgünüm cevap oluşturulamadı")

    #ai mesajini kaydet
    crud.create_message(db,user_session_satiri.id,answer,"ai")

    #logla
    crud.create_log(db,200,request.query,answer,None,human_message.id)

    return QueryResponse(
        query=request.query,
        answer=answer,
        status="success"
    )


def get_history(db,user_name:str):
    user_session_satiri=crud.read_session(db, session_name=user_name)
    if not user_session_satiri:
        return []
    else:
        #filtreleme
        db_messages=crud.read_message(db, user_session_satiri.id)
        return db_messages