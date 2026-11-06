from __future__ import annotations
import secrets
from backend.schemas.document_model import DocumentModel, CategoryModel, DocumentCategoryModel
import uuid as uuid_mod

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.db_setup import get_db
from backend.dependencies.auth import require_admin
from backend.schemas import SessionModel
from backend.schemas.tenant_model import TenantModel, PlanType
from backend.schemas.user_model import UserModel

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tenant/create")
def tenant_create(
    name: str,
    plan: PlanType = PlanType.free,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    api_key = secrets.token_hex(32)
    tenant  = crud.create_tenant(db, name, plan, api_key)
    return {"tenant_id": tenant.id, "api_key": api_key}


@router.delete("/tenant/{tenant_id}/data")
def delete_tenant_data(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    sessions = db.query(SessionModel).filter_by(tenant_id=tenant_id).all()
    for s in sessions:
        db.delete(s)
    db.query(TenantModel).filter_by(id=tenant_id).delete()
    db.commit()
    return {"silindi": True, "tenant_id": tenant_id}

# --- Belge listeleme ---
@router.get("/documents")
def list_documents(
    status: str | None = None,
    category: str | None = None,
    scope: str | None = None,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    """Tüm belgeleri listele — filtrele: status, category slug, scope"""
    q = db.query(DocumentModel)
    if status:
        q = q.filter(DocumentModel.status == status)
    if scope:
        q = q.filter(DocumentModel.access_scope == scope)
    if category:
        cat = db.query(CategoryModel).filter_by(slug=category).first()
        if cat:
            q = q.join(DocumentModel.categories).filter(CategoryModel.id == cat.id)
    docs = q.order_by(DocumentModel.created_at.desc()).all()
    return [
        {
            "id":               str(d.id),
            "title":            d.title,
            "document_type":    d.document_type,
            "status":           d.status,
            "access_scope":     d.access_scope,
            "chunk_count":      d.chunk_count,
            "source_url":       d.source_url,
            "publication_date": str(d.publication_date) if d.publication_date else None,
            "effective_date":   str(d.effective_date) if d.effective_date else None,
            "version":          d.version,
            "created_at":       str(d.created_at),
            "categories":       [c.slug for c in d.categories],
        }
        for d in docs
    ]


# --- Tek belge detayı ---
@router.get("/documents/{document_id}")
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    try:
        doc_uuid = uuid_mod.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz ID")
    doc = db.query(DocumentModel).filter_by(id=doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")
    return {
        "id":               str(doc.id),
        "title":            doc.title,
        "document_type":    doc.document_type,
        "status":           doc.status,
        "access_scope":     doc.access_scope,
        "chunk_count":      doc.chunk_count,
        "content_hash":     doc.content_hash,
        "source_url":       doc.source_url,
        "publication_date": str(doc.publication_date) if doc.publication_date else None,
        "effective_date":   str(doc.effective_date) if doc.effective_date else None,
        "version":          doc.version,
        "owner_id":         doc.owner_id,
        "uploaded_by":      doc.uploaded_by,
        "created_at":       str(doc.created_at),
        "updated_at":       str(doc.updated_at),
        "categories":       [{"slug": c.slug, "name": c.name} for c in doc.categories],
    }


# --- Belge güncelle (kaynak, versiyon, kategori, başlık) ---
@router.patch("/documents/{document_id}")
def update_document(
    document_id: str,
    title: str | None = None,
    document_type: str | None = None,
    source_url: str | None = None,
    version: str | None = None,
    effective_date: str | None = None,
    publication_date: str | None = None,
    category_slugs: list[str] | None = None,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    try:
        doc_uuid = uuid_mod.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz ID")
    doc = db.query(DocumentModel).filter_by(id=doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")

    if title is not None:
        doc.title = title
    if document_type is not None:
        doc.document_type = document_type
    if source_url is not None:
        doc.source_url = source_url
    if version is not None:
        doc.version = version
    if effective_date is not None:
        from datetime import date
        doc.effective_date = date.fromisoformat(effective_date) if effective_date else None
    if publication_date is not None:
        from datetime import date
        doc.publication_date = date.fromisoformat(publication_date) if publication_date else None

    if category_slugs is not None:
        db.query(DocumentCategoryModel).filter_by(document_id=doc.id).delete()
        for slug in category_slugs:
            cat = db.query(CategoryModel).filter_by(slug=slug).first()
            if cat:
                db.add(DocumentCategoryModel(document_id=doc.id, category_id=cat.id))

    db.commit()
    return {"message": "Güncellendi", "id": document_id}


# --- Yeniden indeksle: eski vektörleri sil, yeni PDF ile tekrar yaz ---
@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    """Eski Qdrant noktalarını siler; verilen dosyayı aynı belge kaydı için yeniden işler."""
    from backend.routers.add_documents import _process_upload, upload_status_store
    from backend.database.crud import _get_qdrant_client
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    try:
        doc_uuid = uuid_mod.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz ID")

    doc = db.query(DocumentModel).filter_by(id=doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")

    # 1) Eski vektörleri temizle
    try:
        client = _get_qdrant_client()
        for key in ("metadata.document_id", "document_id"):
            try:
                client.delete(
                    collection_name="mevzu_saglik_docs",
                    points_selector=Filter(
                        must=[FieldCondition(key=key, match=MatchValue(value=str(doc.id)))]
                    ),
                )
            except Exception as inner:
                # key yoksa devam
                pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eski vektör silinemedi: {e}")

    doc.status = "processing"
    doc.chunk_count = 0
    db.commit()

    file_data = []
    for f in files:
        content = await f.read()
        file_data.append({"filename": f.filename or doc.title, "content": content})

    task_id = secrets.token_hex(4)
    upload_status_store[task_id] = {
        "status": "processing",
        "message": f"Reindex: {doc.title}",
        "document_id": str(doc.id),
    }

    # Yeni yükleme: aynı scope/owner ile; content_hash duplicate eski deleted/processing satırını engellemez
    # Not: upload yeni Document satırı açar. Reindex için mevcut satırı güncellemek üzere
    # önce eski kaydı 'deleted' işaretleyip yeniden yüklemek daha güvenli.
    old_owner = doc.owner_id
    old_scope = doc.access_scope
    doc.status = "deleted"
    db.commit()

    background_tasks.add_task(
        _process_upload,
        task_id,
        file_data,
        owner_id=old_owner,
        access_scope=old_scope,
        extra_meta={
            "source_url": doc.source_url,
            "version": doc.version,
            "document_type": doc.document_type or "PDF",
            "publication_date": str(doc.publication_date) if doc.publication_date else None,
        },
    )

    return {
        "message": "Yeniden indeksleme başladı",
        "task_id": task_id,
        "old_document_id": document_id,
        "status_url": f"/add_documents/status/{task_id}",
    }


# --- Kategori listesi ---
@router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    cats = db.query(CategoryModel).order_by(CategoryModel.slug).all()
    return [{"id": c.id, "slug": c.slug, "name": c.name, "description": c.description} for c in cats]


# --- Kategorileri seed et (taksonomi) ---
@router.post("/categories/seed")
def seed_categories(
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    from backend.utils.categories import CATEGORIES, DESCRIPTIONS

    created = []
    skipped = []
    for slug, name in CATEGORIES.items():
        existing = db.query(CategoryModel).filter_by(slug=slug).first()
        if existing:
            skipped.append(slug)
            continue
        db.add(CategoryModel(
            slug=slug,
            name=name,
            description=DESCRIPTIONS.get(slug),
        ))
        created.append(slug)
    db.commit()
    return {"created": created, "skipped": skipped, "total": len(CATEGORIES)}
