from __future__ import annotations
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, text ,Enum,Text
from sqlalchemy.orm import  relationship

from backend.database.base import Base
import enum

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"

class UserModel(Base):
    __tablename__ = "users"

    id                   = Column(Integer, primary_key=True)
    role                 = Column(Enum(UserRole), nullable=False, default=UserRole.user, server_default=text("'user'"))
    is_active            = Column(Boolean, nullable=False, server_default=text("true"))
    username             = Column(String(255), unique=True, nullable=False, index=True)
    email                = Column(String(255), unique=True, nullable=True, index=True)
    password_hash        = Column(String(255), nullable=False)
    tenant_id            = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    reset_token          = Column(String(64), nullable=True)
    reset_token_expires  = Column(DateTime, nullable=True)
    created_at           = Column(DateTime, default=datetime.datetime.now)

    totp_secret      = Column(Text, nullable=True)
    is_2fa_enabled   = Column(Boolean, default=False)
    failed_attempts  = Column(Integer, default=0)
    locked_until     = Column(DateTime(timezone=True), nullable=True)
    recovery_codes   = Column(Text, nullable=True)  # virgülle ayrılmış sha256 hash'leri
    #relatıonships
    tenant = relationship("TenantModel", back_populates="users")
    login_sessions = relationship(
        "LoginSessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions = relationship(  
        "SessionModel",
        back_populates="user",
    )