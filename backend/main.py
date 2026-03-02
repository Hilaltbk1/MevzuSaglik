from database.db_setup import engine
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

from utils import create_app
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