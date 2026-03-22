from __future__ import annotations
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id                   = Column(Integer, primary_key=True)
    username             = Column(String(255), unique=True, nullable=False, index=True)
    email                = Column(String(255), unique=True, nullable=True, index=True)
    password_hash        = Column(String(255), nullable=False)
    tenant_id            = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    reset_token          = Column(String(64), nullable=True)
    reset_token_expires  = Column(DateTime, nullable=True)
    created_at           = Column(DateTime, default=datetime.datetime.now)
