import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.sample import Sample
from backend.app.models.file_asset import FileAsset
from backend.app.services.storage_service import StorageService
from backend.app.services.audit_service import log_audit
from backend.app.schemas.project import ProjectResponse

router = APIRouter(tags=["demo"])


@router.post("/demo/seed", response_model=ProjectResponse, status_code=201)
def seed_demo(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    project = Project(
        name="Demo - Liver PDFF and Osteoporosis",
        research_goal="Investigate the causal relationship between liver fat (Liver PDFF) and osteoporosis risk, with mediation analysis through plasma proteins.",
        exposure="Liver_PDFF",
        outcome="Osteoporosis",
        mediator_set="deCODE plasma proteins",
        status="active",
        created_at=now, updated_at=now,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    storage = StorageService(db)
    storage.ensure_dirs(project.id)

    mock_files = [
        ("mock_mri_001.nii.gz", "mri"),
        ("mock_phenotype.csv", "phenotype"),
        ("mock_covariates.csv", "covariates"),
        ("mock_lead_snps.csv", "genotype"),
    ]
    for fname, ftype in mock_files:
        asset = FileAsset(
            project_id=project.id,
            file_name=fname,
            file_type=ftype,
            file_path=f"projects/{project.id}/raw/{ftype}/{fname}",
            file_size=1024,
            created_at=now,
        )
        db.add(asset)

    sample = Sample(
        project_id=project.id,
        subject_id="DEMO_001",
        mri_file_path=f"storage/projects/{project.id}/raw/mri/mock_mri_001.nii.gz",
        phenotype_file_path=f"storage/projects/{project.id}/raw/phenotype/mock_phenotype.csv",
        covariate_file_path=f"storage/projects/{project.id}/raw/covariates/mock_covariates.csv",
        genotype_file_path=f"storage/projects/{project.id}/raw/genotype/mock_lead_snps.csv",
        qc_status="passed",
        created_at=now,
    )
    db.add(sample)
    db.commit()

    log_audit(db, project.id, "seed_demo", {"demo": True})
    return project
