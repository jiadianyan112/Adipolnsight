import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.analysis_task import AnalysisTask
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectListResponse
from backend.app.services.audit_service import log_audit

router = APIRouter(tags=["projects"])


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=body.name,
        research_goal=body.research_goal,
        exposure=body.exposure,
        outcome=body.outcome,
        mediator_set=body.mediator_set,
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    log_audit(db, project.id, "create_project", {"name": project.name})
    return project


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(status: str = None, db: Session = Depends(get_db)):
    q = db.query(Project).order_by(Project.created_at.desc())
    if status:
        q = q.filter(Project.status == status)
    projects = q.all()
    return ProjectListResponse(projects=projects, total=len(projects))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.query(AnalysisTask).filter(AnalysisTask.project_id == project_id).delete()
    db.delete(project)
    db.commit()
