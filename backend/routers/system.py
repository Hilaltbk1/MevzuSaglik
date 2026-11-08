from __future__ import annotations
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.db_setup import get_db
from backend.dependencies.auth import require_admin
from backend.schemas import LogModel
from backend.schemas.document_model import DocumentModel
from backend.schemas.user_model import UserModel

router = APIRouter(prefix="/admin", tags=["admin-operasyon"])

@router.get("/system")
def system_status(
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin),
):
    """Operasyonel gözlemleme: model/indeks sürümleri + son 24 saatte hata sayıları."""
    since = datetime.utcnow() - timedelta(days=1)
    return {
        "index_version":   os.getenv("QDRANT_COLLECTION", "mevzu_saglik_docs"),
        "llm_model":       os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "embedding_model": "gemini-embedding-001",
        "last_24h": {
            "api_errors":     db.query(LogModel).filter(
                LogModel.created_at >= since, LogModel.status_code >= 400).count(),
            "doc_failed":     db.query(DocumentModel).filter(
                DocumentModel.status == "failed").count(),
            "doc_processing": db.query(DocumentModel).filter(
                DocumentModel.status == "processing").count(),
        },
    }