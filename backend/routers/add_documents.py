from __future__ import annotations
import uuid as uuid_mod
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, BackgroundTasks, UploadFile, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database.crud import upload_files_background, _get_qdrant_client, _get_existing_files
from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_tenant, get_current_user, require_admin
from backend.logger import logger
from backend.schemas.document_model import DocumentModel
from backend.schemas.user_model import UserRole

router = APIRouter(prefix="/add_documents", tags=["Dosya Yükleme İşlemleri"])

MAX_FILE_SIZE       = 50 * 1024 * 1024  # 50MB
upload_status_store: dict[str, dict] = {}


@router.post("/add")
async def add_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    source_url: str | None = Form(None),
    version: str | None = Form(None),
    publication_date: str | None = Form(None),
    document_type: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Belge yükleme — admin: public, kullanıcı: private"""
    from backend.schemas.tenant_model import TenantModel
    user_tenant = db.query(TenantModel).filter_by(id=current_user.tenant_id).first()
    plan_value  = user_tenant.plan if isinstance(user_tenant.plan, str) else user_tenant.plan.value

    if plan_value == "free":
        raise HTTPException(
            status_code=403,
            detail="❌ Ücretsiz planda belge yükleyemezsiniz.",
        )

    file_data = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"{file.filename} çok büyük. Maksimum 50MB.",
            )
        file_data.append({"filename": file.filename, "content": content})

    # Admin → public (owner_id yok), kullanıcı → private
    if current_user.role == UserRole.admin:
        scope    = "public"
        owner_id = None
    else:
        scope    = "private"
        owner_id = current_user.id

    task_id = str(uuid_mod.uuid4())[:8]
    upload_status_store[task_id] = {
        "status":  "processing",
        "message": f"{len(file_data)} dosya işleniyor...",
    }

    background_tasks.add_task(
        _process_upload,
        task_id,
        file_data,
        owner_id=owner_id,
        access_scope=scope,
        extra_meta={
            "source_url":       source_url,
            "version":          version,
            "publication_date": publication_date,
            "document_type":    document_type or "PDF",
        },
    )

    return JSONResponse({
        "task_id": task_id,
        "message": f"{len(file_data)} dosya arka planda işleniyor.",
    })


@router.get("/status/{task_id}")
def get_upload_status(task_id: str, current_user=Depends(get_current_user)):
    if task_id not in upload_status_store:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    return upload_status_store[task_id]


@router.get("/list_existing")
async def list_existing_files(admin_user=Depends(require_admin)):
    """Qdrant'taki mevcut dosyaları listele — sadece admin"""
    try:
        client   = _get_qdrant_client()
        existing = _get_existing_files(client)

        unique_files = set()
        for f in existing:
            base = f.replace('.pdf', '').replace('.PDF', '').strip().lower()
            if base:
                unique_files.add(base)

        return {
            "total_variations": len(existing),
            "unique_files":     len(unique_files),
            "files":            sorted(list(unique_files)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my_documents")
def my_documents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Giriş yapan kullanıcının kendi belgelerini döndür"""
    docs = (
        db.query(DocumentModel)
        .filter_by(owner_id=current_user.id)
        .order_by(DocumentModel.created_at.desc())
        .all()
    )
    return [
        {
            "id":           str(d.id),
            "title":        d.title,
            "status":       d.status,
            "access_scope": d.access_scope,
            "chunk_count":  d.chunk_count,
            "created_at":   str(d.created_at),
            "categories":   [c.slug for c in d.categories],
        }
        for d in docs
    ]


@router.delete("/delete/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Belge sil: PostgreSQL + Qdrant vektörleri"""

    try:
        doc_uuid = uuid_mod.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz belge ID formatı")

    doc = db.query(DocumentModel).filter_by(id=doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")

    # Sadece sahibi veya admin silebilir
    if doc.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Bu belgeyi silme yetkiniz yok")

    # Qdrant'tan document_id ile sil (nested + flat payload anahtarları)
    try:
        import os
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        client = _get_qdrant_client()
        collection = os.getenv("QDRANT_COLLECTION", "mevzu_saglik_docs")
        for key in ("metadata.document_id", "document_id"):
            try:
                client.delete(
                    collection_name=collection,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=str(doc.id)),
                            )
                        ]
                    ),
                )
            except Exception as inner:
                logger.warning(f"Qdrant silme denemesi ({key}): {inner}")
    except Exception as e:
        logger.error(f"Qdrant silme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Vektör silme hatası: {str(e)}")

    logger.info(
        f"AUDIT delete document_id={document_id} by user_id={current_user.id} "
        f"role={current_user.role}"
    )

    doc.status = "deleted"
    db.commit()

    try:
        from backend.services.Retrievers import invalidate_chain
        invalidate_chain()
    except Exception as inv_err:
        logger.warning(f"Zincir sıfırlama uyarısı: {inv_err}")

    return {"message": f"'{doc.title}' başarıyla silindi", "document_id": document_id}


async def _process_upload(
    task_id: str,
    file_data: list,
    owner_id: int | None = None,
    access_scope: str = "public",
    extra_meta: dict | None = None,
):
    from backend.database.db_setup import SessionLocal
    db = SessionLocal()
    try:
        result = await upload_files_background(
            file_data,
            owner_id=owner_id,
            access_scope=access_scope,
            db=db,
            extra_meta=extra_meta or {},
        )
        upload_status_store[task_id] = {"status": "done", "message": result}
    except Exception as e:
        upload_status_store[task_id] = {"status": "error", "message": str(e)}
    finally:
        db.close()
