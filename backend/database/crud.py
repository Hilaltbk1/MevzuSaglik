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
    """Qdrant Cloud'daki mevcut dosyaları al - RAG için işlenmiş dokümanları kontrol eder"""
    existing = set()
    try:
        if not client.collection_exists(COLLECTION_NAME):
            logger.warning(f"⚠️ Collection '{COLLECTION_NAME}' bulunamadı, yeni collection oluşturulacak")
            return existing
            
        logger.info(f"📚 Qdrant collection '{COLLECTION_NAME}' taranıyor...")
        scroll_res, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=True,
        )
        logger.info(f"📦 Qdrant'tan {len(scroll_res)} point alındı")
        
        unique_files = set()
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
                    unique_files.add(filename)
                    # Tüm varyasyonları ekle
                    existing.add(filename)
                    existing.add(filename.lower())
                    # .pdf uzantısını kaldır ve ekle
                    base_name = filename.replace('.pdf', '').replace('.PDF', '').strip()
                    existing.add(base_name)
                    existing.add(base_name.lower())
                    existing.add(base_name + '.pdf')
                    existing.add(base_name + '.PDF')
                    existing.add((base_name + '.pdf').lower())
        
        logger.info(f"✅ Qdrant'ta {len(unique_files)} benzersiz dosya bulundu")
        if unique_files:
            logger.info(f"📋 Mevcut dosyalar: {', '.join(sorted(list(unique_files)[:5]))}{'...' if len(unique_files) > 5 else ''}")
        
    except Exception as e:
        logger.error(f"❌ Mevcut dosyalar kontrol edilirken hata: {e}")
    
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
        logger.info("Qdrant Cloud'a bağlanıldı")
        existing_files = _get_existing_files(client)
        logger.info(f"Qdrant'ta {len(existing_files)} dosya adı varyasyonu bulundu")
    except Exception as e:
        logger.error(f"Qdrant bağlantı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Qdrant bağlantı hatası: {str(e)}")

    doc_list = []
    skipped  = []

    # Her dosyayı kontrol et
    for fd in file_data:
        filename = fd["filename"]
        
        # Dosya adının farklı varyasyonlarını oluştur
        filename_base = filename.replace('.pdf', '').replace('.PDF', '').strip()
        filename_lower = filename.lower()
        filename_base_lower = filename_base.lower()
        
        is_duplicate = False
        
        # Tüm varyasyonları kontrol et (case-insensitive)
        for existing in existing_files:
            existing_lower = existing.lower()
            if (existing_lower == filename_lower or 
                existing_lower == filename_base_lower or
                existing_lower == f"{filename_base_lower}.pdf"):
                is_duplicate = True
                logger.warning(f"🚫 DUPLICATE BULUNDU: '{filename}' zaten Qdrant'ta mevcut ('{existing}' olarak)")
                break
        
        if is_duplicate:
            skipped.append(filename)
            continue
        
        # Dosya yeni, işle
        logger.info(f"✅ Yeni dosya: {filename}")
        doc = _pdf_to_doc(filename, fd["content"], llm_client)
        if doc:
            doc_list.append(doc)
        else:
            logger.error(f"❌ Dosya işlenemedi: {filename}")

    # Eğer tüm dosyalar duplicate ise
    if len(skipped) > 0 and len(doc_list) == 0:
        msg = f"🚫 Tüm dosyalar zaten Qdrant Cloud'da mevcut!\n\nAtlanan dosyalar: {', '.join(skipped)}\n\n💡 Bu dosyalar daha önce yüklenmiş ve RAG sisteminde kullanılıyor."
        logger.warning(f"Tüm dosyalar duplicate: {skipped}")
        return msg
    
    # Eğer hiç dosya işlenemezse
    if len(doc_list) == 0:
        msg = "❌ Hiçbir dosya işlenemedi. Lütfen geçerli PDF dosyaları yükleyin."
        logger.error(msg)
        return msg

    logger.info(f"✅ {len(doc_list)} doküman işlenecek, {len(skipped)} dosya atlandı")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=150, length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(doc_list)
    logger.info(f"📦 {len(chunks)} chunk oluşturuldu")
    
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
            logger.info(f"📤 Batch {i // BATCH_SIZE + 1}: {total_added}/{len(chunks)} chunk Qdrant'a eklendi")
        except Exception as e:
            logger.error(f"Batch {i // BATCH_SIZE + 1} eklenirken hata: {e}")
            raise HTTPException(status_code=500, detail=f"Doküman ekleme hatası: {str(e)}")

    msg = f"✅ {len(doc_list)} dosya başarıyla işlendi!\n\n📊 {total_added} parça Qdrant Cloud'a kaydedildi."
    if skipped:
        msg += f"\n\n🚫 Atlanan dosyalar (zaten Qdrant'ta mevcut):\n• {chr(10).join(['• ' + f for f in skipped])}"
    
    logger.info(f"✅ Upload tamamlandı: {len(doc_list)} dosya, {total_added} chunk, {len(skipped)} atlandı")
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
