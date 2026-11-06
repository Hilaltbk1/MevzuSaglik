from __future__ import annotations

import uuid

from sqlalchemy import Integer, Column, DateTime, ForeignKey, Boolean, UUID ,text
from sqlalchemy.orm import  relationship

from backend.database.base import Base

class LoginSessionModel(Base):
    __tablename__ = 'login_session'

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False ,index=True)
    created_at= Column(DateTime(timezone=True), nullable=False , server_default=text("now()"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked    = Column(Boolean, nullable=False, server_default=text("false"))

    #relationship
    user = relationship("UserModel", back_populates="login_sessions")  # ← YENİ