from __future__ import annotations
import uuid
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, ForeignKey,
    CheckConstraint, UUID, text, func,
)
from sqlalchemy.orm import relationship
from backend.database.base import Base


class CategoryModel(Base):
    __tablename__ = "category"
    id          = Column(Integer, primary_key=True)
    slug        = Column(String(100), unique=True, nullable=False)
    name        = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)


class DocumentCategoryModel(Base):
    __tablename__ = "document_category"
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id", ondelete="CASCADE"), primary_key=True)


class DocumentModel(Base):
    __tablename__ = "documents"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title            = Column(String(500), nullable=False)
    document_type    = Column(String(100), nullable=True)
    source_url       = Column(Text, nullable=True)
    publication_date = Column(Date, nullable=True)
    effective_date   = Column(Date, nullable=True)
    version          = Column(String(50), nullable=True)
    access_scope     = Column(String(10), nullable=False, server_default="public")   # public | private
    owner_id         = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    uploaded_by      = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content_hash     = Column(String(64), nullable=True)
    status           = Column(String(20), nullable=False, server_default="pending", index=True)
    chunk_count      = Column(Integer, nullable=False, server_default="0")
    created_at       = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at       = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=func.now())

    categories = relationship("CategoryModel", secondary="document_category", lazy="selectin")

    __table_args__ = (
        CheckConstraint("access_scope IN ('public','private')", name="ck_documents_scope"),
        CheckConstraint(
            "(access_scope='public' AND owner_id IS NULL) OR (access_scope='private' AND owner_id IS NOT NULL)",
            name="ck_documents_owner_scope",
        ),
        CheckConstraint(
            "status IN ('pending','processing','ready','failed','deleting','deleted')",
            name="ck_documents_status",
        ),
    )