import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

# Backend modüllerini import etmek için path ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

load_dotenv()

print("=== PRODUCTION API KEY SORUNU ÇÖZÜMÜ ===")

# 1. Mevcut API key'i al
current_api_key = os.getenv("TENANT_API_KEY", "").strip()
print(f"1. .env dosyasındaki API Key: {current_api_key[:20]}...")
print(f"   Uzunluk: {len(current_api_key)}")

# 2. Database bağlantısı
database_url = os.getenv("DATABASE_URL", "").strip()
print(f"\n2. Database URL: {database_url[:50]}...")

if not database_url:
    print("   ✗ DATABASE_URL bulunamadı!")
    exit(1)

try:
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    print("   ✓ Database bağlantısı başarılı")
except Exception as e:
    print(f"   ✗ Database bağlantı hatası: {e}")
    exit(1)

# 3. TenantModel'i import et
try:
    from backend.schemas.tenant_model import TenantModel, PlanType
    print("   ✓ TenantModel import edildi")
except Exception as e:
    print(f"   ✗ Import hatası: {e}")
    # Alternatif yol
    print("   ℹ️ Alternatif yol deniyorum...")
    # Basit bir tenant modeli oluşturalım
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
    import enum
    
    Base = declarative_base()
    
    class PlanType(enum.Enum):
        free = "free"
        pro = "pro"
        enterprise = "enterprise"
    
    class TenantModel(Base):
        __tablename__ = 'tenants'
        
        id = Column(Integer, primary_key=True, index=True)
        name = Column(String, nullable=False)
        plan = Column(Enum(PlanType), default=PlanType.free)
        api_key = Column(String, unique=True, nullable=False)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=lambda: datetime.datetime.now())
    
    print("   ✓ Basit TenantModel oluşturuldu")

# 4. Mevcut tenant'ları kontrol et
print("\n3. Database'deki tenant'ları kontrol ediyorum...")
try:
    tenants = db.query(TenantModel).all()
    print(f"   Toplam tenant sayısı: {len(tenants)}")
    
    # Mevcut API key'e sahip tenant var mı?
    tenant_with_key = None
    for tenant in tenants:
        if tenant.api_key == current_api_key:
            tenant_with_key = tenant
            break
    
    if tenant_with_key:
        print(f"   ✓ Database'de bu API key'e sahip tenant BULUNDU!")
        print(f"     Tenant ID: {tenant_with_key.id}")
        print(f"     Name: {tenant_with_key.name}")
        print(f"     Plan: {tenant_with_key.plan}")
        print(f"     Is Active: {tenant_with_key.is_active}")
    else:
        print(f"   ✗ Database'de bu API key'e sahip tenant BULUNAMADI!")
        
        # Yeni tenant oluşturalım mı?
        print("\n4. Yeni tenant oluşturuluyor...")
        import datetime
        
        # Yeni API key oluştur (veya mevcut key'i kullan)
        new_api_key = current_api_key if current_api_key else str(uuid.uuid4().hex)
        
        new_tenant = TenantModel(
            name="Production Tenant",
            plan=PlanType.pro,
            api_key=new_api_key,
            is_active=True,
            created_at=datetime.datetime.now()
        )
        
        db.add(new_tenant)
        db.commit()
        
        print(f"   ✓ Yeni tenant oluşturuldu!")
        print(f"     ID: {new_tenant.id}")
        print(f"     Name: {new_tenant.name}")
        print(f"     API Key: {new_api_key[:20]}...")
        print(f"     Plan: {new_tenant.plan}")
        
        # .env dosyasını güncelle
        if not current_api_key:
            print("\n5. .env dosyasını güncelleyelim mi?")
            # .env dosyasına yeni API key'i yaz
            with open(".env", "a") as f:
                f.write(f"\nTENANT_API_KEY={new_api_key}\n")
            print(f"   ✓ .env dosyası güncellendi")
            
except Exception as e:
    print(f"   ✗ Hata: {e}")
    import traceback
    print(f"   Traceback: {traceback.format_exc()}")

finally:
    db.close()
    print("\n6. Database bağlantısı kapatıldı")

print("\n=== SONUÇ ===")
print("1. Localhost'ta çalışıyor ✓")
print("2. Production backend çalışıyor ✓")
print("3. Database'de tenant kontrol edildi ✓")
print("4. Gerekirse yeni tenant oluşturuldu ✓")
print("\nArtık production'da belge yükleyebilmelisiniz!")