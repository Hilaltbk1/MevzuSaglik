from __future__ import annotations
import PyPDF2
import os
import uuid
import io
import hashlib
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.logger import logger
from backend.preprocessing.preprocessing import flatten_mevzuat_object
from backend.schemas import SessionModel, LogModel, PlanType
from backend.schemas.message_model import MessageModel
from backend.schemas.tenant_model import TenantModel

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "mevzu_saglik_docs")
BATCH_SIZE      = 20


def _get_qdrant_client() -> QdrantClient:
    host    = os.getenv("QDRANT_HOST", "").strip().strip('\n').strip('\r')
    api_key = os.getenv("QDRANT_API_KEY", "").strip().strip('\n').strip('\r')
    return QdrantClient(url=host, api_key=api_key, prefer_grpc=False, timeout=300)


def _get_existing_files(client: QdrantClient) -> set:
    """Qdrant Cloud'daki mevcut dosyaları al"""
    existing = set()
    try:
        if not client.collection_exists(COLLECTION_NAME):
            logger.warning(f"⚠️ Collection '{COLLECTION_NAME}' bulunamadı")
            return existing

        logger.info(f"📚 Qdrant collection '{COLLECTION_NAME}' taranıyor...")
        scroll_res, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=True,
        )
        logger.info(f"📦 Qdrant'tan {len(scroll_res)} point alındı")

        if len(scroll_res) == 0:
            return existing

        unique_files = set()
        for point in scroll_res:
            if point.payload:
                filename = (
                    point.payload.get("Mevzuat_Adi") or
                    point.payload.get("Dosya_Adi") or
                    point.payload.get("filename") or
                    point.payload.get("file_name")
                )
                if not filename and "metadata" in point.payload:
                    m = point.payload["metadata"]
                    if isinstance(m, dict):
                        filename = (
                            m.get("Mevzuat_Adi") or m.get("Dosya_Adi") or
                            m.get("filename") or m.get("file_name") or
                            m.get("Mevzuat Adı") or m.get("Dosya Adı")
                        )
                if filename:
                    unique_files.add(filename)
                    existing.add(filename)
                    existing.add(filename.lower())
                    base = filename.replace('.pdf', '').replace('.PDF', '').strip()
                    existing.add(base)
                    existing.add(base.lower())
                    existing.add(base + '.pdf')
                    existing.add(base + '.PDF')
                    existing.add((base + '.pdf').lower())

        logger.info(f"✅ Qdrant'ta {len(unique_files)} benzersiz dosya bulundu")
    except Exception as e:
        logger.error(f"❌ Mevcut dosyalar kontrol edilirken hata: {e}")

    return existing


def _pdf_to_doc(
    filename: str,
    content: bytes,
    llm_client,
    owner_id: int | None = None,
    access_scope: str = "public",
) -> Document | None:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        full_text  = "".join(
            page.extract_text() + "\n"
            for page in pdf_reader.pages
            if page.extract_text()
        )
        data = {
            "Mevzuat Adı":     filename,
            "Mevzuat Türü":    "Sağlık Mevzuatı",
            "Mevzuat İçeriği": [full_text],
            "Tablolar":        [],
        }
        page_content = flatten_mevzuat_object(data)
        return Document(
            page_content=str(page_content),
            metadata={
                "Mevzuat_Adi":  filename,
                "Mevzuat_Türü": "Sağlık Mevzuatı",
                "Dosya_Adi":    filename,
                # Qdrant MatchValue ile tutarlı olsun diye string sakla
                "owner_id":     str(owner_id) if owner_id is not None else None,
                "access_scope": access_scope,
            },
        )
    except Exception as e:
        logger.error(f"Dosya işleme hatası ({filename}): {e}")
        return None


async def upload_files_background(
    file_data: list,
    owner_id: int | None = None,
    access_scope: str = "public",
    db: Session | None = None,
    extra_meta: dict | None = None,
) -> str:
    """Arka planda çalışır. file_data = [{"filename": str, "content": bytes}, ...]"""
    from backend.llm_client import llm_client
    from backend.schemas.document_model import DocumentModel, CategoryModel, DocumentCategoryModel
    from backend.utils.categories import CATEGORIES

    if extra_meta is None:
        extra_meta = {}

    logger.info(f"upload_files_background başladı: {len(file_data)} dosya")

    try:
        embedding = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            output_dimensionality=3072,
        )
    except Exception as e:
        logger.error(f"Embedding oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding API hatası: {str(e)}")

    try:
        client         = _get_qdrant_client()
        existing_files = _get_existing_files(client)
    except Exception as e:
        logger.error(f"Qdrant bağlantı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Qdrant bağlantı hatası: {str(e)}")

    doc_list = []
    skipped  = []

    for fd in file_data:
        filename = fd["filename"]

        # 1) Hash ile duplicate kontrolü (silinmiş/başarısız kayıtları yok say)
        file_hash = hashlib.sha256(fd["content"]).hexdigest()
        if db:
            existing_doc = (
                db.query(DocumentModel)
                .filter(
                    DocumentModel.content_hash == file_hash,
                    DocumentModel.owner_id == owner_id,
                    DocumentModel.access_scope == access_scope,
                    DocumentModel.status.notin_(["deleted", "failed"]),
                )
                .first()
            )
            if existing_doc:
                skipped.append(f"{filename} (aynı içerik zaten mevcut: {existing_doc.title})")
                continue

        # 2) Dosya adı ile duplicate kontrolü
        filename_base       = filename.replace('.pdf', '').replace('.PDF', '').strip()
        filename_lower      = filename.lower()
        filename_base_lower = filename_base.lower()

        is_duplicate = False
        for existing in existing_files:
            el = existing.lower()
            if el == filename_lower or el == filename_base_lower or el == f"{filename_base_lower}.pdf":
                is_duplicate = True
                logger.warning(f"🚫 DUPLICATE: '{filename}' zaten mevcut")
                break

        if is_duplicate:
            skipped.append(filename)
            continue

        logger.info(f"✅ Yeni dosya: {filename}")
        doc = _pdf_to_doc(
            filename, fd["content"], llm_client,
            owner_id=owner_id, access_scope=access_scope,
        )
        if not doc:
            logger.error(f"❌ Dosya işlenemedi: {filename}")
            continue

        # 3) PostgreSQL kaydı
        if db:
            from datetime import date as date_type
            db_doc = DocumentModel(
                title=filename,
                document_type=extra_meta.get("document_type", "PDF"),
                access_scope=access_scope,
                owner_id=owner_id,
                uploaded_by=owner_id,
                content_hash=file_hash,
                status="processing",
                source_url=extra_meta.get("source_url"),
                version=extra_meta.get("version"),
                publication_date=(
                    date_type.fromisoformat(extra_meta["publication_date"])
                    if extra_meta.get("publication_date") else None
                ),
            )
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)

            # document_id metadata'ya yaz
            doc.metadata["document_id"] = str(db_doc.id)

            # Otomatik kategori ata → Qdrant metadata topics ile aynı olsun
            assigned = []
            title_lower = filename.lower()
            for slug in CATEGORIES:
                if any(part in title_lower for part in slug.split("_")):
                    cat = db.query(CategoryModel).filter_by(slug=slug).first()
                    if cat:
                        db.add(DocumentCategoryModel(
                            document_id=db_doc.id,
                            category_id=cat.id,
                        ))
                        assigned.append(slug)
            db.commit()
            if not assigned:
                assigned = ["genel"]
            doc.metadata["topics"] = assigned
            doc.metadata["primary_topic"] = assigned[0]
        else:
            doc.metadata.setdefault("topics", ["genel"])
            doc.metadata.setdefault("primary_topic", "genel")

        doc_list.append(doc)

    if len(skipped) > 0 and len(doc_list) == 0:
        msg = (
            f"🚫 Tüm dosyalar zaten mevcut!\n\n"
            f"Atlanan dosyalar: {', '.join(skipped)}\n\n"
            f"💡 Bu dosyalar daha önce yüklenmiş."
        )
        logger.warning(msg)
        return msg

    if len(doc_list) == 0:
        msg = "❌ Hiçbir dosya işlenemedi. Lütfen geçerli PDF dosyaları yükleyin."
        logger.error(msg)
        return msg

    logger.info(f"✅ {len(doc_list)} doküman işlenecek, {len(skipped)} dosya atlandı")

    from backend.services.chunking11 import build_chunks, doc_key_for, contextual_text
    chunks = []
    for d_idx, doc in enumerate(doc_list):
        base_meta = dict(doc.metadata)
        key = doc_key_for(base_meta.get("Mevzuat_Adi", ""), str(d_idx))
        for ch in build_chunks(doc.page_content, base_meta, doc_key=key,
                               type_hint=base_meta.get("Mevzuat_Türü")):
            m = dict(ch.metadata)
            m["body"] = ch.text
            chunks.append(Document(
                page_content=contextual_text(m, ch.text),
                metadata=m
            ))
    logger.info(f"📦 {len(chunks)} chunk oluşturuldu")

    try:
        vector_store = QdrantVectorStore(
            client=client, collection_name=COLLECTION_NAME, embedding=embedding
        )
    except Exception as e:
        logger.error(f"Vector store oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Vector store hatası: {str(e)}")

    total_added    = 0
    failed_batches = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch     = chunks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        for attempt in range(3):
            try:
                vector_store.add_documents(documents=batch)
                total_added += len(batch)
                logger.info(f"📤 Batch {batch_num}: {total_added}/{len(chunks)}")
                if i + BATCH_SIZE < len(chunks):
                    import time
                    time.sleep(0.5)
                break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Resource exhausted" in error_msg or "quota" in error_msg.lower():
                    if attempt < 2:
                        import time
                        wait = 2 * (2 ** attempt)
                        logger.warning(f"⚠️ Rate limit, {wait}s bekleniyor...")
                        time.sleep(wait)
                        continue
                logger.error(f"❌ Batch {batch_num} hata: {error_msg}")
                failed_batches.append(batch_num)
                break

    # Status güncelle — document_id bazında güncelle
    if db:
        from backend.schemas.document_model import DocumentModel as DM
        for doc in doc_list:
            did = doc.metadata.get("document_id")
            if did:
                db.query(DM).filter_by(id=did).update({
                    "status": "failed" if failed_batches else "ready",
                    "chunk_count": len([c for c in chunks if c.metadata.get("document_id") == did]),
                })
        db.commit()

    if failed_batches:
        return (
            f"⚠️ Kısmi başarı: {total_added}/{len(chunks)} chunk eklendi.\n"
            f"❌ Başarısız batch'ler: {', '.join(map(str, failed_batches))}"
        )

    msg = f"✅ {len(doc_list)} dosya işlendi! 📊 {total_added} parça Qdrant'a kaydedildi."
    if skipped:
        msg += "\n\n🚫 Atlanan: " + ", ".join(skipped)
    logger.info(f"✅ Upload tamamlandı")

    try:
        from backend.services.Retrievers import invalidate_chain
        invalidate_chain()
    except Exception as inv_err:
        logger.warning(f"Zincir sıfırlama uyarısı: {inv_err}")

    return msg


# ── CREATE ────────────────────────────────────────────────

def create_message(db: Session, session_id: int, content: str, sender_type: str) -> MessageModel:
    msg = MessageModel(session_id=session_id, sender_type=sender_type, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def create_session(db: Session, user_name: str, tenant_id: int, user_id: int = None) -> SessionModel:
    s = SessionModel(
        user_name=user_name,
        tenant_id=tenant_id,
        user_id=user_id,
        session_uuid=str(uuid.uuid4()),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def create_log(
    db: Session,
    status_code: int,
    request_data: str,
    response_data: str,
    error_message: str,
    message_id: int,
) -> LogModel:
    log = LogModel(
        status_code=status_code,
        request=request_data,
        response=response_data,
        error_message=error_message,
        message_id=message_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def create_tenant(db: Session, name: str, plan: PlanType, api_key: str) -> TenantModel:
    t = TenantModel(name=name, api_key=api_key, plan=plan)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


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


def read_user_sessions(db: Session, user_name: str = None, user_id: int = None):
    """Tercihen user_id ile filtrele; yoksa user_name (geriye uyumluluk)."""
    q = db.query(SessionModel)
    if user_id is not None:
        q = q.filter(SessionModel.user_id == user_id)
    elif user_name is not None:
        q = q.filter(SessionModel.user_name == user_name)
    else:
        return []
    return q.order_by(SessionModel.created_at.desc()).all()


def read_all_messages(db: Session):
    return db.query(MessageModel).all()


def read_all_sessions(db: Session):
    return db.query(SessionModel).all()


def read_all_logs(db: Session):
    return db.query(LogModel).all()
