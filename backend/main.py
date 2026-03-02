from database.base import Base
from database.db_setup import engine
from utils import create_app

# --- BU SATIR TABLOLARI OLUŞTURUR ---
print("Tablolar kontrol ediliyor/oluşturuluyor...")
Base.metadata.create_all(bind=engine)


#routers dahil etme


app=create_app()

@app.get("/")
def home():
    return {"Hello": "World"}