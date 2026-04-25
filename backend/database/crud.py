from __future__ import annotations
import PyPDF2
import os
import uuid
import io
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.logger import logger
from backend.preprocessing.preprocessing import flatten_mevzuat_object
from backend.schemas import SessionModel, LogModel, PlanType
from backend.schemas.message_model import MessageModel
from backend.schemas.tenant_model import TenantModel

COLLECTION_NAME = "mevzu_saglik_docs"
BATCH_SIZE      = 50


def _get_qdrant_client() -> QdrantClient:
    host    = os.getenv("QDRANT_HOST", "").strip().strip('\n').strip('\r')
    api_key = os.getenv("QDRANT_API_KEY", "").strip().strip('\n').strip('\r')
    return QdrantClient(url=host, api_key=api_key, prefer_grpc=False, timeout=300)


def _get_existing_files(client: QdrantClient) -> set:
    """Qdrant'ta var olan dosyaları al - RAG için işlenmiş dokümanları kontrol eder"""
    existing = set()
    try:
        if client.collection_exists(COLLECTION_NAME):
            logger.info(f"Qdrant collection '{COLLECTION_NAME}' kontrol ediliyor...")
            scroll_res, _ = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=10000,
                with_payload=True,  # Tüm payload'ları al
            )
            logger.info(f"Qdrant'tan {len(scroll_res)} point alındı")
            
            for point in scroll_res:
                if point.payload:
                    # Dosya adını farklı field'lardan ara
                    filename = (
                        point.payload.get("Mevzuat_Adi") or
                        point.payload.get("Dosya_Adi") or
                        point.payload.get("filename") or
                        point.payload.get("file_name")
                    )
                    if filename:
                        # Hem .pdf'li hem .pdf'siz versiyonları ekle
                        existing.add(filename)
                        # .pdf uzantısını kaldır ve ekle
                        base_name = filename.replace('.pdf', '').replace('.PDF', '')
                        existing.add(base_name)
                        existing.add(base_name + '.pdf')
                        existing.add(base_name + '.PDF')
                        logger.debug(f"Mevcut dosya bulundu: {filename}")
            
            # Benzersiz dosya adlarını logla
            unique_files = set()
            for f in existing:
                base = f.replace('.pdf', '').replace('.PDF', '')
                unique_files.add(base)
            logger.info(f"Qdrant'ta toplam {len(unique_files)} benzersiz dosya mevcut")
            
    except Exception as e:
        logger.warning(f"Mevcut dosyalar kontrol edilirken hata: {e}")
    
    return existing


def _pdf_to_doc(filename: str, content: bytes, llm_client) -> Document | None:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        full_text  = "".join(
            page.extract_text() + "\n"
            for page in pdf_reader.pages
            if page.extract_text()
        )
        data = {
            "Mevzuat Adı":    filename,
            "Mevzuat Türü":   "Sağlık Mevzuatı",
            "Mevzuat İçeriği": [full_text],
            "Tablolar":       [],
        }
        page_content = flatten_mevzuat_object(data, llm_client)
        return Document(
            page_content=str(page_content),
            metadata={"Mevzuat_Adi": filename, "Mevzuat_Türü": "Sağlık Mevzuatı", "Dosya_Adi": filename},
        )
    except Exception as e:
        logger.error(f"Dosya işleme hatası ({filename}): {e}")
        return None


async def upload_files_background(file_data: list) -> str:
    """Arka planda çalışır. file_data = [{"filename": str, "content": bytes}, ...]"""
    from backend.llm_client import llm_client

    logger.info(f"upload_files_background başladı: {len(file_data)} dosya")
    
    try:
        logger.info("GoogleGenerativeAIEmbeddings oluşturuluyor...")
        embedding = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            output_dimensionality=3072,
        )
        logger.info("Embedding başarıyla oluşturuldu")
    except Exception as e:
        logger.error(f"Embedding oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding API hatası: {str(e)}")

    try:
        client = _get_qdrant_client()
        logger.info("Qdrant client başarıyla oluşturuldu")
        existing_files = _get_existing_files(client)
        logger.info(f"Mevcut dosyalar kontrol ediliyor: {len(existing_files)} benzersiz dosya adı bulundu")
    except Exception as e:
        logger.error(f"Qdrant bağlantı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Qdrant bağlantı hatası: {str(e)}")

    doc_list = []
    skipped  = []

    for fd in file_data:
        filename = fd["filename"]
        
        # Dosya adı kontrolü - farklı varyasyonları kontrol et
        filename_base = filename.replace('.pdf', '').replace('.PDF', '')
        is_duplicate = False
        
        # Dosya adının farklı varyasyonlarını kontrol et
        if (filename in existing_files or 
            filename_base in existing_files or
            f"{filename_base}.pdf" in existing_files or
            f"{filename_base}.PDF" in existing_files):
            is_duplicate = True
            logger.warning(f"⚠️ Dosya zaten Qdrant'ta mevcut: {filename}")
        
        if is_duplicate:
            skipped.append(filename)
            continue
            
        doc = _pdf_to_doc(filename, fd["content"], llm_client)
        if doc:
            doc_list.append(doc)
        else:
            logger.warning(f"⚠️ Dosya işlenemedi: {filename}")

    # Eğer tüm dosyalar zaten yüklüyse, uyarı döndür
    if len(skipped) > 0 and len(doc_list) == 0:
        msg = f"⚠️ Tüm dosyalar zaten Qdrant veritabanında mevcut: {', '.join(skipped)}"
        logger.warning(msg)
        return msg
    
    # Eğer bazı dosyalar atlandıysa bilgi ver
    if len(skipped) > 0:
        logger.info(f"{len(skipped)} dosya zaten mevcut olduğu için atlandı: {', '.join(skipped)}")
        logger.warning(msg)
        return msg

    logger.info(f"{len(doc_list)} doküman oluşturuldu, {len(skipped)} dosya atlandı")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=150, length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(doc_list)
    logger.info(f"{len(chunks)} chunk oluşturuldu")
    
    try:
        vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)
    except Exception as e:
        logger.error(f"Vector store oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Vector store hatası: {str(e)}")

    total_added = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        try:
            vector_store.add_documents(documents=batch)
            total_added += len(batch)
            logger.info(f"Batch {i // BATCH_SIZE + 1}: {total_added}/{len(chunks)} chunk eklendi.")
        except Exception as e:
            logger.error(f"Batch {i // BATCH_SIZE + 1} eklenirken hata: {e}")
            raise HTTPException(status_code=500, detail=f"Doküman ekleme hatası: {str(e)}")

    msg = f"✅ {len(doc_list)} dosya işlendi, {total_added} parça Qdrant'a kaydedildi."
    if skipped:
        msg += f"\n⚠️ Atlanan dosyalar (zaten Qdrant'ta mevcut): {', '.join(skipped)}"
    
    logger.info(f"upload_files_background tamamlandı: {msg}")
    return msg


# ── CREATE ────────────────────────────────────────────────

def create_message(db: Session, session_id: int, content: str, sender_type: str) -> MessageModel:
    new_message = MessageModel(session_id=session_id, sender_type=sender_type, content=content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def create_session(db: Session, user_name: str, tenant_id: int) -> SessionModel:
    new_session = SessionModel(
        user_name=user_name,
        tenant_id=tenant_id,
        session_uuid=str(uuid.uuid4()),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def create_log(db: Session, status_code: int, request_data: str, response_data: str, error_message: str, message_id: int) -> LogModel:
    new_log = LogModel(
        status_code=status_code,
        request=request_data,
        response=response_data,
        error_message=error_message,
        message_id=message_id,
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


def create_tenant(db: Session, name: str, plan: PlanType, api_key: str) -> TenantModel:
    tenant = TenantModel(name=name, api_key=api_key, plan=plan)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


# ── READ ──────────────────────────────────────────────────

def get_session_by_uuid(db: Session, session_uuid: str) -> SessionModel | None:
    return db.query(SessionModel).filter(SessionModel.session_uuid == session_uuid).first()


def get_messages_by_uuid(db: Session, session_uuid: str):
    return (
        db.query(MessageModel)
        .join(SessionModel)
        .filter(SessionModel.session_uuid == session_uuid)
        .order_by(MessageModel.created_at.asc())
        .all()
    )


def read_messages_by_session(db: Session, session_id: int):
    return (
        db.query(MessageModel)
        .filter_by(session_id=session_id)
        .order_by(MessageModel.created_at.asc())
        .all()
    )


def read_log(db: Session, message_id: int):
    return db.query(LogModel).filter_by(message_id=message_id).all()


def read_user_sessions(db: Session, user_name: str):
    return (
        db.query(SessionModel)
        .filter(SessionModel.user_name == user_name)
        .order_by(SessionModel.created_at.desc())
        .all()
    )


def read_all_messages(db: Session):
    return db.query(MessageModel).all()


def read_all_sessions(db: Session):
    return db.query(SessionModel).all()


def read_all_logs(db: Session):
    return db.query(LogModel).all()
