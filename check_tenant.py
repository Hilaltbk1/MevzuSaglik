#!/usr/bin/env python3
"""Database'de tenant'ı kontrol etmek için script"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Backend path'ini ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.db_setup import get_db, engine
from backend.database.base import Base
from backend.schemas.tenant_model import TenantModel

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

# Database session'ı al
db = next(get_db())

# Mevcut tenant'ları kontrol et
api_key = os.getenv("TENANT_API_KEY", "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af")
tenant = db.query(TenantModel).filter_by(api_key=api_key).first()

if tenant:
    print(f"✓ Tenant bulundu:")
    print(f"  ID: {tenant.id}")
    print(f"  Name: {tenant.name}")
    print(f"  API Key: {tenant.api_key}")
    print(f"  Plan: {tenant.plan}")
    print(f"  Is Active: {tenant.is_active}")
    
    if not tenant.is_active:
        print("\n⚠️ Tenant INACTIVE! Aktif hale getiriliyor...")
        tenant.is_active = True
        db.commit()
        print("✓ Tenant aktif hale getirildi")
else:
    print("✗ Tenant bulunamadı!")
    print(f"  API Key: {api_key}")

db.close()
