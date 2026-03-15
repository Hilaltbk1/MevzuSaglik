# backend/routers/health.py  (yeni dosya)
from fastapi import APIRouter
from backend.database.db_setup import SessionLocal

router = APIRouter(tags=["Sistem"])

@router.get("/health")
def health_check():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "error", "db": str(e)}