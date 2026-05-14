from datetime import datetime
from pydantic import BaseModel


class FileResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_type: str
    file_path: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    files: list[FileResponse]
