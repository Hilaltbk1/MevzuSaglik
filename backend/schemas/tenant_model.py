from __future__ import annotations
import datetime,enum
from sqlalchemy import Column,Integer,String,DateTime,Enum,Boolean
from sqlalchemy.orm import relationship

from backend.database.base import Base

class PlanType(str,enum.Enum):
    free="free"
    pro="pro"
    enterprise="enterprise"


class TenantModel(Base):
    __tablename__ = "tenant"
    id= Column(Integer,primary_key=True)
    name=Column(String(255),nullable=False)
    api_key=Column(String(64),nullable=False,unique=True)
    plan=Column(Enum(PlanType),default=PlanType.free)
    is_active = Column(Boolean,default=True)
    created_at = Column(DateTime,default=datetime.datetime.now)

    #relationshıp
    users = relationship("UserModel", back_populates="tenant")
    sessions = relationship("SessionModel", back_populates="tenant")