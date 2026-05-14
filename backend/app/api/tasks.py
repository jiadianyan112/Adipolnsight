import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.task import TaskCreate, TaskResponse, TaskListResponse
from backend.app.services.task_orchestrator import TaskOrchestrator, TASK_DEPENDENCY_ORDER
from backend.app.services.audit_service import log_audit

router = APIRouter(tags=["tasks"])


def run_skill_task(task_id: int):
    from backend.app.database import SessionLocal
    from backend.app.tasks.base import dispatch_skill
    db = SessionLocal()
    try:
        orchestrator = TaskOrchestrator(db)
        task = orchestrator.get_task(task_id)
        if not task:
            return
        orchestrator.mark_running(task_id)
        dispatch_skill(task, db)
    finally:
        db.close()


@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    orch = TaskOrchestrator(db)
    task = orch.create_task(body.project_id, body.task_type, body.parameters)
    log_audit(db, body.project_id, "create_task", {"task_type": body.task_type}, task.id)
    background_tasks.add_task(run_skill_task, task.id)
    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    orch = TaskOrchestrator(db)
    task = orch.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
def list_project_tasks(project_id: int, db: Session = Depends(get_db)):
    orch = TaskOrchestrator(db)
    tasks = orch.get_project_tasks(project_id)
    return TaskListResponse(tasks=tasks)


@router.post("/tasks/{task_id}/rerun", response_model=TaskResponse)
def rerun_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    orch = TaskOrchestrator(db)
    old = orch.get_task(task_id)
    if not old:
        raise HTTPException(status_code=404, detail="Task not found")
    new_task = orch.create_task(old.project_id, old.task_type, json.loads(old.input_json).get("parameters", {}))
    log_audit(db, old.project_id, "rerun_task", {"original_task_id": task_id}, new_task.id)
    background_tasks.add_task(run_skill_task, new_task.id)
    return new_task


@router.post("/projects/{project_id}/pipeline/run-all", response_model=TaskListResponse)
def run_full_pipeline(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    orch = TaskOrchestrator(db)

    def run_pipeline():
        from backend.app.database import SessionLocal
        pdb = SessionLocal()
        try:
            for tt in TASK_DEPENDENCY_ORDER:
                porc = TaskOrchestrator(pdb)
                task = porc.create_task(project_id, tt)
                porc.mark_running(task.id)
                from backend.app.tasks.base import dispatch_skill
                dispatch_skill(task, pdb)
                updated = porc.get_task(task.id)
                if updated.status == "failed":
                    break
        finally:
            pdb.close()

    background_tasks.add_task(run_pipeline)
    log_audit(db, project_id, "run_full_pipeline")
    return TaskListResponse(tasks=orch.get_project_tasks(project_id))
