import json
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.task import (
    TaskCreate, TaskResponse, TaskListResponse, PaginatedTaskResponse,
    UnifiedJobResponse, UnifiedJobListResponse, STATUS_NORMALIZE_MAP,
)
from backend.app.services.task_orchestrator import TaskOrchestrator, TASK_DEPENDENCY_ORDER
from backend.app.services.audit_service import log_audit

logger = logging.getLogger("adipoinsight.tasks_api")

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


@router.get("/projects/{project_id}/tasks")
def list_project_tasks(
    project_id: int,
    page: int = 1,
    page_size: int = 0,       # 0 = unpaginated (backward compat)
    status: str = "",
    type: str = "",
    updated_after: str = "",  # ISO datetime string
    latest_only: bool = False, # return only latest per task_type
    db: Session = Depends(get_db),
):
    """
    项目任务列表（v0.3.0 新增分页 & 轻量轮询参数）。

    - page=1&page_size=7: 第一页 7 条
    - page_size=0: 返回全部（向后兼容旧格式）
    - status=running: 只过滤运行中的任务
    - type=gwas_analysis: 只过滤 GWAS 任务
    - updated_after=2026-05-19T12:00:00Z: 只返回此后更新的任务
    - latest_only=true: 每种 task_type 只返回最新一条（轮询优化首选）
    """
    from datetime import datetime as dt
    from backend.app.models.analysis_task import AnalysisTask

    q = db.query(AnalysisTask).filter(AnalysisTask.project_id == project_id)

    # 可选过滤
    if status:
        q = q.filter(AnalysisTask.status == status)
    if type:
        q = q.filter(AnalysisTask.task_type == type)
    if updated_after:
        try:
            ts = dt.fromisoformat(updated_after.replace("Z", "+00:00"))
            q = q.filter(AnalysisTask.updated_at > ts)
        except (ValueError, TypeError):
            pass

    # latest_only: 每种 task_type 只取最新
    if latest_only:
        from sqlalchemy import func, and_
        subq = (
            db.query(
                AnalysisTask.task_type,
                func.max(AnalysisTask.updated_at).label("max_updated"),
            )
            .filter(AnalysisTask.project_id == project_id)
            .group_by(AnalysisTask.task_type)
            .subquery()
        )
        q = q.join(
            subq,
            and_(
                AnalysisTask.task_type == subq.c.task_type,
                AnalysisTask.updated_at == subq.c.max_updated,
            ),
        )

    q = q.order_by(AnalysisTask.updated_at.desc())

    # 分页 / 全量
    if page_size > 0:
        total = q.count()
        offset = (page - 1) * page_size
        task_list = q.offset(offset).limit(page_size).all()
        latest = task_list[0].updated_at if task_list else None
        return PaginatedTaskResponse(
            items=[TaskResponse.model_validate(t) for t in task_list],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(offset + page_size) < total,
            latest_updated_at=latest,
        )

    # 向后兼容：全量返回
    task_list = q.all()
    return TaskListResponse(tasks=task_list)


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


# ===== 统一任务查询 Adapter (v0.3.0) =====

def _adapt_analysis_task(task) -> UnifiedJobResponse:
    """将 AnalysisTask ORM 对象转换为 UnifiedJobResponse"""
    input_data: Dict[str, Any] = {}
    try:
        input_data = json.loads(task.input_json) if task.input_json else {}
    except (json.JSONDecodeError, TypeError):
        pass

    return UnifiedJobResponse(
        job_id=f"task-{task.id}",
        project_id=task.project_id,
        job_type=task.task_type,
        pipeline_step=task.task_type,
        status=STATUS_NORMALIZE_MAP.get(task.status, task.status),
        progress=task.progress,
        progress_stage="",
        input=input_data,
        result=None,
        error_code=task.error_code or "",
        error_message=task.error_message or "",
        created_at=task.created_at.isoformat() if task.created_at else None,
        updated_at=task.updated_at.isoformat() if task.updated_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        finished_at=task.finished_at.isoformat() if task.finished_at else None,
        source="analysis_task",
    )


def _adapt_job_manager_job(job_dict: Dict[str, Any]) -> UnifiedJobResponse:
    """将 JobManager.to_dict() 输出转换为 UnifiedJobResponse"""
    return UnifiedJobResponse(
        job_id=f"job-{job_dict.get('job_id', '')}",
        project_id=job_dict.get("project_id", 0),
        job_type=job_dict.get("capability_type", "unknown"),
        pipeline_step=job_dict.get("capability_type", "unknown"),
        status=STATUS_NORMALIZE_MAP.get(job_dict.get("status", ""), job_dict.get("status", "queued")),
        progress=job_dict.get("progress", 0),
        progress_stage=job_dict.get("progress_stage", ""),
        input=job_dict.get("input", {}),
        result=job_dict.get("result"),
        error_code=job_dict.get("error_code", ""),
        error_message=job_dict.get("error_message", ""),
        created_at=job_dict.get("created_at"),
        updated_at=job_dict.get("updated_at"),
        started_at=job_dict.get("started_at"),
        finished_at=job_dict.get("finished_at"),
        source="ai_job",
    )


def _collect_unified_jobs(project_id: int, db: Session) -> List[UnifiedJobResponse]:
    """统一收集 AnalysisTask + JobManager Job，返回 UnifiedJobResponse 列表"""
    jobs: List[UnifiedJobResponse] = []

    # 1. 从 AnalysisTask (SQLite) 收集
    try:
        orch = TaskOrchestrator(db)
        tasks = orch.get_project_tasks(project_id)
        for t in tasks:
            jobs.append(_adapt_analysis_task(t))
    except Exception as exc:
        logger.warning("Failed to collect AnalysisTask jobs: %s", exc)

    # 2. 从 JobManager (内存) 收集
    try:
        from backend.app.ai.job_manager import job_manager as jm
        jm_jobs = jm.list_jobs(project_id=project_id)
        for j in jm_jobs:
            d = j.to_dict()
            # 去重: 如果 AnalysisTask 已记录同一 task_type，则跳过 JobManager 中的旧记录
            # (AnalysisTask 是旧系统的权威来源)
            job_type = d.get("capability_type", "")
            already_covered = any(
                u.source == "analysis_task" and u.job_type == job_type
                for u in jobs
            )
            if not already_covered:
                jobs.append(_adapt_job_manager_job(d))
    except Exception as exc:
        logger.warning("Failed to collect JobManager jobs: %s", exc)

    # 按 created_at 倒序
    jobs.sort(key=lambda j: j.created_at or "", reverse=True)
    return jobs


@router.get("/projects/{project_id}/jobs/unified", response_model=UnifiedJobListResponse)
def list_unified_jobs(project_id: int, db: Session = Depends(get_db)):
    """
    统一任务查询 — 合并 AnalysisTask 和 JobManager Job。

    返回标准化的 UnifiedJobResponse 列表，包含:
    - source: "analysis_task" 或 "ai_job"
    - status: 统一归一化值 (queued | running | succeeded | failed | cancelled)
    - source_stats: 各来源的任务数统计

    这是阶段 1 兼容层。前端可逐步迁移至此接口。
    """
    jobs = _collect_unified_jobs(project_id, db)

    source_stats: Dict[str, int] = {}
    for j in jobs:
        source_stats[j.source] = source_stats.get(j.source, 0) + 1

    return UnifiedJobListResponse(jobs=jobs, source_stats=source_stats)
