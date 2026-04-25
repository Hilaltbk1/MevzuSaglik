#!/usr/bin/env python3
"""Yeni tenant oluşturmak için script"""
import os
import sys
import secrets
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.db_setup import get_db, engine
from backend.database.base import Base
from backend.schemas.tenant_model import TenantModel, PlanType

Base.metadata.create_all(bind=engine)
db = next(get_db())

# Yeni tenant oluştur
tenant_name = "Hilal"
plan = PlanType.pro  # pro, free, enterprise
api_key = secrets.token_hex(32)

tenant = TenantModel(
    name=tenant_name,
    api_key=api_key,
    plan=plan,
    is_active=True
)
db.add(tenant)
db.commit()
db.refresh(tenant)

print(f"✓ Yeni tenant oluşturuldu:")
print(f"  Name: {tenant.name}")
print(f"  ID: {tenant.id}")
print(f"  Plan: {tenant.plan}")
print(f"  API Key: {api_key}")
print(f"\n.env dosyasına ekle:")
print(f"TENANT_API_KEY={api_key}")

db.close()
