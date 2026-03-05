from __future__ import annotations
from backend.database.db_setup import engine
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

from backend.utils import create_app
# Diğer importlar bundan sonra gelsin:
from backend.database.base import Base


# Qdrant/gRPC tip hatasını runtime'da ezmek için "Monkey Patch"
def patch_grpc_type_error():
    try:
        import grpc
        # EnumTypeWrapper ile | (Union) operatörü arasındaki kavgayı durduruyoruz
        if not hasattr(grpc, 'UpdateMode'):
            class MockUpdateMode: pass
            grpc.UpdateMode = MockUpdateMode
    except ImportError:
        pass

patch_grpc_type_error()


# --- BU SATIR TABLOLARI OLUŞTURUR ---
print("Tablolar kontrol ediliyor/oluşturuluyor...")
Base.metadata.create_all(bind=engine)


#routers dahil etme


app=create_app()

@app.get("/")
def home():
    return {"Hello": "World22"}