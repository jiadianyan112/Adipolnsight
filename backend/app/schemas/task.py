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


# ===== 分页支持 (v0.3.0) =====

class PaginatedTaskResponse(BaseModel):
    """分页任务列表 — 轮询友好，减少数据传输量"""
    items: list[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    latest_updated_at: Optional[datetime] = None


# ===== 统一任务结构 (v0.3.0) =====

from typing import Any, Dict, Literal

UNIFIED_JOB_STATUSES = ["queued", "running", "succeeded", "failed", "cancelled"]
UnifiedJobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]

# 旧状态 → 统一状态映射
STATUS_NORMALIZE_MAP: Dict[str, str] = {
    "pending": "queued",
    "queued": "queued",
    "running": "running",
    "processing": "running",
    "success": "succeeded",
    "succeeded": "succeeded",
    "completed": "succeeded",
    "complete": "succeeded",
    "failed": "failed",
    "error": "failed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


class UnifiedJobResponse(BaseModel):
    """统合 AnalysisTask 和 JobManager Job 的标准化结构"""
    job_id: str                         # "task-{id}" or "job-{uuid}"
    project_id: int
    job_type: str                       # pipeline step key (e.g., gwas_analysis)
    pipeline_step: str                  # same as job_type for pipeline alignment
    status: str                         # normalized: queued | running | succeeded | failed | cancelled
    progress: int
    progress_stage: str
    input: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None
    error_code: str = ""
    error_message: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    source: str = "analysis_task"       # "analysis_task" | "ai_job"


class UnifiedJobListResponse(BaseModel):
    jobs: list[UnifiedJobResponse]
    source_stats: Dict[str, int] = {}   # e.g. {"analysis_task": 5, "ai_job": 3}
