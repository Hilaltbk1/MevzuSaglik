import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from database.base import Base



class MessageModel(Base):
    __tablename__ = 'message'

    id=Column(Integer, primary_key=True)
    session_id =Column(Integer,ForeignKey("session.id"),nullable=False)
    session=relationship("SessionModel",back_populates="messages")
    sender_type=Column(String(50),nullable=False)
    content=Column(Text,nullable=False)
    created_at=Column(DateTime,default=datetime.datetime.now)

    logs=relationship("LogModel",back_populates="message",cascade="all, delete-orphan")


