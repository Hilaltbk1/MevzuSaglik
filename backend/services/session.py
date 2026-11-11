from __future__ import annotations
import time
from langchain_core.messages import HumanMessage, AIMessage
from backend.schemas.query_model import QueryRequest, QueryResponse
from backend.services.Retrievers import retrieval_chain
from backend.services.chunking11 import source_label
from backend.services.scope import classify_question, Scope
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.database import crud

OUT_OF_SCOPE_ANSWER = (
    "Bu soru sağlık mevzuatı kapsamı dışında. Ben kanun, yönetmelik, tebliğ ve "
    "uygulama rehberleri hakkında kaynaklı yanıt verebilirim. Sorunuzu mevzuatla "
    "ilgili biçimde yeniden ifade eder misiniz? "
    "Örn: 'Hemşirelik yönetmeliğine göre nöbet süresi kaç saattir?'"
)

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

    # ═══ YENİ: Kapsam kapısı — retrieval'dan ÖNCE ═══
    decision = classify_question(request.query)
    if decision.scope is Scope.OUT_OF_SCOPE:
        human_message = crud.create_message(db, s_id, request.query, "human")
        crud.create_message(db, s_id, OUT_OF_SCOPE_ANSWER, "ai")
        try:
            crud.create_log(db, 200, request.query, OUT_OF_SCOPE_ANSWER, None,
                            human_message.id, scope="out_of_scope",
                            source_count=0, latency_ms=0)
        except Exception as log_error:
            print(f"Loglama sırasında hata oluştu: {log_error}")
        return QueryResponse(
            query=request.query,
            answer=OUT_OF_SCOPE_ANSWER,
            sources=[],
            status="out_of_scope",
            session_uuid=request.session_uuid,
        )
    # ═══ Kapsam kapısı sonu ═══

    # Geçmişi çek (mevcut kodun — aynen)
    # Geçmişi çek — sadece son 6 mesaj (3 soru-cevap) yeterli
    db_messages = crud.read_messages_by_session(db, s_id)
    chat_history = []
    for msg in db_messages[-6:]:
        if msg.sender_type == "human":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))
    # Kullanıcı mesajını kaydet
    human_message = crud.create_message(db, s_id, request.query, "human")

    # AI Yanıtı — user_id ile erişim filtresi geçir
    current_chain = get_chain(tenant_id)
    try:
        t0 = time.perf_counter()
        response = current_chain.full_chain.invoke({
            "input":           request.query,
            "chat_history":    chat_history,
            "current_user_id": user_id,
        })
        latency_ms = int((time.perf_counter() - t0) * 1000)
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

    # Loglama — scope, latency, kaynak sayısı eklendi
    try:
        crud.create_log(db, 200, request.query, answer, None, human_message.id,
                        scope="in_scope", source_count=len(sources),
                        latency_ms=latency_ms)
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
