from __future__ import annotations
from langchain_core.messages import HumanMessage, AIMessage
from backend.schemas.query_model import QueryRequest, QueryResponse
from backend.services.Retrievers import retrieval_chain
from backend.services.chunking11 import source_label
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.database import crud

def get_chain(tenant_id: int = 0):
    return retrieval_chain()


def ask_question(
    db: Session,
    request: QueryRequest,
    tenant_id: int = 0,
    user_id: int | None = None,
) -> QueryResponse:
    db_session = crud.get_session_by_uuid(db, request.session_uuid)
    if not db_session:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")

    if db_session.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Bu oturuma erişim yetkiniz yok")

    if user_id is not None and db_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Bu oturuma erişim yetkiniz yok")

    s_id = db_session.id

    # Geçmişi çek
    db_messages  = crud.read_messages_by_session(db, s_id)
    chat_history = []
    for msg in db_messages:
        if msg.sender_type == "human":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))

    # Kullanıcı mesajını kaydet
    human_message = crud.create_message(db, s_id, request.query, "human")

    # AI Yanıtı — user_id ile erişim filtresi geçir
    current_chain = get_chain(tenant_id)
    try:
        response = current_chain.full_chain.invoke({
            "input":           request.query,
            "chat_history":    chat_history,
            "current_user_id": user_id,
        })
    except Exception as e:
        print(f"--- RAG ZİNCİRİ HATASI: {e} ---")
        raise e

    answer = response.get("answer", "Üzgünüm cevap oluşturulamadı")

    # Kaynakları listele (madde ve ek bilgisi varsa source_label ile dahil et)
    raw_docs = response.get("context", [])
    sources  = list(set([
        doc.metadata.get("source_label") or source_label(doc.metadata) or doc.metadata.get("Mevzuat_Adi", "Bilinmeyen")
        for doc in raw_docs
    ]))

    # AI mesajını kaydet
    crud.create_message(db, s_id, answer, "ai")

    # Loglama
    try:
        crud.create_log(db, 200, request.query, answer, None, human_message.id)
    except Exception as log_error:
        print(f"Loglama sırasında hata oluştu: {log_error}")

    return QueryResponse(
        query=request.query,
        answer=answer,
        sources=sources,
        status="success",
        session_uuid=request.session_uuid,
    )


def get_session_history(db: Session, uuid: str):
    try:
        session = crud.get_session_by_uuid(db, uuid)
        if not session:
            return []

        formatted_messages = [
            {
                "id":         msj.id,
                "sender":     msj.sender_type,
                "content":    msj.content,
                "created_at": msj.created_at,
                "is_user":    msj.sender_type == "human",
            }
            for msj in session.messages
        ]

        return [{
            "session_id":   session.id,
            "session_uuid": session.session_uuid,
            "user_name":    session.user_name,
            "created_at":   session.created_at,
            "messages":     formatted_messages,
        }]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geçmiş çekilirken hata: {str(e)}")
