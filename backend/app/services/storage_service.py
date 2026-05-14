import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.config import STORAGE_DIR
from backend.app.models.file_asset import FileAsset


class StorageService:
    def __init__(self, db: Session):
        self.db = db

    def get_project_root(self, project_id: int) -> Path:
        return STORAGE_DIR / "projects" / str(project_id)

    def get_output_dir(self, project_id: int, task_type: str) -> Path:
        return self.get_project_root(project_id) / "outputs" / task_type

    def ensure_dirs(self, project_id: int):
        root = self.get_project_root(project_id)
        for sub in ["raw/mri", "raw/phenotype", "raw/covariates", "raw/genotype",
                     "outputs/segmentation", "outputs/gwas", "outputs/opengwas",
                     "outputs/mr", "outputs/mediation_mr", "outputs/risk_modeling", "outputs/report"]:
            (root / sub).mkdir(parents=True, exist_ok=True)

    def save_upload(self, file, project_id: int, file_type: str) -> FileAsset:
        self.ensure_dirs(project_id)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{file_type}_{file.filename}"
        dest_dir = self.get_project_root(project_id) / "raw" / file_type
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        rel_path = str(dest_path.relative_to(STORAGE_DIR))
        asset = FileAsset(
            project_id=project_id,
            file_name=file.filename,
            file_type=file_type,
            file_path=rel_path,
            file_size=dest_path.stat().st_size,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def list_project_files(self, project_id: int) -> list[FileAsset]:
        return self.db.query(FileAsset).filter(FileAsset.project_id == project_id).all()

    def get_file_path(self, file_id: int) -> Path:
        asset = self.db.query(FileAsset).filter(FileAsset.id == file_id).first()
        if not asset:
            return None
        return STORAGE_DIR / asset.file_path
