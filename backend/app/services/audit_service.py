import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog


def log_audit(db: Session, project_id: int, action: str, detail: dict = None, task_id: int = None):
    entry = AuditLog(
        project_id=project_id,
        task_id=task_id,
        action=action,
        detail_json=json.dumps(detail or {}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
