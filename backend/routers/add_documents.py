from __future__ import annotations

from http.client import HTTPException
from typing import List

from fastapi import APIRouter, UploadFile

from backend.database.crud import upload_files

router=APIRouter(
    prefix="/add_documents",
    tags=["Dosya Yükleme İşlemleri"]
)


@router.post("/add")
async def add_files(files: List[UploadFile]):
    try:
        # 1. CRUD fonksiyonunu bekleyerek (await) çağırıyoruz
        result = await upload_files(files=files)

        # 2. CRUD'dan dönen sonucu (mesajı) kullanıcıya geri veriyoruz
        return result

    except Exception as e:
        # Bir hata oluşursa kullanıcıya 500 hatası ve detayını dönüyoruz
        raise HTTPException(status_code=500, detail=str(e))