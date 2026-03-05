from __future__ import annotations
from sqlalchemy import Integer,Column, String, DateTime
from sqlalchemy.orm import relationship
import datetime
from backend.database.base import Base

class SessionModel(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    session_uuid=Column(String(36), nullable=False)
    user_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

    messages=relationship("MessageModel",back_populates="session",cascade="all, delete-orphan")
