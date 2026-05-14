import json
from datetime import datetime, timezone
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.models.analysis_task import AnalysisTask
from backend.app.models.analysis_result import AnalysisResult
from backend.app.schemas.task import TASK_TYPE_NAMES, TASK_TYPES

TASK_DEPENDENCY_ORDER = [
    "image_segmentation", "gwas_analysis", "opengwas_fetch",
    "mendelian_randomization", "mediation_mr", "risk_modeling", "report_generation",
]


class TaskOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, project_id: int, task_type: str, parameters: dict = None) -> AnalysisTask:
        params = parameters or {}
        task = AnalysisTask(
            project_id=project_id,
            task_type=task_type,
            task_name=TASK_TYPE_NAMES.get(task_type, task_type),
            status="pending",
            progress=0,
            input_json=json.dumps({"project_id": project_id, "task_type": task_type, "parameters": params}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_progress(self, task_id: int, progress: int, status: str = None):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if task:
            task.progress = progress
            if status:
                task.status = status
            task.updated_at = datetime.now(timezone.utc)
            self.db.commit()

    def mark_running(self, task_id: int):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        task.progress = 10
        task.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def mark_success(self, task_id: int, output: dict):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        task.status = "success"
        task.progress = 100
        task.output_json = json.dumps(output.get("summary", {}))
        task.finished_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        result = AnalysisResult(
            task_id=task.id, project_id=task.project_id, result_type=task.task_type,
            summary_json=json.dumps(output.get("summary", {})),
            output_files_json=json.dumps(output.get("output_files", [])),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(result)
        self.db.commit()

    def mark_failed(self, task_id: int, error_code: str, error_message: str):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        task.status = "failed"
        task.progress = 0
        task.error_code = error_code
        task.error_message = error_message
        task.finished_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def get_project_tasks(self, project_id: int) -> list[AnalysisTask]:
        return self.db.query(AnalysisTask).filter(
            AnalysisTask.project_id == project_id
        ).order_by(AnalysisTask.created_at.desc()).all()

    def get_task(self, task_id: int) -> AnalysisTask:
        return self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

    def get_next_task_type(self, project_id: int) -> str | None:
        existing = self.db.query(AnalysisTask.task_type).filter(
            AnalysisTask.project_id == project_id
        ).all()
        done = {t[0] for t in existing}
        for tt in TASK_DEPENDENCY_ORDER:
            if tt not in done:
                return tt
        return None
