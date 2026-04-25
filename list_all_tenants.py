#!/usr/bin/env python3
"""Supabase'de tüm tenant'ları listele"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.db_setup import get_db, engine
from backend.database.base import Base
from backend.schemas.tenant_model import TenantModel

Base.metadata.create_all(bind=engine)
db = next(get_db())

# Tüm tenant'ları getir
tenants = db.query(TenantModel).all()

print("=" * 80)
print("TÜM TENANT'LAR")
print("=" * 80)

if not tenants:
    print("Hiç tenant yok!")
else:
    for tenant in tenants:
        print(f"\nID: {tenant.id}")
        print(f"  Name: {tenant.name}")
        print(f"  API Key: {tenant.api_key}")
        print(f"  Plan: {tenant.plan}")
        print(f"  Is Active: {tenant.is_active}")
        print(f"  Created: {tenant.created_at if hasattr(tenant, 'created_at') else 'N/A'}")

print("\n" + "=" * 80)
print(f"Toplam: {len(tenants)} tenant")
print("=" * 80)

db.close()
