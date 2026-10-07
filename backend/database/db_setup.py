
from __future__ import annotations

from dotenv import load_dotenv
from backend.config.configuration import Settings
import sys
import os
import socket

load_dotenv()

# Socket timeout ayarla (10 saniye)
socket.setdefaulttimeout(10)

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
#Settings den nesne oluşturduk
settings=Settings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/database
# Proje kök dizinine (ca.pem'in olduğu yer) çıkmak için:
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

DB_AVAILABLE = False
engine = None
SessionLocal = None

# Veritabanı bağlantısını dene - hata alırsa geç
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    if settings.DATABASE_URL:
        # psycopg2 kullan (psycopg v3 değil)  
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://") and "+psycopg2" not in db_url and "+psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=3,
            pool_recycle=1800,
            pool_timeout=10,
            connect_args={"connect_timeout": 10}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DB_AVAILABLE = True
        print("✅ Veritabanı bağlantısı başarılı")
    else:
        print("⚠️  DATABASE_URL bulunamadı, veritabanı devre dışı")
except Exception as e:
    print(f"⚠️  Veritabanı bağlantı hatası (Qdrant ile devam ediliyor): {e}")
    DB_AVAILABLE = False

# if settings.DATABASE_URL:
#     try:
#         # psycopg2 kullan (psycopg v3 değil)  
#         db_url = settings.DATABASE_URL
#         if db_url.startswith("postgresql://") and "+psycopg2" not in db_url and "+psycopg" not in db_url:
#             db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
#         engine = create_engine(
#             db_url,
#             pool_pre_ping=True,
#             pool_size=5,
#             max_overflow=3,
#             pool_recycle=1800,
#             pool_timeout=10,
#             connect_args={"connect_timeout": 10}
#         )
#         SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#         DB_AVAILABLE = True
#     except Exception as e:
#         print(f"⚠️  Engine oluşturma hatası: {e}")
#         DB_AVAILABLE = False
# else:
#     print("⚠️  DATABASE_URL bulunamadı, veritabanı devre dışı")


def get_db():
    if not DB_AVAILABLE or SessionLocal is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Veritabanı bağlantısı şu an kullanılamıyor. Lütfen daha sonra tekrar deneyin."
        )
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()