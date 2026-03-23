from __future__ import annotations
from typing import List
from fastapi import APIRouter, UploadFile, HTTPException, File, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.database.crud import upload_files_background

router = APIRouter(
    prefix="/add_documents",
    tags=["Dosya Yükleme İşlemleri"]
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Yükleme durumunu takip etmek için basit in-memory store
upload_status_store: dict[str, dict] = {}


@router.post("/add")
async def add_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    import uuid

    # Boyut kontrolü ve dosya içeriklerini oku (stream kapanmadan önce)
    file_data = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"{file.filename} dosyası çok büyük. Maksimum 50MB yükleyebilirsiniz."
            )
        file_data.append({"filename": file.filename, "content": content})

    # Takip ID'si oluştur
    task_id = str(uuid.uuid4())[:8]
    upload_status_store[task_id] = {"status": "processing", "message": f"{len(file_data)} dosya işleniyor..."}

    # Arka planda işle
    background_tasks.add_task(_process_upload, task_id, file_data)

    return JSONResponse({"task_id": task_id, "message": f"{len(file_data)} dosya arka planda işleniyor. /add_documents/status/{task_id} ile takip edebilirsiniz."})


@router.get("/status/{task_id}")
def get_upload_status(task_id: str):
    if task_id not in upload_status_store:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    return upload_status_store[task_id]


async def _process_upload(task_id: str, file_data: list):
    """Arka planda çalışan yükleme işlemi."""
    try:
        result = await upload_files_background(file_data)
        upload_status_store[task_id] = {"status": "done", "message": result}
    except Exception as e:
        upload_status_store[task_id] = {"status": "error", "message": str(e)}
