
from __future__ import annotations

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,  # Maksimum 10 bağlantı
    max_overflow=5,  # Ekstra 5 bağlantı
    pool_recycle=3600,  # 1 saatte bir bağlantıları yenile
    pool_timeout=30,  # 30 saniye bekle
    connect_args={"connect_timeout": 10}  # 10 saniye timeout
)
#session oluşturmam lazım
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()