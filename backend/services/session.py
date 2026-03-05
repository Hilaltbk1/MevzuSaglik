from __future__ import annotations
from langchain_core.messages import HumanMessage, AIMessage
from backend.schemas.query_model import QueryRequest, QueryResponse
from backend.services.Retrievers import retrieval_chain
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.database import crud

_chain = None


def get_chain():
    global _chain
    if _chain is None:
        print("⛓️ RAG Zinciri ilk kez oluşturuluyor, bu biraz zaman alabilir...")
        _chain = retrieval_chain()
    return _chain


# services/session.py
def ask_question(db: Session, request: QueryRequest) -> QueryResponse:
    db_session= crud.get_session_by_uuid(db, request.session_uuid)
    if not db_session:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")

    s_id = db_session.id

    # 2. Geçmişi çekme
    db_messages = crud.read_messages_by_session(db, s_id)

    chat_history = []
    for msg in db_messages:
        if msg.sender_type == "human":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))

    # 3. Kullanıcı mesajını kaydet
    human_message = crud.create_message(db, s_id, request.query, "human")

    # 2. AI Yanıtı Oluşturma
    current_chain = get_chain()

    try:
        response = current_chain.full_chain.invoke({"input": request.query, "chat_history": chat_history})
    except Exception as e:
        print(f"--- RAG ZİNCİRİ HATASI: {e} ---")  # Bu satır hatayı terminale basar
        raise e
    answer = response.get("answer", "Üzgünüm cevap oluşturulamadı")

    # 3. Kaynakları Listeleme
    raw_docs = response.get("context", [])
    sources = list(set([f"{doc.metadata.get('Mevzuat_Adi', 'Bilinmeyen')}" for doc in raw_docs]))

    # 4. AI Mesajını Kaydet
    crud.create_message(db, s_id, answer, "ai")

    # 5. HATA ÖNLEYİCİ LOGLAMA: Loglamayı try-except içine alalım ki hata verirse mesajlar silinmesin
    try:
        crud.create_log(db, 200, request.query, answer, None, human_message.id)
    except Exception as log_error:
        print(f"Loglama sırasında hata oluştu: {log_error}")

    # 6. DÖNÜŞ (Şemadaki tüm alanların olduğundan emin ol)
    return QueryResponse(
        query=request.query,
        answer=answer,
        sources=sources,
        status="success",
        session_uuid=request.session_uuid # Şema bunu bekliyor!
    )

# Oturuma göre mesajları getir
def get_session_history(db: Session, uuid: str):
    try:
        session = crud.get_session_by_uuid(db, uuid)
        if not session:
            return []

        formatted_messages = [
            {
                "id": msj.id,
                "sender": msj.sender_type,
                "content": msj.content,  # İçeriği eklemeyi unutma
                "created_at": msj.created_at,
                "is_user": True if msj.sender_type == "human" else False
            }
            for msj in session.messages
        ]

        return [{
            "session_id": session.id,
            "session_uuid": session.session_uuid,
            "user_name": session.user_name,
            "created_at": session.created_at,
            "messages": formatted_messages
        }]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geçmiş çekilirken hata: {str(e)}")