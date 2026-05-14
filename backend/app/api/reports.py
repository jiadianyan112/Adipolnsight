from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.report import Report
from backend.app.schemas.report import ReportResponse
from backend.app.services.audit_service import log_audit

router = APIRouter(tags=["reports"])


@router.post("/projects/{project_id}/reports/generate", response_model=ReportResponse, status_code=201)
def generate_report(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    def _gen():
        from backend.app.database import SessionLocal
        rdb = SessionLocal()
        try:
            from backend.app.services.report_service import ReportService
            svc = ReportService(rdb)
            svc.generate(project_id)
        finally:
            rdb.close()

    background_tasks.add_task(_gen)
    report = Report(project_id=project_id, title="Analysis Report", status="draft")
    db.add(report)
    db.commit()
    db.refresh(report)
    log_audit(db, project_id, "generate_report", detail={"report_id": report.id})
    return report


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
