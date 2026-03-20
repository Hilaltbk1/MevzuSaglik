from __future__ import annotations
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from backend.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id                     = Column(Integer, primary_key=True)
    user_name              = Column(String(255), unique=True, nullable=False, index=True)
    is_premium             = Column(Boolean, default=False, nullable=False)
    stripe_customer_id     = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    premium_since          = Column(DateTime, nullable=True)
    premium_until          = Column(DateTime, nullable=True)
    created_at             = Column(DateTime, default=datetime.datetime.now)