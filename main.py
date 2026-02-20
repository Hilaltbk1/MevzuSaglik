from fastapi import FastAPI

from database.base import Base
from database.db_setup import engine
from routers import search, history
from utils import create_app

# --- BU SATIR TABLOLARI OLUŞTURUR ---
print("Tablolar kontrol ediliyor/oluşturuluyor...")
Base.metadata.create_all(bind=engine)


#routers dahil etme



import schemas # Modellerinin olduğu yer

app=create_app()

@app.get("/")
def home():
    return {"Hello": "World"}