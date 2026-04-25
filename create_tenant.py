#!/usr/bin/env python3
"""Database'de tenant oluşturmak için script"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Backend path'ini ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.db_setup import get_db, engine
from backend.database.base import Base
from backend.schemas.tenant_model import TenantModel, PlanType
from sqlalchemy.orm import Session

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

# Database session'ı al
db = next(get_db())

# Mevcut tenant'ları kontrol et
api_key = os.getenv("TENANT_API_KEY", "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af")
existing = db.query(TenantModel).filter_by(api_key=api_key).first()

if existing:
    print(f"✓ Tenant zaten var: {existing.name} (ID: {existing.id})")
else:
    # Yeni tenant oluştur
    tenant = TenantModel(
        name="Hilal",
        api_key=api_key,
        plan=PlanType.pro,
        is_active=True
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    print(f"✓ Tenant oluşturuldu: {tenant.name} (ID: {tenant.id})")
    print(f"  API Key: {tenant.api_key}")

db.close()
