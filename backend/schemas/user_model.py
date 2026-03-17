from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime
import datetime
from backend.database.base import Base

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    tenant_id = Column(Integer, nullable=True) # Optional link to a tenant, or default tenant
    created_at = Column(DateTime, default=datetime.datetime.now)
