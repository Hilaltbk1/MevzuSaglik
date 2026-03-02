

from database.db_setup import engine
from utils import create_app
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Diğer importlar bundan sonra gelsin:
from database.base import Base
# --- BU SATIR TABLOLARI OLUŞTURUR ---
print("Tablolar kontrol ediliyor/oluşturuluyor...")
Base.metadata.create_all(bind=engine)


#routers dahil etme


app=create_app()

@app.get("/")
def home():
    return {"Hello": "World"}