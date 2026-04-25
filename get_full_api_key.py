import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.schemas.tenant_model import TenantModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

# Tüm tenant'ları listele
tenants = db.query(TenantModel).all()
print(f"Toplam tenant sayısı: {len(tenants)}")

for tenant in tenants:
    print(f"\nTenant: {tenant.name}")
    print(f"API Key: {tenant.api_key}")
    print(f"Length: {len(tenant.api_key)}")

db.close()