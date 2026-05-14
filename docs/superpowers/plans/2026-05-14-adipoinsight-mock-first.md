# AdipoInsight Mock-First MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a demonstrable end-to-end medical research AI platform with real engineering skeleton + mock analysis scripts.

**Architecture:** FastAPI backend with SQLite, Vite+React frontend with Zustand, 7 independent mock Python CLI scripts called via subprocess by a task orchestrator. Unified result viewer component adapts rendering based on result_type.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, SQLite, BackgroundTasks | Vite, React 18, TypeScript, Tailwind CSS, Zustand, Axios, Recharts, react-markdown

**Spec:** `docs/superpowers/specs/2026-05-14-adipoinsight-mock-first-design.md`

---

## Phase 1: Project Scaffolding & Backend Foundation

### Task 1.1: Initialize Git repository and project root

**Files:**
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Initialize git**

```bash
cd /mnt/e/Adipolnsight && git init
```

- [ ] **Step 2: Write .gitignore**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
*.db

# Node
node_modules/
dist/

# IDE
.vscode/
.idea/

# Env
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Storage (runtime)
storage/
```

- [ ] **Step 3: Write README.md**

```markdown
# AdipoInsight

医学科研 AI 分析平台 — Mock-First MVP

## 快速启动

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 一键 Demo

1. 打开 http://localhost:5173
2. 点击 "一键创建 Demo 项目"
3. 进入工作台，点击 "Run Full Pipeline"
4. 查看各步骤结果，生成科研报告

## 技术栈

- 后端: FastAPI + SQLAlchemy + SQLite
- 前端: Vite + React + TypeScript + Tailwind CSS + Zustand
- 分析: Python mock CLI scripts

## 文档

- [架构设计](docs/architecture.md)
- [API 文档](docs/api.md)
- [Mock Skills](docs/mock_skills.md)
- [真实模块替换](docs/real_module_replacement.md)
```

- [ ] **Step 4: Create directory structure**

```bash
cd /mnt/e/Adipolnsight && mkdir -p \
  backend/app/api \
  backend/app/models \
  backend/app/schemas \
  backend/app/services \
  backend/app/tasks \
  backend/app/utils \
  backend/scripts \
  analysis_scripts/segmentation \
  analysis_scripts/gwas \
  analysis_scripts/opengwas \
  analysis_scripts/mr \
  analysis_scripts/mediation_mr \
  analysis_scripts/risk_modeling \
  analysis_scripts/report \
  mock_data/mri \
  mock_data/phenotype \
  mock_data/covariates \
  mock_data/genetics \
  docs
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore README.md && git commit -m "feat: initialize project with README and .gitignore"
```

---

### Task 1.2: Create backend package structure and dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pydantic==2.10.4
python-multipart==0.0.19
pandas==2.2.3
aiosqlite==0.20.0
```

- [ ] **Step 2: Write config.py**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
MOCK_DATA_DIR = BASE_DIR / "mock_data"
ANALYSIS_SCRIPTS_DIR = BASE_DIR / "analysis_scripts"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/adipoinsight.db")
SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "").replace("sqlite+aiosqlite", "sqlite")
```

- [ ] **Step 3: Write database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.app.config import SYNC_DATABASE_URL

engine = create_engine(SYNC_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.app.models import project, sample, file_asset, analysis_task, analysis_result, report, audit_log  # noqa
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: Write main.py with health endpoint and lifespan**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database import init_db
from backend.app.api import projects, files, tasks, results, reports, demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AdipoInsight", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 5: Create __init__.py files**

```bash
touch backend/__init__.py \
      backend/app/__init__.py \
      backend/app/api/__init__.py \
      backend/app/models/__init__.py \
      backend/app/schemas/__init__.py \
      backend/app/services/__init__.py \
      backend/app/tasks/__init__.py \
      backend/app/utils/__init__.py
```

- [ ] **Step 6: Verify backend starts**

```bash
cd /mnt/e/Adipolnsight && python -c "from backend.app.main import app; print('OK')"
```

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat: backend scaffolding with FastAPI, config, database, health endpoint"
```

---

## Phase 2: Data Models & Pydantic Schemas

### Task 2.1: Create all SQLAlchemy models

**Files:**
- Create: `backend/app/models/project.py`
- Create: `backend/app/models/sample.py`
- Create: `backend/app/models/file_asset.py`
- Create: `backend/app/models/analysis_task.py`
- Create: `backend/app/models/analysis_result.py`
- Create: `backend/app/models/report.py`
- Create: `backend/app/models/audit_log.py`

- [ ] **Step 1: Write project.py**

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    research_goal = Column(Text, default="")
    exposure = Column(String(255), default="")
    outcome = Column(String(255), default="")
    mediator_set = Column(String(255), default="")
    status = Column(String(32), default="draft")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Write sample.py**

```python
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
```

- [ ] **Step 3: Write file_asset.py**

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.app.database import Base


class FileAsset(Base):
    __tablename__ = "file_assets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(64), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Write analysis_task.py**

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.app.database import Base


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_type = Column(String(64), nullable=False)
    task_name = Column(String(255), default="")
    status = Column(String(32), default="pending")
    progress = Column(Integer, default=0)
    input_json = Column(Text, default="{}")
    output_json = Column(Text, default="{}")
    error_code = Column(String(64), default="")
    error_message = Column(Text, default="")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 5: Write analysis_result.py**

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    result_type = Column(String(64), nullable=False)
    summary_json = Column(Text, default="{}")
    output_files_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 6: Write report.py**

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), default="")
    content_markdown = Column(Text, default="")
    status = Column(String(32), default="draft")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 7: Write audit_log.py**

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=True)
    action = Column(String(128), nullable=False)
    detail_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 8: Verify models create tables**

```bash
cd /mnt/e/Adipolnsight && python -c "
import sys; sys.path.insert(0,'.')
from backend.app.database import init_db; init_db()
print('Tables created')
"
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/ && git commit -m "feat: add all 7 SQLAlchemy models"
```

---

### Task 2.2: Create all Pydantic schemas

**Files:**
- Create: `backend/app/schemas/project.py`
- Create: `backend/app/schemas/task.py`
- Create: `backend/app/schemas/result.py`
- Create: `backend/app/schemas/report.py`
- Create: `backend/app/schemas/file.py`

- [ ] **Step 1: Write project.py schemas**

```python
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    research_goal: str = ""
    exposure: str = ""
    outcome: str = ""
    mediator_set: str = ""


class ProjectResponse(BaseModel):
    id: int
    name: str
    research_goal: str
    exposure: str
    outcome: str
    mediator_set: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
```

- [ ] **Step 2: Write task.py schemas**

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


TASK_TYPES = [
    "image_segmentation", "gwas_analysis", "opengwas_fetch",
    "mendelian_randomization", "mediation_mr", "risk_modeling", "report_generation",
]

TASK_TYPE_NAMES = {
    "image_segmentation": "AI Image Segmentation",
    "gwas_analysis": "GWAS Analysis",
    "opengwas_fetch": "OpenGWAS Data Fetch",
    "mendelian_randomization": "Mendelian Randomization",
    "mediation_mr": "Mediation MR",
    "risk_modeling": "Risk Modeling",
    "report_generation": "Report Generation",
}


class TaskCreate(BaseModel):
    project_id: int
    task_type: str = Field(..., pattern="^(image_segmentation|gwas_analysis|opengwas_fetch|mendelian_randomization|mediation_mr|risk_modeling|report_generation)$")
    parameters: dict = {}


class TaskResponse(BaseModel):
    id: int
    project_id: int
    task_type: str
    task_name: str
    status: str
    progress: int
    input_json: str
    output_json: str
    error_code: str
    error_message: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
```

- [ ] **Step 3: Write result.py schemas**

```python
from datetime import datetime
from pydantic import BaseModel


class ResultResponse(BaseModel):
    id: int
    task_id: int
    project_id: int
    result_type: str
    summary_json: str
    output_files_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectResultsResponse(BaseModel):
    project_id: int
    results: list[ResultResponse]
```

- [ ] **Step 4: Write report.py schemas**

```python
from datetime import datetime
from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: int
    project_id: int
    title: str
    content_markdown: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Write file.py schemas**

```python
from datetime import datetime
from pydantic import BaseModel


class FileResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_type: str
    file_path: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    files: list[FileResponse]
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/ && git commit -m "feat: add Pydantic schemas for all models"
```

---

## Phase 3: Backend API Routes

### Task 3.1: Projects API

**Files:**
- Create: `backend/app/api/projects.py`
- Create: `backend/app/services/audit_service.py`

- [ ] **Step 1: Write audit_service.py**

```python
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
```

- [ ] **Step 2: Write projects.py**

```python
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
```

- [ ] **Step 3: Verify the API**

```bash
cd /mnt/e/Adipolnsight/backend && python -c "
from app.main import app
from fastapi.testclient import TestClient
# Just verify import
print('Projects API loaded OK')
"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/projects.py backend/app/services/audit_service.py && git commit -m "feat: add projects CRUD API with audit logging"
```

---

### Task 3.2: Files API & StorageService

**Files:**
- Create: `backend/app/services/storage_service.py`
- Create: `backend/app/api/files.py`

- [ ] **Step 1: Write storage_service.py**

```python
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
```

- [ ] **Step 2: Write files.py**

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.storage_service import StorageService
from backend.app.schemas.file import FileResponse as FileResp, FileListResponse
from backend.app.services.audit_service import log_audit

router = APIRouter(tags=["files"])


@router.post("/projects/{project_id}/files", response_model=FileResp, status_code=201)
def upload_file(
    project_id: int, file: UploadFile = File(...),
    file_type: str = Form(default="mri"),
    db: Session = Depends(get_db),
):
    storage = StorageService(db)
    asset = storage.save_upload(file, project_id, file_type)
    log_audit(db, project_id, "upload_file", {"file_name": asset.file_name, "file_type": file_type})
    return asset


@router.get("/projects/{project_id}/files", response_model=FileListResponse)
def list_files(project_id: int, db: Session = Depends(get_db)):
    storage = StorageService(db)
    files = storage.list_project_files(project_id)
    return FileListResponse(files=files)


@router.get("/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    storage = StorageService(db)
    path = storage.get_file_path(file_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path))
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/storage_service.py backend/app/api/files.py && git commit -m "feat: add file upload/download API with StorageService"
```

---

### Task 3.3: Tasks API & TaskOrchestrator

**Files:**
- Create: `backend/app/services/task_orchestrator.py`
- Create: `backend/app/api/tasks.py`

- [ ] **Step 1: Write task_orchestrator.py**

```python
import json
from datetime import datetime, timezone
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.models.analysis_task import AnalysisTask
from backend.app.models.analysis_result import AnalysisResult
from backend.app.schemas.task import TASK_TYPE_NAMES, TASK_TYPES

TASK_DEPENDENCY_ORDER = [
    "image_segmentation", "gwas_analysis", "opengwas_fetch",
    "mendelian_randomization", "mediation_mr", "risk_modeling", "report_generation",
]


class TaskOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, project_id: int, task_type: str, parameters: dict = None) -> AnalysisTask:
        params = parameters or {}
        task = AnalysisTask(
            project_id=project_id,
            task_type=task_type,
            task_name=TASK_TYPE_NAMES.get(task_type, task_type),
            status="pending",
            progress=0,
            input_json=json.dumps({"project_id": project_id, "task_type": task_type, "parameters": params}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_progress(self, task_id: int, progress: int, status: str = None):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if task:
            task.progress = progress
            if status:
                task.status = status
            task.updated_at = datetime.now(timezone.utc)
            self.db.commit()

    def mark_running(self, task_id: int):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        task.progress = 10
        task.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def mark_success(self, task_id: int, output: dict):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        task.status = "success"
        task.progress = 100
        task.output_json = json.dumps(output.get("summary", {}))
        task.finished_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        result = AnalysisResult(
            task_id=task.id, project_id=task.project_id, result_type=task.task_type,
            summary_json=json.dumps(output.get("summary", {})),
            output_files_json=json.dumps(output.get("output_files", [])),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(result)
        self.db.commit()

    def mark_failed(self, task_id: int, error_code: str, error_message: str):
        task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        task.status = "failed"
        task.progress = 0
        task.error_code = error_code
        task.error_message = error_message
        task.finished_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def get_project_tasks(self, project_id: int) -> list[AnalysisTask]:
        return self.db.query(AnalysisTask).filter(
            AnalysisTask.project_id == project_id
        ).order_by(AnalysisTask.created_at.desc()).all()

    def get_task(self, task_id: int) -> AnalysisTask:
        return self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

    def get_next_task_type(self, project_id: int) -> str | None:
        existing = self.db.query(AnalysisTask.task_type).filter(
            AnalysisTask.project_id == project_id
        ).all()
        done = {t[0] for t in existing}
        for tt in TASK_DEPENDENCY_ORDER:
            if tt not in done:
                return tt
        return None
```

- [ ] **Step 2: Write tasks.py**

```python
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.task import TaskCreate, TaskResponse, TaskListResponse, TASK_DEPENDENCY_ORDER
from backend.app.services.task_orchestrator import TaskOrchestrator
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
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/task_orchestrator.py backend/app/api/tasks.py && git commit -m "feat: add task API with orchestrator and pipeline support"
```

---

### Task 3.4: Results & Reports & Demo API

**Files:**
- Create: `backend/app/api/results.py`
- Create: `backend/app/api/reports.py`
- Create: `backend/app/api/demo.py`

- [ ] **Step 1: Write results.py**

```python
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
```

- [ ] **Step 2: Write reports.py**

```python
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
    log_audit(db, project_id, "generate_report", report_id=report.id)
    return report


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
```

- [ ] **Step 3: Write demo.py**

```python
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
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/results.py backend/app/api/reports.py backend/app/api/demo.py && git commit -m "feat: add results, reports, and demo seed API endpoints"
```

---

## Phase 4: Task Execution Engine

### Task 4.1: BaseSkillRunner + 7 Skill Runners

**Files:**
- Create: `backend/app/tasks/base.py`
- Create: `backend/app/tasks/segmentation.py`
- Create: `backend/app/tasks/gwas.py`
- Create: `backend/app/tasks/opengwas.py`
- Create: `backend/app/tasks/mr.py`
- Create: `backend/app/tasks/mediation_mr.py`
- Create: `backend/app/tasks/risk_modeling.py`
- Create: `backend/app/tasks/report_gen.py`

- [ ] **Step 1: Write base.py with dispatch_skill**

```python
import json
import subprocess
import uuid
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.config import ANALYSIS_SCRIPTS_DIR, STORAGE_DIR
from backend.app.models.analysis_task import AnalysisTask
from backend.app.services.task_orchestrator import TaskOrchestrator


class BaseSkillRunner:
    task_type: str
    script_path: str

    def prepare_inputs(self, task: AnalysisTask) -> dict:
        return json.loads(task.input_json)

    def build_command(self, inputs: dict) -> list[str]:
        return ["python", str(ANALYSIS_SCRIPTS_DIR / self.script_path)]

    def run(self, cmd: list[str], cwd: str = None) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=cwd)

    def parse_outputs(self, stdout: str) -> dict:
        lines = stdout.strip().split("\n")
        last_line = lines[-1] if lines else "{}"
        return json.loads(last_line)

    def execute(self, task: AnalysisTask, orch: TaskOrchestrator, db: Session):
        orch.update_progress(task.id, 10)
        inputs = self.prepare_inputs(task)
        orch.update_progress(task.id, 20)
        cmd = self.build_command(inputs)
        out_dir = STORAGE_DIR / "projects" / str(task.project_id) / "outputs" / task.task_type
        out_dir.mkdir(parents=True, exist_ok=True)
        orch.update_progress(task.id, 30)

        try:
            result = self.run(cmd, cwd=str(out_dir))
        except subprocess.TimeoutExpired:
            orch.mark_failed(task.id, "TASK_TIMEOUT", "Task exceeded 300s limit")
            return
        except FileNotFoundError:
            orch.mark_failed(task.id, "SCRIPT_NOT_FOUND", f"Script not found: {self.script_path}")
            return

        log_dir = out_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "run.log").write_text(result.stdout + "\n" + result.stderr)
        (log_dir / "command.txt").write_text(" ".join(cmd))

        orch.update_progress(task.id, 70)

        if result.returncode != 0:
            orch.mark_failed(task.id, "SCRIPT_EXECUTION_FAILED", result.stderr[:500])
            return

        try:
            output = self.parse_outputs(result.stdout)
        except (json.JSONDecodeError, IndexError):
            orch.mark_failed(task.id, "OUTPUT_JSON_INVALID", "Failed to parse stdout JSON")
            return

        orch.update_progress(task.id, 90)
        orch.mark_success(task.id, output)


RUNNER_REGISTRY = {}


def register(runner_cls):
    inst = runner_cls()
    RUNNER_REGISTRY[inst.task_type] = inst
    return runner_cls


def dispatch_skill(task: AnalysisTask, db: Session):
    orch = TaskOrchestrator(db)
    runner = RUNNER_REGISTRY.get(task.task_type)
    if not runner:
        orch.mark_failed(task.id, "SCRIPT_NOT_FOUND", f"No runner for {task.task_type}")
        return
    runner.execute(task, orch, db)
```

- [ ] **Step 2: Write segmentation.py runner**

```python
from backend.app.tasks.base import BaseSkillRunner, register


@register
class SegmentationSkillRunner(BaseSkillRunner):
    task_type = "image_segmentation"
    script_path = "segmentation/mock_segmentation.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        out_dir = f"storage/projects/{project_id}/outputs/segmentation"
        return [
            "python", str(self.script_path),
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
```

- [ ] **Step 3: Write gwas.py runner**

```python
from backend.app.tasks.base import BaseSkillRunner, register


@register
class GWASSkillRunner(BaseSkillRunner):
    task_type = "gwas_analysis"
    script_path = "gwas/mock_gwas.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        phenotype = params.get("phenotype", "Liver_PDFF")
        out_dir = f"storage/projects/{project_id}/outputs/gwas"
        return [
            "python", str(self.script_path),
            "--phenotype", phenotype,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
```

- [ ] **Step 4: Write opengwas.py runner**

```python
from backend.app.tasks.base import BaseSkillRunner, register


@register
class OpenGWASSkillRunner(BaseSkillRunner):
    task_type = "opengwas_fetch"
    script_path = "opengwas/mock_opengwas_fetch.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        outcome_id = params.get("outcome_id", "ukb-b-12141")
        out_dir = f"storage/projects/{project_id}/outputs/opengwas"
        return [
            "python", str(self.script_path),
            "--outcome-id", outcome_id,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
```

- [ ] **Step 5: Write mr.py, mediation_mr.py, risk_modeling.py runners**

```python
# mr.py
from backend.app.tasks.base import BaseSkillRunner, register


@register
class MRSkillRunner(BaseSkillRunner):
    task_type = "mendelian_randomization"
    script_path = "mr/mock_mr.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        exposure = params.get("exposure", "Liver_PDFF")
        outcome = params.get("outcome", "Osteoporosis")
        out_dir = f"storage/projects/{project_id}/outputs/mr"
        return [
            "python", str(self.script_path),
            "--exposure", exposure,
            "--outcome", outcome,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]


# mediation_mr.py
@register
class MediationMRSkillRunner(BaseSkillRunner):
    task_type = "mediation_mr"
    script_path = "mediation_mr/mock_mediation_mr.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        exposure = params.get("exposure", "Liver_PDFF")
        outcome = params.get("outcome", "Osteoporosis")
        out_dir = f"storage/projects/{project_id}/outputs/mediation_mr"
        return [
            "python", str(self.script_path),
            "--exposure", exposure,
            "--outcome", outcome,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]


# risk_modeling.py
@register
class RiskModelSkillRunner(BaseSkillRunner):
    task_type = "risk_modeling"
    script_path = "risk_modeling/mock_risk_modeling.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        exposure = params.get("exposure", "Liver_PDFF")
        outcome = params.get("outcome", "Osteoporosis")
        out_dir = f"storage/projects/{project_id}/outputs/risk_modeling"
        return [
            "python", str(self.script_path),
            "--exposure", exposure,
            "--outcome", outcome,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
```

- [ ] **Step 6: Write report_gen.py runner**

```python
from backend.app.tasks.base import BaseSkillRunner, register


@register
class ReportSkillRunner(BaseSkillRunner):
    task_type = "report_generation"
    script_path = "report/mock_report.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        out_dir = f"storage/projects/{project_id}/outputs/report"
        return [
            "python", str(self.script_path),
            "--project-id", str(project_id),
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
```

- [ ] **Step 7: Verify all runners register**

```bash
cd /mnt/e/Adipolnsight && python -c "
import sys; sys.path.insert(0,'.')
from backend.app.tasks.base import RUNNER_REGISTRY
from backend.app.tasks.segmentation import SegmentationSkillRunner
from backend.app.tasks.gwas import GWASSkillRunner
from backend.app.tasks.opengwas import OpenGWASSkillRunner
from backend.app.tasks.mr import MRSkillRunner
from backend.app.tasks.mediation_mr import MediationMRSkillRunner
from backend.app.tasks.risk_modeling import RiskModelSkillRunner
from backend.app.tasks.report_gen import ReportSkillRunner
assert len(RUNNER_REGISTRY) == 7, f'Expected 7, got {len(RUNNER_REGISTRY)}'
print('All 7 runners registered:', list(RUNNER_REGISTRY.keys()))
"
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/tasks/ && git commit -m "feat: add BaseSkillRunner + 7 task runners with subprocess execution"
```

---

### Task 4.2: ReportService

**Files:**
- Create: `backend/app/services/report_service.py`

- [ ] **Step 1: Write report_service.py**

```python
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.report import Report
from backend.app.models.analysis_result import AnalysisResult
from backend.app.models.project import Project


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate(self, project_id: int):
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        results = self.db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id
        ).order_by(AnalysisResult.created_at.asc()).all()

        sections = [
            f"# {project.name} — 科研分析报告\n",
            f"## 1. 项目摘要\n",
            f"- **研究目标**: {project.research_goal}",
            f"- **暴露变量**: {project.exposure}",
            f"- **结局变量**: {project.outcome}",
            f"- **中介变量集**: {project.mediator_set or 'N/A'}",
            f"- **生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        ]

        section_titles = {
            "image_segmentation": "## 2. AI 影像分割与脂肪表型提取",
            "gwas_analysis": "## 3. GWAS 分析结果",
            "opengwas_fetch": "## 4. OpenGWAS 数据获取结果",
            "mendelian_randomization": "## 5. 孟德尔随机化 (MR) 因果推断",
            "mediation_mr": "## 6. Mediation MR 中介蛋白分析",
            "risk_modeling": "## 7. Risk Modeling 风险建模",
        }

        for result in results:
            title = section_titles.get(result.result_type, f"## {result.result_type}")
            sections.append(f"\n{title}\n")
            try:
                summary = json.loads(result.summary_json)
                for k, v in summary.items():
                    sections.append(f"- **{k}**: {v}")
            except json.JSONDecodeError:
                sections.append("_No summary available_")

        sections.append(f"\n## 8. 结论\n")
        sections.append(f"This report presents the mock-first analysis of {project.exposure} → {project.outcome}.\n")
        sections.append(f"\n## 9. Mock-First 限制说明\n")
        sections.append("All analysis results in this report are generated by mock scripts for demonstration purposes. "
                         "They do not reflect real biological findings and should not be used for clinical decisions.\n")

        content = "\n".join(sections)
        report = self.db.query(Report).filter(
            Report.project_id == project_id
        ).order_by(Report.created_at.desc()).first()

        if report:
            report.content_markdown = content
            report.status = "final"
            report.updated_at = datetime.now(timezone.utc)
        else:
            report = Report(
                project_id=project_id,
                title=f"{project.name} — Analysis Report",
                content_markdown=content,
                status="final",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(report)
        self.db.commit()
        return report
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/report_service.py && git commit -m "feat: add ReportService that aggregates all analysis results into markdown"
```

---

## Phase 5: Mock Analysis Scripts

### Task 5.1: All 7 mock scripts

**Files:**
- Create: `analysis_scripts/segmentation/mock_segmentation.py`
- Create: `analysis_scripts/gwas/mock_gwas.py`
- Create: `analysis_scripts/opengwas/mock_opengwas_fetch.py`
- Create: `analysis_scripts/mr/mock_mr.py`
- Create: `analysis_scripts/mediation_mr/mock_mediation_mr.py`
- Create: `analysis_scripts/risk_modeling/mock_risk_modeling.py`
- Create: `analysis_scripts/report/mock_report.py`

- [ ] **Step 1: Write mock_segmentation.py**

```python
#!/usr/bin/env python3
import argparse, json, random, time, sys, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    metrics = {
        "liver_pdff": round(random.uniform(8.0, 15.0), 2),
        "visceral_fat_volume": round(random.uniform(2500, 5000), 1),
        "subcutaneous_fat_volume": round(random.uniform(5000, 8000), 1),
        "bone_marrow_fat_fraction": round(random.uniform(0.25, 0.45), 2),
        "dice_liver": round(random.uniform(0.90, 0.96), 2),
        "dice_visceral_fat": round(random.uniform(0.88, 0.94), 2),
        "dice_subcutaneous_fat": round(random.uniform(0.89, 0.95), 2),
        "dice_bone_marrow": round(random.uniform(0.87, 0.93), 2),
        "qc_status": "passed",
    }

    with open(os.path.join(args.output_dir, "segmentation_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    csv_path = os.path.join(args.output_dir, "fat_quantification.csv")
    with open(csv_path, "w") as f:
        f.write("subject_id,liver_pdff,visceral_fat_volume,subcutaneous_fat_volume,bone_marrow_fat_fraction\n")
        f.write(f"DEMO_001,{metrics['liver_pdff']},{metrics['visceral_fat_volume']},{metrics['subcutaneous_fat_volume']},{metrics['bone_marrow_fat_fraction']}\n")

    # Write placeholder PNG (1x1 white pixel)
    png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    with open(os.path.join(args.output_dir, "overlay_preview.png"), "wb") as f:
        f.write(png)

    print(f"[mock_segmentation] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id,
        "status": "success",
        "summary": metrics,
        "output_files": ["segmentation_metrics.json", "fat_quantification.csv", "overlay_preview.png"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write mock_gwas.py**

```python
#!/usr/bin/env python3
import argparse, json, random, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phenotype", default="Liver_PDFF")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)
    n_snps = 12

    tsv = "SNP\tCHR\tBP\tEA\tOA\tBETA\tSE\tP\n"
    for i in range(n_snps):
        tsv += f"rs{i+1000}\t{random.randint(1,22)}\t{random.randint(100000,250000000)}\tA\tG\t{round(random.uniform(-0.3, 0.3), 4)}\t{round(random.uniform(0.01, 0.05), 4)}\t{random.uniform(1e-8, 1e-4):.2e}\n"

    with open(os.path.join(args.output_dir, "gwas_summary_stats.tsv"), "w") as f:
        f.write(tsv)

    with open(os.path.join(args.output_dir, "lead_snps.csv"), "w") as f:
        f.write("SNP,CHR,BP,P\n")
        f.write("rs1001,3,123456,1.2e-10\n")

    with open(os.path.join(args.output_dir, "significant_loci.csv"), "w") as f:
        f.write("locus,chr,start,end,lead_snp,n_snps\n")
        f.write("1,3,100000,200000,rs1001,50\n")

    summary = {
        "phenotype": args.phenotype,
        "sample_size": 40484,
        "significant_loci_count": 18,
        "lead_snps_count": n_snps,
        "lambda_gc": round(random.uniform(1.00, 1.05), 2),
    }
    with open(os.path.join(args.output_dir, "gwas_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_gwas] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["gwas_summary_stats.tsv", "lead_snps.csv", "significant_loci.csv", "gwas_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write mock_opengwas_fetch.py**

```python
#!/usr/bin/env python3
import argparse, json, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcome-id", default="ukb-b-12141")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    tsv = "SNP\tBETA\tSE\tP\n"
    for i in range(12):
        tsv += f"rs{i+1000}\t0.05\t0.02\t0.04\n"
    with open(os.path.join(args.output_dir, "outcome_summary_stats.tsv"), "w") as f:
        f.write(tsv)

    with open(os.path.join(args.output_dir, "harmonised_preview.csv"), "w") as f:
        f.write("SNP,exposure_beta,outcome_beta,harmonised\n")
        f.write("rs1001,0.05,0.04,True\n")

    summary = {
        "outcome_id": args.outcome_id,
        "outcome_name": "Osteoporosis",
        "matched_snps": 12,
        "proxy_snps_used": 0,
        "source": "Mock IEU OpenGWAS",
    }
    with open(os.path.join(args.output_dir, "opengwas_metadata.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_opengwas] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["outcome_summary_stats.tsv", "harmonised_preview.csv", "opengwas_metadata.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write mock_mr.py**

```python
#!/usr/bin/env python3
import argparse, json, random, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposure", default="Liver_PDFF")
    parser.add_argument("--outcome", default="Osteoporosis")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    beta = round(random.uniform(0.1, 0.3), 3)
    se = round(random.uniform(0.05, 0.1), 3)

    csv = "method,beta,se,or,ci_lower,ci_upper,p_value\n"
    csv += f"IVW,{beta},{se},{round(random.uniform(1.1, 1.4), 2)},{round(random.uniform(1.02, 1.1), 2)},{round(random.uniform(1.2, 1.5), 2)},{random.uniform(0.001, 0.02):.4f}\n"
    with open(os.path.join(args.output_dir, "mr_results.csv"), "w") as f:
        f.write(csv)

    with open(os.path.join(args.output_dir, "heterogeneity.csv"), "w") as f:
        f.write("method,Q,Q_df,Q_pval\nIVW,15.2,10,0.12\n")

    with open(os.path.join(args.output_dir, "pleiotropy.csv"), "w") as f:
        f.write("egger_intercept,se,pval\n0.002,0.004,0.62\n")

    summary = {
        "exposure": args.exposure, "outcome": args.outcome, "method": "IVW",
        "beta": beta, "or": round(random.uniform(1.1, 1.4), 2),
        "ci_lower": round(random.uniform(1.02, 1.1), 2),
        "ci_upper": round(random.uniform(1.2, 1.5), 2),
        "p_value": round(random.uniform(0.001, 0.02), 4),
        "cochran_q_p": round(random.uniform(0.1, 0.5), 2),
        "egger_intercept_p": round(random.uniform(0.3, 0.7), 2),
    }
    with open(os.path.join(args.output_dir, "mr_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_mr] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["mr_results.csv", "heterogeneity.csv", "pleiotropy.csv", "mr_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Write mock_mediation_mr.py**

```python
#!/usr/bin/env python3
import argparse, json, random, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposure", default="Liver_PDFF")
    parser.add_argument("--outcome", default="Osteoporosis")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    proteins = ["ACY1", "H6PD", "SHBG", "ADH1A", "POR", "NAAA"]
    csv = "protein,beta_a,beta_b,indirect_effect,proportion_mediated,p_mediation\n"
    top_mediators = []
    for p in proteins:
        ba = round(random.uniform(0.01, 0.15), 3)
        bb = round(random.uniform(0.005, 0.03), 3)
        ie = round(ba * bb, 4)
        pm = round(random.uniform(0.5, 5.0), 3)
        pval = round(random.uniform(0.0001, 0.01), 4)
        csv += f"{p},{ba},{bb},{ie},{pm},{pval}\n"
        top_mediators.append({"protein": p, "beta_a": ba, "beta_b": bb, "indirect_effect": ie, "proportion_mediated": pm, "p_mediation": pval})

    with open(os.path.join(args.output_dir, "mediation_results.csv"), "w") as f:
        f.write(csv)

    with open(os.path.join(args.output_dir, "candidate_proteins.csv"), "w") as f:
        f.write("protein\n" + "\n".join(proteins) + "\n")

    summary = {
        "exposure": args.exposure, "outcome": args.outcome,
        "mediator_source": "deCODE_plasma_proteins",
        "tested_proteins": 4907, "significant_mediators": len(proteins),
        "top_mediators": top_mediators,
    }
    with open(os.path.join(args.output_dir, "mediation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_mediation_mr] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": {
            "exposure": args.exposure, "outcome": args.outcome,
            "mediator_source": "deCODE_plasma_proteins",
            "tested_proteins": 4907, "significant_mediators": len(proteins),
        },
        "output_files": ["mediation_results.csv", "candidate_proteins.csv", "mediation_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Write mock_risk_modeling.py**

```python
#!/usr/bin/env python3
import argparse, json, random, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposure", default="Liver_PDFF")
    parser.add_argument("--outcome", default="Osteoporosis")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    csv = "model,beta,se,p_value\nOLS,0.35,0.08,0.0001\n"
    with open(os.path.join(args.output_dir, "ols_results.csv"), "w") as f:
        f.write(csv)

    with open(os.path.join(args.output_dir, "rcs_results.csv"), "w") as f:
        f.write("knot,estimate,se,p_value\n1,0.30,0.07,0.001\n2,0.40,0.09,0.0005\n")

    summary = {
        "pdff_quartile": "Q4", "osteopenia_aor": round(random.uniform(1.1, 1.2), 2),
        "osteoporosis_aor": round(random.uniform(1.2, 1.3), 2),
        "risk_level": "High", "model_type": "OLS + RCS + Multinomial Logistic",
    }
    with open(os.path.join(args.output_dir, "risk_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_risk_modeling] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["ols_results.csv", "rcs_results.csv", "risk_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Write mock_report.py**

```python
#!/usr/bin/env python3
import argparse, json, time, os, glob

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.3)

    md = f"# AdipoInsight Research Report\n\nProject ID: {args.project_id}\n\nAll analysis steps completed.\n"
    out_path = os.path.join(args.output_dir, "final_report.md")
    with open(out_path, "w") as f:
        f.write(md)

    print(f"[mock_report] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success",
        "summary": {"report_path": out_path, "sections": 8},
        "output_files": ["final_report.md"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Verify all scripts run**

```bash
cd /mnt/e/Adipolnsight && python analysis_scripts/segmentation/mock_segmentation.py --output-dir /tmp/test_seg --task-id test1 && python analysis_scripts/gwas/mock_gwas.py --output-dir /tmp/test_gwas --task-id test2 && python analysis_scripts/opengwas/mock_opengwas_fetch.py --output-dir /tmp/test_og --task-id test3 && python analysis_scripts/mr/mock_mr.py --output-dir /tmp/test_mr --task-id test4 && python analysis_scripts/mediation_mr/mock_mediation_mr.py --output-dir /tmp/test_med --task-id test5 && python analysis_scripts/risk_modeling/mock_risk_modeling.py --output-dir /tmp/test_risk --task-id test6 && python analysis_scripts/report/mock_report.py --project-id 1 --output-dir /tmp/test_report --task-id test7 && echo "ALL 7 SCRIPTS PASSED"
```

- [ ] **Step 9: Commit**

```bash
git add analysis_scripts/ && git commit -m "feat: add all 7 mock analysis CLI scripts with unified JSON I/O"
```

---

### Task 5.2: Mock data files

**Files:**
- Create: `mock_data/phenotype/mock_phenotype.csv`
- Create: `mock_data/covariates/mock_covariates.csv`
- Create: `mock_data/genetics/mock_lead_snps.csv`

- [ ] **Step 1: Create mock data files**

```bash
cat > /mnt/e/Adipolnsight/mock_data/phenotype/mock_phenotype.csv << 'CSV'
subject_id,Liver_PDFF,BMD_T_score,Fat_mass_kg,Height_cm,Weight_kg
DEMO_001,11.42,-1.8,28.5,168.0,72.3
DEMO_002,8.15,-1.2,22.1,172.5,68.9
DEMO_003,14.30,-2.3,34.2,165.0,81.5
CSV

cat > /mnt/e/Adipolnsight/mock_data/covariates/mock_covariates.csv << 'CSV'
subject_id,age,sex,BMI,smoking_status,alcohol_intake,physical_activity
DEMO_001,58,Female,25.6,Never,Low,Moderate
DEMO_002,62,Male,23.1,Former,Moderate,High
DEMO_003,55,Female,29.9,Current,Low,Low
CSV

cat > /mnt/e/Adipolnsight/mock_data/genetics/mock_lead_snps.csv << 'CSV'
SNP,CHR,BP,EA,OA,EAF,BETA,SE,P
rs738409,22,43928847,G,C,0.23,0.08,0.01,3.4e-15
rs58542926,19,19268740,T,C,0.07,0.06,0.012,1.2e-08
rs641738,19,54102061,T,C,0.45,-0.04,0.008,2.1e-07
rs1260326,2,27508073,C,T,0.38,0.05,0.009,5.6e-08
rs780094,2,27519700,T,C,0.42,0.03,0.007,8.9e-06
rs4240624,8,9183358,G,A,0.31,0.06,0.014,3.2e-05
rs73001065,19,45480956,T,C,0.12,-0.08,0.019,7.1e-05
rs10883437,10,113018354,A,G,0.28,0.04,0.011,1.5e-04
CSV
```

- [ ] **Step 2: Commit**

```bash
git add mock_data/ && git commit -m "feat: add mock phenotype, covariates, and genetics datasets"
```

---

## Phase 6: Frontend Foundation

### Task 6.1: Initialize Vite + React project

**Files:**
- Create: `frontend/` via `npm create vite`

- [ ] **Step 1: Scaffold with Vite**

```bash
cd /mnt/e/Adipolnsight && npm create vite@latest frontend -- --template react-ts 2>&1
```

- [ ] **Step 2: Install dependencies**

```bash
cd /mnt/e/Adipolnsight/frontend && npm install && npm install tailwindcss @tailwindcss/vite axios zustand react-router-dom react-markdown recharts
```

- [ ] **Step 3: Configure Tailwind with Vite plugin**

Read `frontend/vite.config.ts`, then replace it with:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
})
```

- [ ] **Step 4: Write `frontend/src/index.css` with Tailwind import**

```css
@import "tailwindcss";
```

- [ ] **Step 5: Verify dev server starts**

```bash
cd /mnt/e/Adipolnsight/frontend && timeout 10 npm run dev 2>&1 || true
```

- [ ] **Step 6: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/ && git commit -m "feat: initialize Vite + React + TypeScript + Tailwind + Zustand + react-router"
```

---

### Task 6.2: TypeScript types and API client

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/services/apiClient.ts`

- [ ] **Step 1: Write types/index.ts**

```typescript
export interface Project {
  id: number;
  name: string;
  research_goal: string;
  exposure: string;
  outcome: string;
  mediator_set: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  research_goal: string;
  exposure: string;
  outcome: string;
  mediator_set: string;
}

export interface AnalysisTask {
  id: number;
  project_id: number;
  task_type: string;
  task_name: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  progress: number;
  input_json: string;
  output_json: string;
  error_code: string;
  error_message: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisResult {
  id: number;
  task_id: number;
  project_id: number;
  result_type: string;
  summary_json: string;
  output_files_json: string;
  created_at: string;
}

export interface Report {
  id: number;
  project_id: number;
  title: string;
  content_markdown: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface FileAsset {
  id: number;
  project_id: number;
  file_name: string;
  file_type: string;
  file_path: string;
  file_size: number;
  created_at: string;
}

export const TASK_TYPE_LABELS: Record<string, string> = {
  image_segmentation: 'AI Image Segmentation',
  gwas_analysis: 'GWAS Analysis',
  opengwas_fetch: 'OpenGWAS Data Fetch',
  mendelian_randomization: 'Mendelian Randomization',
  mediation_mr: 'Mediation MR',
  risk_modeling: 'Risk Modeling',
  report_generation: 'Report Generation',
};

export const PIPELINE_ORDER = [
  'image_segmentation', 'gwas_analysis', 'opengwas_fetch',
  'mendelian_randomization', 'mediation_mr', 'risk_modeling', 'report_generation',
];
```

- [ ] **Step 2: Write services/apiClient.ts**

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed';
    return Promise.reject(new Error(msg));
  },
);

export default api;
```

- [ ] **Step 3: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/src/types/ frontend/src/services/ && git commit -m "feat: add TypeScript types and Axios API client"
```

---

### Task 6.3: Zustand stores

**Files:**
- Create: `frontend/src/stores/projectStore.ts`
- Create: `frontend/src/stores/taskStore.ts`
- Create: `frontend/src/stores/resultStore.ts`

- [ ] **Step 1: Write projectStore.ts**

```typescript
import { create } from 'zustand';
import api from '../services/apiClient';
import type { Project } from '../types';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  fetchProject: (id: number) => Promise<void>;
  createProject: (data: any) => Promise<Project>;
  deleteProject: (id: number) => Promise<void>;
  createDemo: () => Promise<Project>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const res = await api.get('/projects');
      set({ projects: res.data.projects, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  fetchProject: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const res = await api.get(`/projects/${id}`);
      set({ currentProject: res.data, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  createProject: async (data) => {
    const res = await api.post('/projects', data);
    get().fetchProjects();
    return res.data;
  },

  deleteProject: async (id) => {
    await api.delete(`/projects/${id}`);
    get().fetchProjects();
  },

  createDemo: async () => {
    const res = await api.post('/demo/seed');
    get().fetchProjects();
    return res.data;
  },
}));
```

- [ ] **Step 2: Write taskStore.ts**

```typescript
import { create } from 'zustand';
import api from '../services/apiClient';
import type { AnalysisTask } from '../types';

interface TaskState {
  tasks: AnalysisTask[];
  loading: boolean;
  polling: boolean;
  fetchTasks: (projectId: number) => Promise<void>;
  createTask: (projectId: number, taskType: string, params?: any) => Promise<AnalysisTask>;
  rerunTask: (taskId: number) => Promise<void>;
  runFullPipeline: (projectId: number) => Promise<void>;
  startPolling: (projectId: number) => void;
  stopPolling: () => void;
}

export const useTaskStore = create<TaskState>((set, get) => {
  let timer: ReturnType<typeof setInterval> | null = null;

  return {
    tasks: [],
    loading: false,
    polling: false,

    fetchTasks: async (projectId: number) => {
      try {
        const res = await api.get(`/projects/${projectId}/tasks`);
        set({ tasks: res.data.tasks });
      } catch (_) {}
    },

    createTask: async (projectId, taskType, params) => {
      const res = await api.post('/tasks', { project_id: projectId, task_type: taskType, parameters: params || {} });
      get().fetchTasks(projectId);
      return res.data;
    },

    rerunTask: async (taskId) => {
      await api.post(`/tasks/${taskId}/rerun`);
    },

    runFullPipeline: async (projectId) => {
      await api.post(`/projects/${projectId}/pipeline/run-all`);
      get().startPolling(projectId);
    },

    startPolling: (projectId) => {
      if (timer) clearInterval(timer);
      set({ polling: true });
      timer = setInterval(async () => {
        const { tasks } = get();
        const hasRunning = tasks.some((t) => t.status === 'running' || t.status === 'pending');
        await get().fetchTasks(projectId);
        const updated = get().tasks;
        const stillRunning = updated.some((t) => t.status === 'running' || t.status === 'pending');
        if (hasRunning && !stillRunning) {
          get().stopPolling();
        }
      }, 2000);
    },

    stopPolling: () => {
      if (timer) { clearInterval(timer); timer = null; }
      set({ polling: false });
    },
  };
});
```

- [ ] **Step 3: Write resultStore.ts**

```typescript
import { create } from 'zustand';
import api from '../services/apiClient';
import type { AnalysisResult, Report } from '../types';

interface ResultState {
  currentResult: AnalysisResult | null;
  currentReport: Report | null;
  loading: boolean;
  fetchResult: (taskId: number) => Promise<void>;
  fetchReport: (reportId: number) => Promise<void>;
  generateReport: (projectId: number) => Promise<Report>;
}

export const useResultStore = create<ResultState>((set) => ({
  currentResult: null,
  currentReport: null,
  loading: false,

  fetchResult: async (taskId) => {
    set({ loading: true });
    try {
      const res = await api.get(`/tasks/${taskId}/result`);
      set({ currentResult: res.data, loading: false });
    } catch (_) {
      set({ loading: false });
    }
  },

  fetchReport: async (reportId) => {
    set({ loading: true });
    try {
      const res = await api.get(`/reports/${reportId}`);
      set({ currentReport: res.data, loading: false });
    } catch (_) {
      set({ loading: false });
    }
  },

  generateReport: async (projectId) => {
    const res = await api.post(`/projects/${projectId}/reports/generate`);
    set({ currentReport: res.data });
    return res.data;
  },
}));
```

- [ ] **Step 4: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/src/stores/ && git commit -m "feat: add Zustand stores for projects, tasks, and results"
```

---

## Phase 7: Frontend Components & Pages

### Task 7.1: Shared UI components

**Files:**
- Create: `frontend/src/components/shared/StatusBadge.tsx`
- Create: `frontend/src/components/shared/ProgressBar.tsx`
- Create: `frontend/src/components/shared/ErrorAlert.tsx`
- Create: `frontend/src/components/layout/AppLayout.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Write StatusBadge.tsx**

```tsx
const colors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  running: 'bg-blue-100 text-blue-700',
  success: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  cancelled: 'bg-yellow-100 text-yellow-700',
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  );
}
```

- [ ] **Step 2: Write ProgressBar.tsx**

```tsx
export default function ProgressBar({ value }: { value: number }) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}
```

- [ ] **Step 3: Write ErrorAlert.tsx**

```tsx
export default function ErrorAlert({ code, message }: { code: string; message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
      <span className="font-mono font-bold mr-2">[{code}]</span>
      {message}
    </div>
  );
}
```

- [ ] **Step 4: Write AppLayout.tsx and Sidebar.tsx**

```tsx
// AppLayout.tsx
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function AppLayout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}

// Sidebar.tsx
import { Link, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const loc = useLocation();
  const linkCls = (p: string) =>
    `block px-4 py-2 rounded-lg text-sm ${loc.pathname === p ? 'bg-blue-100 text-blue-800 font-medium' : 'text-gray-600 hover:bg-gray-100'}`;

  return (
    <aside className="w-56 bg-white border-r border-gray-200 p-4 flex flex-col">
      <h1 className="text-lg font-bold text-gray-800 mb-6">AdipoInsight</h1>
      <nav className="flex-1 space-y-1">
        <Link to="/" className={linkCls('/')}>Projects</Link>
      </nav>
      <div className="text-xs text-gray-400 pt-4 border-t">v0.1.0 Mock-First</div>
    </aside>
  );
}
```

- [ ] **Step 5: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/src/components/shared/ frontend/src/components/layout/ && git commit -m "feat: add shared UI components (StatusBadge, ProgressBar, ErrorAlert, Layout)"
```

---

### Task 7.2: Project components

**Files:**
- Create: `frontend/src/components/project/ProjectCard.tsx`
- Create: `frontend/src/components/project/ProjectForm.tsx`
- Create: `frontend/src/components/project/ProjectHeader.tsx`

- [ ] **Step 1: Write all project components**

```tsx
// ProjectCard.tsx
import { Link } from 'react-router-dom';
import type { Project } from '../../types';
import StatusBadge from '../shared/StatusBadge';

export default function ProjectCard({ project, onDelete }: { project: Project; onDelete: (id: number) => void }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-gray-800">{project.name}</h3>
        <StatusBadge status={project.status} />
      </div>
      <p className="text-sm text-gray-500 mb-3 line-clamp-2">{project.research_goal}</p>
      <div className="flex gap-2 text-xs text-gray-400 mb-3">
        <span>Exposure: {project.exposure}</span>
        <span>|</span>
        <span>Outcome: {project.outcome}</span>
      </div>
      <div className="flex gap-2">
        <Link to={`/projects/${project.id}`} className="text-sm text-blue-600 hover:underline">
          Open Workspace →
        </Link>
        <button onClick={() => onDelete(project.id)} className="text-sm text-red-400 hover:text-red-600 ml-auto">
          Delete
        </button>
      </div>
    </div>
  );
}

// ProjectForm.tsx
import { useState, type FormEvent } from 'react';
import type { ProjectCreate } from '../../types';

interface Props { onSubmit: (data: ProjectCreate) => Promise<void>; loading: boolean; }

export default function ProjectForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<ProjectCreate>({
    name: '', research_goal: '', exposure: '', outcome: '', mediator_set: '',
  });

  const handle = async (e: FormEvent) => { e.preventDefault(); await onSubmit(form); };

  const field = (label: string, key: keyof ProjectCreate, required = false) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type="text" value={form[key]} required={required}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );

  return (
    <form onSubmit={handle} className="space-y-4 max-w-lg">
      {field('Project Name *', 'name', true)}
      {field('Research Goal', 'research_goal')}
      {field('Exposure (e.g. Liver_PDFF)', 'exposure')}
      {field('Outcome (e.g. Osteoporosis)', 'outcome')}
      {field('Mediator Set', 'mediator_set')}
      <button type="submit" disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
        {loading ? 'Creating...' : 'Create Project'}
      </button>
    </form>
  );
}

// ProjectHeader.tsx
import type { Project } from '../../types';
import StatusBadge from '../shared/StatusBadge';

export default function ProjectHeader({ project }: { project: Project }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{project.name}</h2>
          <p className="text-sm text-gray-500 mt-1">{project.research_goal}</p>
        </div>
        <StatusBadge status={project.status} />
      </div>
      <div className="flex gap-4 mt-3 text-sm text-gray-600">
        <span><strong>Exposure:</strong> {project.exposure}</span>
        <span><strong>Outcome:</strong> {project.outcome}</span>
        {project.mediator_set && <span><strong>Mediator:</strong> {project.mediator_set}</span>}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/src/components/project/ && git commit -m "feat: add project components (Card, Form, Header)"
```

---

### Task 7.3: Task components

**Files:**
- Create: `frontend/src/components/task/WorkflowStepper.tsx`
- Create: `frontend/src/components/task/TaskCard.tsx`
- Create: `frontend/src/components/task/TaskLogViewer.tsx`

- [ ] **Step 1: Write WorkflowStepper.tsx**

```tsx
import { PIPELINE_ORDER, TASK_TYPE_LABELS } from '../../types';
import type { AnalysisTask } from '../../types';

interface Props { tasks: AnalysisTask[]; currentStep: number; }

export default function WorkflowStepper({ tasks, currentStep }: Props) {
  const statusMap: Record<string, string> = {};
  tasks.forEach((t) => { statusMap[t.task_type] = t.status; });

  return (
    <div className="flex items-center gap-2 mb-6 overflow-x-auto py-2">
      {PIPELINE_ORDER.map((tt, i) => {
        const status = statusMap[tt];
        const colors: Record<string, string> = {
          success: 'bg-green-500', running: 'bg-blue-500 animate-pulse',
          failed: 'bg-red-500', pending: 'bg-gray-300',
        };
        return (
          <div key={tt} className="flex items-center gap-1 shrink-0">
            <div className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded-full ${colors[status || 'pending']}`} />
              <span className={`text-xs ${status === 'running' ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                {i + 1}. {TASK_TYPE_LABELS[tt] || tt}
              </span>
            </div>
            {i < PIPELINE_ORDER.length - 1 && <div className="w-4 h-px bg-gray-300 mx-1" />}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Write TaskCard.tsx**

```tsx
import type { AnalysisTask } from '../../types';
import { TASK_TYPE_LABELS } from '../../types';
import StatusBadge from '../shared/StatusBadge';
import ProgressBar from '../shared/ProgressBar';
import ErrorAlert from '../shared/ErrorAlert';

interface Props {
  task: AnalysisTask;
  onRun: (taskType: string) => void;
  onViewResult: (taskId: number) => void;
  onRerun: (taskId: number) => void;
}

export default function TaskCard({ task, onRun, onViewResult, onRerun }: Props) {
  const hasResult = task.status === 'success';
  const isRunning = task.status === 'running' || task.status === 'pending';
  const isFailed = task.status === 'failed';
  const notStarted = !task.status || task.status === 'pending' || !task.id;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-medium text-sm text-gray-800">{task.task_name || TASK_TYPE_LABELS[task.task_type]}</h4>
        {task.id ? <StatusBadge status={task.status} /> : <StatusBadge status="pending" />}
      </div>
      {isRunning && <ProgressBar value={task.progress} />}
      {isFailed && <ErrorAlert code={task.error_code} message={task.error_message} />}
      <div className="flex gap-2 mt-3">
        {!task.id || notStarted ? (
          <button onClick={() => onRun(task.task_type)}
            className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700">
            Run
          </button>
        ) : null}
        {hasResult && (
          <button onClick={() => onViewResult(task.id)}
            className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">
            View Result
          </button>
        )}
        {isFailed && (
          <button onClick={() => onRerun(task.id)}
            className="bg-orange-500 text-white px-3 py-1 rounded text-xs hover:bg-orange-600">
            Rerun
          </button>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write TaskLogViewer.tsx**

```tsx
import type { AnalysisTask } from '../../types';

export default function TaskLogViewer({ task }: { task: AnalysisTask }) {
  return (
    <div className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs font-mono space-y-1 overflow-auto max-h-64">
      <div><span className="text-gray-500">[task_id]</span> {task.id}</div>
      <div><span className="text-gray-500">[status]</span> {task.status}</div>
      <div><span className="text-gray-500">[progress]</span> {task.progress}%</div>
      <div><span className="text-gray-500">[started]</span> {task.started_at || 'N/A'}</div>
      <div><span className="text-gray-500">[finished]</span> {task.finished_at || 'N/A'}</div>
      {task.error_code && <div className="text-red-400"><span className="text-gray-500">[error]</span> [{task.error_code}] {task.error_message}</div>}
      <div className="text-gray-500 mt-2">--- stdout preview ---</div>
      <div>{task.output_json || '(empty)'}</div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/src/components/task/ && git commit -m "feat: add task components (WorkflowStepper, TaskCard, TaskLogViewer)"
```

---

### Task 7.4: UnifiedResultView & ReportViewer

**Files:**
- Create: `frontend/src/components/result/UnifiedResultView.tsx`
- Create: `frontend/src/components/report/ReportViewer.tsx`

- [ ] **Step 1: Write UnifiedResultView.tsx**

```tsx
import { type AnalysisResult } from '../../types';

function SummaryCards({ summary }: { summary: Record<string, any> }) {
  if (!summary || Object.keys(summary).length === 0) {
    return <p className="text-sm text-gray-400">No summary data available.</p>;
  }
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      {Object.entries(summary).map(([k, v]) => {
        const displayVal = typeof v === 'object' ? JSON.stringify(v).slice(0, 60) : String(v);
        return (
          <div key={k} className="bg-blue-50 rounded-lg p-3 border border-blue-100">
            <div className="text-xs text-blue-500 mb-1">{k}</div>
            <div className="text-sm font-semibold text-gray-800 truncate">{displayVal}</div>
          </div>
        );
      })}
    </div>
  );
}

function DataTable({ files }: { files: string[] }) {
  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium text-gray-700 mb-2">Output Files</h4>
      <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        {files.map((f, i) => (
          <div key={i} className="px-3 py-2 text-xs text-gray-600 border-b last:border-0 font-mono">
            {f}
          </div>
        ))}
        {files.length === 0 && <div className="px-3 py-4 text-xs text-gray-400 text-center">No output files</div>}
      </div>
    </div>
  );
}

export default function UnifiedResultView({ result }: { result: AnalysisResult }) {
  let summary: Record<string, any> = {};
  let files: string[] = [];

  try { summary = JSON.parse(result.summary_json); } catch (_) {}
  try { files = JSON.parse(result.output_files_json); } catch (_) {}

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-800 mb-4">Analysis Result — {result.result_type}</h3>
      <SummaryCards summary={summary} />
      <DataTable files={files} />
    </div>
  );
}
```

- [ ] **Step 2: Write ReportViewer.tsx**

```tsx
import ReactMarkdown from 'react-markdown';

export default function ReportViewer({ content }: { content: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 prose prose-sm max-w-none">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/src/components/result/ frontend/src/components/report/ && git commit -m "feat: add UnifiedResultView + ReportViewer components"
```

---

### Task 7.5: Pages

**Files:**
- Create: `frontend/src/pages/ProjectListPage.tsx`
- Create: `frontend/src/pages/ProjectCreatePage.tsx`
- Create: `frontend/src/pages/ProjectWorkspacePage.tsx`
- Create: `frontend/src/pages/ReportPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write ProjectListPage.tsx**

```tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import ProjectCard from '../components/project/ProjectCard';

export default function ProjectListPage() {
  const { projects, loading, fetchProjects, deleteProject, createDemo } = useProjectStore();
  const nav = useNavigate();

  useEffect(() => { fetchProjects(); }, []);

  const handleDemo = async () => {
    const p = await createDemo();
    nav(`/projects/${p.id}`);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Projects</h2>
        <div className="flex gap-2">
          <button onClick={handleDemo}
            className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700">
            One-Click Demo
          </button>
          <button onClick={() => nav('/projects/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
            New Project
          </button>
        </div>
      </div>
      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg mb-2">No projects yet</p>
          <p>Click "One-Click Demo" or "New Project" to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onDelete={deleteProject} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write ProjectCreatePage.tsx**

```tsx
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import ProjectForm from '../components/project/ProjectForm';
import type { ProjectCreate } from '../types';

export default function ProjectCreatePage() {
  const { createProject, loading } = useProjectStore();
  const nav = useNavigate();

  const handle = async (data: ProjectCreate) => {
    const p = await createProject(data);
    nav(`/projects/${p.id}`);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">New Project</h2>
      <ProjectForm onSubmit={handle} loading={loading} />
    </div>
  );
}
```

- [ ] **Step 3: Write ProjectWorkspacePage.tsx**

```tsx
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import { useTaskStore } from '../stores/taskStore';
import { useResultStore } from '../stores/resultStore';
import ProjectHeader from '../components/project/ProjectHeader';
import WorkflowStepper from '../components/task/WorkflowStepper';
import TaskCard from '../components/task/TaskCard';
import TaskLogViewer from '../components/task/TaskLogViewer';
import UnifiedResultView from '../components/result/UnifiedResultView';
import { PIPELINE_ORDER } from '../types';

export default function ProjectWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const nav = useNavigate();
  const { currentProject, fetchProject } = useProjectStore();
  const { tasks, fetchTasks, createTask, rerunTask, runFullPipeline, startPolling, stopPolling } = useTaskStore();
  const { currentResult, fetchResult, generateReport, currentReport } = useResultStore();

  const [viewingTaskId, setViewingTaskId] = useState<number | null>(null);
  const [showLog, setShowLog] = useState<number | null>(null);

  useEffect(() => {
    fetchProject(pid);
    fetchTasks(pid);
    return () => stopPolling();
  }, [pid]);

  useEffect(() => {
    startPolling(pid);
  }, []);

  if (!currentProject) return <p className="text-gray-400">Loading project...</p>;

  const taskMap: Record<string, any> = {};
  tasks.forEach((t) => { taskMap[t.task_type] = t; });

  const handleRun = async (taskType: string) => {
    await createTask(pid, taskType);
    startPolling(pid);
  };

  const handleViewResult = async (taskId: number) => {
    setViewingTaskId(taskId);
    await fetchResult(taskId);
  };

  const handleRunAll = async () => {
    await runFullPipeline(pid);
  };

  const handleGenerateReport = async () => {
    const report = await generateReport(pid);
    nav(`/projects/${pid}/report`, { state: { report } });
  };

  const hasAnySuccess = tasks.some((t) => t.status === 'success');

  return (
    <div>
      <ProjectHeader project={currentProject} />

      <div className="flex gap-2 mb-4">
        <button onClick={handleRunAll}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">
          Run Full Pipeline
        </button>
        {hasAnySuccess && (
          <button onClick={handleGenerateReport}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700">
            Generate Report
          </button>
        )}
      </div>

      <WorkflowStepper tasks={tasks} currentStep={0} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {PIPELINE_ORDER.map((tt) => (
          <TaskCard
            key={tt}
            task={taskMap[tt] || { task_type: tt, task_name: '', status: '', progress: 0, error_code: '', error_message: '', id: 0, project_id: pid, input_json: '', output_json: '', created_at: '', updated_at: '', started_at: null, finished_at: null }}
            onRun={handleRun}
            onViewResult={handleViewResult}
            onRerun={rerunTask}
          />
        ))}
      </div>

      {viewingTaskId && currentResult && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold text-gray-800">Result Detail</h3>
            <button onClick={() => { setViewingTaskId(null); setShowLog(null); }}
              className="text-xs text-gray-400 hover:text-gray-600">Close</button>
          </div>
          <UnifiedResultView result={currentResult} />
          <button onClick={() => setShowLog(viewingTaskId)}
            className="text-sm text-blue-500 mt-2 hover:underline">View Logs</button>
        </div>
      )}

      {showLog && (
        <div className="mb-6">
          <TaskLogViewer task={tasks.find((t) => t.id === showLog)!} />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Write ReportPage.tsx**

```tsx
import { useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useResultStore } from '../stores/resultStore';
import ReportViewer from '../components/report/ReportViewer';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const { currentReport, fetchReport } = useResultStore();
  const loc = useLocation();

  useEffect(() => {
    if (loc.state?.report?.id) {
      fetchReport(loc.state.report.id);
    }
  }, []);

  if (!currentReport?.content_markdown) {
    return <p className="text-gray-400">Report is being generated or not available...</p>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-4">{currentReport.title}</h2>
      <ReportViewer content={currentReport.content_markdown} />
    </div>
  );
}
```

- [ ] **Step 5: Write App.tsx with router**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import ProjectListPage from './pages/ProjectListPage';
import ProjectCreatePage from './pages/ProjectCreatePage';
import ProjectWorkspacePage from './pages/ProjectWorkspacePage';
import ReportPage from './pages/ReportPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<ProjectListPage />} />
          <Route path="/projects/new" element={<ProjectCreatePage />} />
          <Route path="/projects/:id" element={<ProjectWorkspacePage />} />
          <Route path="/projects/:id/report" element={<ReportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 6: Verify main.tsx**

Read `frontend/src/main.tsx` and replace if needed:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 7: Verify full frontend builds**

```bash
cd /mnt/e/Adipolnsight/frontend && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 8: Commit**

```bash
cd /mnt/e/Adipolnsight && git add frontend/src/pages/ frontend/src/App.tsx frontend/src/main.tsx && git commit -m "feat: add all pages with routing, workspace, and demo flow"
```

---

## Phase 8: Documentation & Final Integration

### Task 8.1: Write documentation

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/api.md`
- Create: `docs/mock_skills.md`
- Create: `docs/real_module_replacement.md`

- [ ] **Step 1: Write architecture.md**

```markdown
# AdipoInsight Architecture

## Overview

AdipoInsight is a medical research AI platform built with a Mock-First strategy.
The system consists of three layers:

1. **Frontend** (Vite + React + TypeScript + Tailwind + Zustand)
2. **Backend API** (FastAPI + SQLAlchemy + SQLite)
3. **Analysis Scripts** (Python CLI scripts called via subprocess)

## Data Flow

```
Browser → React App → REST API (/api/v1/*)
  → FastAPI → TaskOrchestrator → SkillRunner
    → subprocess → mock_*.py → stdout JSON
      → SkillRunner saves results → SQLite + storage/
```

## Directory Layout

See project README for full tree.

## Key Design Decisions

- SQLite for zero-config local deployment
- BackgroundTasks for in-process task execution (no Redis needed)
- UnifiedResultView adapts UI based on result_type
- All mock scripts share the same CLI contract (--output-dir, --task-id, stdout JSON)
```

- [ ] **Step 2: Write api.md**

```markdown
# AdipoInsight API Reference

Base URL: `http://localhost:8000/api/v1`

## Projects

| Method | Path | Description |
|--------|------|-------------|
| POST | /projects | Create project |
| GET | /projects | List projects |
| GET | /projects/{id} | Get project |
| DELETE | /projects/{id} | Delete project |

## Files

| Method | Path | Description |
|--------|------|-------------|
| POST | /projects/{id}/files | Upload file |
| GET | /projects/{id}/files | List files |
| GET | /files/{id}/download | Download file |

## Tasks

| Method | Path | Description |
|--------|------|-------------|
| POST | /tasks | Create and run task |
| GET | /tasks/{id} | Get task status |
| GET | /projects/{id}/tasks | List project tasks |
| POST | /tasks/{id}/rerun | Rerun task |
| POST | /projects/{id}/pipeline/run-all | Run full pipeline |

## Results

| Method | Path | Description |
|--------|------|-------------|
| GET | /tasks/{id}/result | Get task result |
| GET | /projects/{id}/results | List project results |

## Reports

| Method | Path | Description |
|--------|------|-------------|
| POST | /projects/{id}/reports/generate | Generate report |
| GET | /reports/{id} | Get report |

## Demo

| Method | Path | Description |
|--------|------|-------------|
| POST | /demo/seed | Create demo project |

## Task Types

`image_segmentation` | `gwas_analysis` | `opengwas_fetch` | `mendelian_randomization` | `mediation_mr` | `risk_modeling` | `report_generation`

## Error Codes

`SCRIPT_NOT_FOUND` | `SCRIPT_EXECUTION_FAILED` | `OUTPUT_JSON_INVALID` | `OUTPUT_FILE_MISSING` | `TASK_TIMEOUT` | `FILE_NOT_FOUND` | `DATABASE_ERROR`
```

- [ ] **Step 3: Write mock_skills.md**

```markdown
# Mock Skills Reference

Each mock script is a standalone Python CLI:

```bash
python mock_xxx.py --output-dir <path> --task-id <id> [--other-args]
```

## Output Protocol

- stdout: log lines followed by one JSON line at the end
- exit code: 0 = success
- all data files go to --output-dir

## Scripts

| Script | Key Output |
|--------|-----------|
| mock_segmentation.py | segmentation_metrics.json, fat_quantification.csv |
| mock_gwas.py | gwas_summary_stats.tsv, lead_snps.csv, gwas_summary.json |
| mock_opengwas_fetch.py | outcome_summary_stats.tsv, opengwas_metadata.json |
| mock_mr.py | mr_results.csv, mr_summary.json |
| mock_mediation_mr.py | mediation_results.csv, mediation_summary.json |
| mock_risk_modeling.py | ols_results.csv, risk_summary.json |
| mock_report.py | final_report.md |
```

- [ ] **Step 4: Write real_module_replacement.md**

```markdown
# Real Module Replacement Guide

Each mock script defines a contract boundary through its CLI interface and output JSON schema.
To replace a mock with a real module:

1. Write the real script with the same CLI arguments
2. Keep the stdout JSON format identical
3. Update the SkillRunner's `script_path` in `backend/app/tasks/`

## Replacement Map

| Module | Mock | Real Replacement |
|--------|------|-----------------|
| Segmentation | mock_segmentation.py | TSSA-UNet inference script |
| GWAS | mock_gwas.py | REGENIE pipeline |
| OpenGWAS | mock_opengwas_fetch.py | IEU OpenGWAS API client |
| MR | mock_mr.py | TwoSampleMR R script |
| Mediation MR | mock_mediation_mr.py | pQTL + TwoStepMR |
| Risk Modeling | mock_risk_modeling.py | Clinical risk model |

The contract remains: accept input JSON, produce output JSON on stdout, write files to output dir.
```

- [ ] **Step 5: Commit**

```bash
cd /mnt/e/Adipolnsight && git add docs/ && git commit -m "docs: add architecture, API, mock skills, and real module replacement docs"
```

---

### Task 8.2: End-to-end smoke test & verification

- [ ] **Step 1: Start backend and verify health**

```bash
cd /mnt/e/Adipolnsight && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl -s http://localhost:8000/api/v1/health | python -m json.tool
```

Expected: `{"status": "ok", "version": "0.1.0"}`

- [ ] **Step 2: Seed demo project via API**

```bash
curl -s -X POST http://localhost:8000/api/v1/demo/seed | python -m json.tool
```

Expected: Project object with `name: "Demo - Liver PDFF and Osteoporosis"`

- [ ] **Step 3: Create a segmentation task**

```bash
curl -s -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "task_type": "image_segmentation"}' | python -m json.tool
```

- [ ] **Step 4: Wait and check task status**

```bash
sleep 3
curl -s http://localhost:8000/api/v1/tasks/1 | python -m json.tool
```

Expected: `status: "success"`, `progress: 100`

- [ ] **Step 5: Run full pipeline**

```bash
curl -s -X POST http://localhost:8000/api/v1/projects/1/pipeline/run-all | python -m json.tool
```

- [ ] **Step 6: Check all tasks completed**

```bash
sleep 15
curl -s http://localhost:8000/api/v1/projects/1/tasks | python -c "import sys,json; d=json.load(sys.stdin); [print(t['task_type'], t['status']) for t in d['tasks']]"
```

Expected: all 7 tasks show `success`

- [ ] **Step 7: Verify output files exist**

```bash
find storage/projects/1/outputs -type f | sort
```

- [ ] **Step 8: Generate and check report**

```bash
curl -s -X POST http://localhost:8000/api/v1/projects/1/reports/generate | python -m json.tool
sleep 2
curl -s http://localhost:8000/api/v1/reports/1 | python -c "import sys,json; d=json.load(sys.stdin); print(d['content_markdown'][:200])"
```

- [ ] **Step 9: Kill backend**

```bash
kill %1 2>/dev/null || true
```

- [ ] **Step 10: Verify frontend builds**

```bash
cd /mnt/e/Adipolnsight/frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 11: Commit any final fixes**

```bash
cd /mnt/e/Adipolnsight && git add -A && git status
```

---

### Task 8.3: Install dependencies and run full verification

- [ ] **Step 1: Install backend Python dependencies**

```bash
cd /mnt/e/Adipolnsight/backend && pip install -r requirements.txt
```

- [ ] **Step 2: Install frontend npm dependencies**

```bash
cd /mnt/e/Adipolnsight/frontend && npm install
```

- [ ] **Step 3: Run all verification commands from Task 8.2**

- [ ] **Step 4: Final commit**

```bash
git add -A && git commit -m "chore: final verification fixes and cleanup"
```

---

## Implementation Order

Execute tasks in this order. Each task builds on the previous one.

1. Task 1.1 - Git + project root
2. Task 1.2 - Backend scaffolding
3. Task 2.1 - SQLAlchemy models
4. Task 2.2 - Pydantic schemas
5. Task 3.1 - Projects API
6. Task 3.2 - Files API + StorageService
7. Task 3.3 - Tasks API + Orchestrator
8. Task 3.4 - Results, Reports, Demo APIs
9. Task 4.1 - BaseSkillRunner + 7 runners
10. Task 4.2 - ReportService
11. Task 5.1 - All 7 mock scripts
12. Task 5.2 - Mock data files
13. Task 6.1 - Frontend scaffolding
14. Task 6.2 - Types + API client
15. Task 6.3 - Zustand stores
16. Task 7.1 - Shared UI components
17. Task 7.2 - Project components
18. Task 7.3 - Task components
19. Task 7.4 - Result + Report components
20. Task 7.5 - All pages + routing
21. Task 8.1 - Documentation
22. Task 8.2 - E2E smoke test
23. Task 8.3 - Final verification
