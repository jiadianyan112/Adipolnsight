from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.app.database import Base


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    subject_id = Column(String(64), default="")
    mri_file_path = Column(String(512), default="")
    phenotype_file_path = Column(String(512), default="")
    covariate_file_path = Column(String(512), default="")
    genotype_file_path = Column(String(512), default="")
    qc_status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
