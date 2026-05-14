from datetime import datetime
from pydantic import BaseModel


class ResultResponse(BaseModel):
    id: int
    task_id: int
    project_id: int
    result_type: str
    summary_json: str
    output_files_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectResultsResponse(BaseModel):
    project_id: int
    results: list[ResultResponse]
