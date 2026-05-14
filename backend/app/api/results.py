from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.analysis_result import AnalysisResult
from backend.app.schemas.result import ResultResponse, ProjectResultsResponse

router = APIRouter(tags=["results"])


@router.get("/tasks/{task_id}/result", response_model=ResultResponse)
def get_task_result(task_id: int, db: Session = Depends(get_db)):
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/projects/{project_id}/results", response_model=ProjectResultsResponse)
def list_project_results(project_id: int, db: Session = Depends(get_db)):
    results = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).order_by(AnalysisResult.created_at.asc()).all()
    return ProjectResultsResponse(project_id=project_id, results=results)
