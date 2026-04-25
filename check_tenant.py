import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.schemas.tenant_model import TenantModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Database URL: {DATABASE_URL[:50]}...")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

# Tüm tenant'ları listele
tenants = db.query(TenantModel).all()
print(f"\nToplam tenant sayısı: {len(tenants)}")

for tenant in tenants:
    print(f"\nTenant ID: {tenant.id}")
    print(f"  Name: {tenant.name}")
    print(f"  Plan: {tenant.plan}")
    print(f"  API Key: {tenant.api_key[:20]}...")
    print(f"  Is Active: {tenant.is_active}")
    print(f"  Created: {tenant.created_at}")

# .env dosyasındaki API key'i kontrol et
env_api_key = os.getenv("TENANT_API_KEY")
print(f"\n.env dosyasındaki API Key: {env_api_key[:20]}...")

# Bu API key'e sahip tenant var mı?
tenant_with_key = db.query(TenantModel).filter_by(api_key=env_api_key).first()
if tenant_with_key:
    print(f"✓ Database'de bu API key'e sahip tenant bulundu: {tenant_with_key.name}")
else:
    print("✗ Database'de bu API key'e sahip tenant BULUNAMADI!")
    print("  Bu API key ile bir tenant oluşturmanız gerekiyor.")

db.close()