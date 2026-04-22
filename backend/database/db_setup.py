
from __future__ import annotations

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config.configuration import Settings
import sys
import os
load_dotenv()

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
#Settings den nesne oluşturduk
settings=Settings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/database
# Proje kök dizinine (ca.pem'in olduğu yer) çıkmak için:
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)
#session oluşturmam lazım
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()