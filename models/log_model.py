from sqlalchemy import Column, Integer, DateTime, ForeignKey,Text
import datetime
from sqlalchemy.orm import relationship

from database.base import Base

class LogModel(Base):
    __tablename__ = "log"

    id = Column(Integer, primary_key=True)
    status_code=Column(Integer,nullable=False)
    request=Column(Text, nullable=False)
    response=Column(Text, nullable=False)
    error_message=Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

    message_id=Column(Integer, ForeignKey('message.id'), nullable=False)
    message=relationship("MessageModel",back_populates="logs")
