from __future__ import annotations
import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, BackgroundTasks, UploadFile, Depends
from fastapi.responses import JSONResponse

from backend.database.crud import upload_files_background
from backend.dependencies.auth import get_current_tenant

router = APIRouter(prefix="/add_documents", tags=["Dosya Yükleme İşlemleri"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
upload_status_store: dict[str, dict] = {}


@router.post("/add")
async def add_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    tenant=Depends(get_current_tenant),
):
    """Belge yükleme endpoint'i - plan kontrolü ile"""
    
    # Plan kontrolü
    if tenant.plan.value == "free":
        raise HTTPException(
            status_code=403,
            detail="❌ Ücretsiz planda belge yükleyemezsiniz. Lütfen Pro veya Unlimited plana yükseltin."
        )
    
    file_data = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"{file.filename} çok büyük. Maksimum 50MB yükleyebilirsiniz.",
            )
        file_data.append({"filename": file.filename, "content": content})

    task_id = str(uuid.uuid4())[:8]
    upload_status_store[task_id] = {"status": "processing", "message": f"{len(file_data)} dosya işleniyor..."}
    background_tasks.add_task(_process_upload, task_id, file_data)

    return JSONResponse({
        "task_id": task_id,
        "message": f"{len(file_data)} dosya arka planda işleniyor.",
    })


@router.get("/status/{task_id}")
def get_upload_status(task_id: str, tenant=Depends(get_current_tenant)):
    if task_id not in upload_status_store:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    return upload_status_store[task_id]


@router.get("/list_existing")
async def list_existing_files(tenant=Depends(get_current_tenant)):
    """Qdrant'taki mevcut dosyaları listele (debug için)"""
    try:
        from backend.database.crud import _get_qdrant_client, _get_existing_files
        client = _get_qdrant_client()
        existing = _get_existing_files(client)
        
        # Benzersiz dosya adlarını al
        unique_files = set()
        for f in existing:
            base = f.replace('.pdf', '').replace('.PDF', '').strip().lower()
            if base:
                unique_files.add(base)
        
        return {
            "total_variations": len(existing),
            "unique_files": len(unique_files),
            "files": sorted(list(unique_files))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _process_upload(task_id: str, file_data: list):
    try:
        result = await upload_files_background(file_data)
        upload_status_store[task_id] = {"status": "done", "message": result}
    except Exception as e:
        upload_status_store[task_id] = {"status": "error", "message": str(e)}
