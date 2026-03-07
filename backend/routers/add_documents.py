from __future__ import annotations
from typing import List
# DÜZELTİLEN SATIR: File artık FastAPI'den geliyor
from fastapi import APIRouter, UploadFile, HTTPException, File

from backend.database.crud import upload_files

router = APIRouter(
    prefix="/add_documents",
    tags=["Dosya Yükleme İşlemleri"]
)

@router.post("/add")
# Buradaki List[...] sayesinde kullanıcı 10 tane dosya da yüklese sistem kabul eder.
async def add_files(files: List[UploadFile] = File(...)):
    try:
        # CRUD fonksiyonuna tüm liste (files) gidiyor
        result = await upload_files(files=files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))