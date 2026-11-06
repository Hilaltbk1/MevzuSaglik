
from __future__ import annotations

import logging
import os
import sys
import socket
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

from backend.config.configuration import Settings

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Socket timeout ayarla (10 saniye)
socket.setdefaulttimeout(10)

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Settings den nesne oluşturduk
settings = Settings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/database
# Proje kök dizinine çıkmak için:
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

# Global variables
DB_AVAILABLE = False
engine = None
SessionLocal = None

def init_database() -> None:
    """Initialize database connection with proper error handling."""
    global DB_AVAILABLE, engine, SessionLocal
    
    if not settings.DATABASE_URL:
        logger.warning("⚠️  DATABASE_URL bulunamadı, veritabanı devre dışı")
        DB_AVAILABLE = False
        return
    
    try:
        # DB URL normalizasyonu - psycopg3 kullan
        db_url = settings.DATABASE_URL
        # psycopg2 prefix'i varsa psycopg3'e çevir
        if "postgresql+psycopg2://" in db_url:
            db_url = db_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://") and "+psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=3,
            pool_recycle=1800,
            pool_timeout=10,
            connect_args={"connect_timeout": 10},
            echo=False  # Set to True for SQL debug logging
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DB_AVAILABLE = True
        logger.info("✅ Veritabanı bağlantısı başarılı")
        
    except SQLAlchemyError as e:
        logger.error(f"❌ SQLAlchemy hatası: {e}")
        DB_AVAILABLE = False
    except Exception as e:
        logger.error(f"❌ Veritabanı bağlantı hatası: {e}")
        DB_AVAILABLE = False

# Initialize on import
init_database()

def get_db() -> Generator[Session, None, None]:
    """Database dependency for FastAPI endpoints."""
    if not DB_AVAILABLE or SessionLocal is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Veritabanı bağlantısı şu an kullanılamıyor. Lütfen daha sonra tekrar deneyin."
        )
    
    db = SessionLocal()
    try:
        yield db
    except (DisconnectionError, SQLAlchemyError) as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables() -> bool:
    """Create all tables. Returns True if successful."""
    if not DB_AVAILABLE or engine is None:
        logger.warning("Database not available, skipping table creation")
        return False
    
    try:
        from backend.database.base import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Table creation failed: {e}")
        return False