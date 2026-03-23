from __future__ import annotations
from typing import List
from fastapi import APIRouter, UploadFile, HTTPException, File

from backend.database.crud import upload_files

router = APIRouter(
    prefix="/add_documents",
    tags=["Dosya Yükleme İşlemleri"]
)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

@router.post("/add")
async def add_files(files: List[UploadFile] = File(...)):
    for file in files:
        # Dosya boyutu kontrolü
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"{file.filename} dosyası çok büyük. Maksimum 20MB yükleyebilirsiniz."
            )
        # İçeriği geri sar (tekrar okunabilsin diye)
        await file.seek(0)

    try:
        result = await upload_files(files=files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))