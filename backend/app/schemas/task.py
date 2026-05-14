from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


TASK_TYPES = [
    "image_segmentation", "gwas_analysis", "opengwas_fetch",
    "mendelian_randomization", "mediation_mr", "risk_modeling", "report_generation",
]

TASK_TYPE_NAMES = {
    "image_segmentation": "AI Image Segmentation",
    "gwas_analysis": "GWAS Analysis",
    "opengwas_fetch": "OpenGWAS Data Fetch",
    "mendelian_randomization": "Mendelian Randomization",
    "mediation_mr": "Mediation MR",
    "risk_modeling": "Risk Modeling",
    "report_generation": "Report Generation",
}


class TaskCreate(BaseModel):
    project_id: int
    task_type: str = Field(..., pattern="^(image_segmentation|gwas_analysis|opengwas_fetch|mendelian_randomization|mediation_mr|risk_modeling|report_generation)$")
    parameters: dict = {}


class TaskResponse(BaseModel):
    id: int
    project_id: int
    task_type: str
    task_name: str
    status: str
    progress: int
    input_json: str
    output_json: str
    error_code: str
    error_message: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
