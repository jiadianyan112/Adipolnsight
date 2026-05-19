"""
报告 API Router — /api/v1/reports/*

自 v0.3.0 起：POST /projects/{id}/reports/generate 统一委托到
JobManager + ReportGenerationSkill，不再独立执行 BackgroundTasks。

旧 ReportService.generate() 标记为 deprecated，仅供内部迁移参考。
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.report import Report
from backend.app.schemas.report import ReportResponse

logger = logging.getLogger("adipoinsight.reports_api")

router = APIRouter(tags=["reports"])


@router.post("/projects/{project_id}/reports/generate")
def generate_report(project_id: int, db: Session = Depends(get_db)):
    """
    统一报告生成入口。

    委托到 JobManager 创建 report_generation Job 并立即返回 job_id。
    前端应使用 GET /api/ai/jobs/{job_id} 轮询状态，
    完成后调用 GET /api/ai/jobs/{job_id}/result 获取完整报告。

    v0.3.0 变更：不再使用 BackgroundTasks + ReportService 独立执行。
    返回结构保持向后兼容：仍创建 Report draft 记录，但实际生成由 JobManager 负责。
    """
    from backend.app.ai.job_manager import job_manager as jm
    from backend.app.ai.registry import registry

    if not registry.has("report_generation"):
        raise HTTPException(
            status_code=500,
            detail="report_generation skill not registered",
        )

    # 创建 draft Report（向后兼容）
    report = Report(
        project_id=project_id,
        title="科研分析报告",
        status="generating",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 创建并启动 JobManager 任务
    try:
        job = jm.create_job(
            capability_type="report_generation",
            input_data={
                "project_id": project_id,
                "report_type": "full",
                "language": "zh-CN",
                "include_figures": True,
                "include_tables": True,
                "include_ai_interpretation": True,
            },
            project_id=project_id,
        )
        jm.run_job(job.job_id)

        logger.info(
            "[Reports API] Report job started via JobManager: job_id=%s project_id=%s report_id=%s",
            job.job_id, project_id, report.id,
        )
    except Exception as exc:
        logger.error("[Reports API] Failed to create report job: %s", exc)
        report.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create report job: {str(exc)}",
        )

    return {
        "report_id": report.id,
        "project_id": project_id,
        "job_id": job.job_id,
        "status": "generating",
        "message": "报告生成任务已提交。请通过 GET /api/ai/jobs/{job_id} 轮询状态。",
    }


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
