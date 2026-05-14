from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.storage_service import StorageService
from backend.app.schemas.file import FileResponse as FileResp, FileListResponse
from backend.app.services.audit_service import log_audit

router = APIRouter(tags=["files"])


@router.post("/projects/{project_id}/files", response_model=FileResp, status_code=201)
def upload_file(
    project_id: int, file: UploadFile = File(...),
    file_type: str = Form(default="mri"),
    db: Session = Depends(get_db),
):
    storage = StorageService(db)
    asset = storage.save_upload(file, project_id, file_type)
    log_audit(db, project_id, "upload_file", {"file_name": asset.file_name, "file_type": file_type})
    return asset


@router.get("/projects/{project_id}/files", response_model=FileListResponse)
def list_files(project_id: int, db: Session = Depends(get_db)):
    storage = StorageService(db)
    files = storage.list_project_files(project_id)
    return FileListResponse(files=files)


@router.get("/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    storage = StorageService(db)
    path = storage.get_file_path(file_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path))
