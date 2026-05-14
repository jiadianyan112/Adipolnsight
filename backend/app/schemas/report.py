from datetime import datetime
from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: int
    project_id: int
    title: str
    content_markdown: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
