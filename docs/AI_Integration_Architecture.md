# AdipoInsight AI 能力接入分层架构

> 版本：v0.2.0-draft
> 日期：2026-05-17
> 原则：分层解耦、适配器模式、Mock-First 可替换、前端不嵌入 AI 逻辑

---

## 一、七层架构总览

```
┌─────────────────────────────────────────────────────────────┐
│  1. Frontend Layer          React + Zustand + Axios         │
│     ┌─────────────────────────────────────────────────┐    │
│     │ Pages → Components → Stores → apiClient         │    │
│     └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  2. BFF / API Layer         FastAPI Routers                 │
│     ┌─────────────────────────────────────────────────┐    │
│     │ Request → Validate → Auth(check) → Task.create   │    │
│     └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  3. AI Orchestrator Layer   TaskOrchestrator + dispatch     │
│     ┌─────────────────────────────────────────────────┐    │
│     │ resolve(task_type) → AdapterRegistry.get()       │    │
│     └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  4. AI Skill Adapter Layer  7 Adapters (Mock ↔ Real)       │
│     ┌─────────────────────────────────────────────────┐    │
│     │ ISkillAdapter.execute() → subprocess / HTTP / SDK│    │
│     └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  5. Job / Task Layer        Lifecycle + State Machine       │
│     ┌─────────────────────────────────────────────────┐    │
│     │ pending → running → success / failed / cancelled │    │
│     └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  6. Storage Layer           文件 / 结果 / 报告持久化       │
│     ┌─────────────────────────────────────────────────┐    │
│     │ storage/projects/{id}/raw / outputs / reports    │    │
│     └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  7. Infrastructure          SQLite + BackgroundTasks        │
│     ┌─────────────────────────────────────────────────┐    │
│     │ Database / FileSystem / ProcessManager           │    │
│     └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、推荐目录结构

```
AdipoInsight/
│
├── frontend/                          # 前端（已有，不重构）
│   └── src/
│       ├── components/analysis/       # 分析模块组件（改数据源为 store）
│       ├── components/result/         # 结果展示组件
│       ├── components/task/           # 任务组件
│       ├── pages/                     # 页面
│       ├── services/apiClient.ts      # HTTP 封装（已有）
│       ├── stores/                    # Zustand stores（已有）
│       └── types/index.ts            # TS 类型（已有）
│
├── backend/                           # 后端
│   └── app/
│       ├── api/                       # BFF/API 层（已有）
│       │   ├── projects.py
│       │   ├── files.py
│       │   ├── tasks.py
│       │   ├── results.py
│       │   ├── reports.py
│       │   └── demo.py
│       │
│       ├── orchestrator/              # ★ AI Orchestrator 层（重构自 services/）
│       │   ├── __init__.py
│       │   ├── task_orchestrator.py   # 任务创建 + 状态管理
│       │   └── adapter_registry.py   # Adapter 注册与路由
│       │
│       ├── adapters/                  # ★ AI Skill Adapter 层（新增）
│       │   ├── __init__.py
│       │   ├── base.py               # ISkillAdapter ABC + MockAdapterMixin
│       │   ├── registry.py           # @register_adapter 装饰器
│       │   │
│       │   ├── image_segmentation/   # 影像分割适配器
│       │   │   ├── __init__.py
│       │   │   ├── mock.py           # MockAdapter
│       │   │   ├── real.py           # RealAdapter（预留）
│       │   │   └── schemas.py        # 输入/输出 JSON Schema
│       │   │
│       │   ├── phenotype_quantification/
│       │   │   ├── __init__.py
│       │   │   ├── mock.py
│       │   │   ├── real.py
│       │   │   └── schemas.py
│       │   │
│       │   ├── gwas_analysis/
│       │   │   ├── __init__.py
│       │   │   ├── mock.py
│       │   │   ├── real.py
│       │   │   └── schemas.py
│       │   │
│       │   ├── two_sample_mr/
│       │   │   ├── __init__.py
│       │   │   ├── mock.py
│       │   │   ├── real.py
│       │   │   └── schemas.py
│       │   │
│       │   ├── mediation_mr/
│       │   │   ├── __init__.py
│       │   │   ├── mock.py
│       │   │   ├── real.py
│       │   │   └── schemas.py
│       │   │
│       │   ├── risk_modeling/
│       │   │   ├── __init__.py
│       │   │   ├── mock.py
│       │   │   ├── real.py
│       │   │   └── schemas.py
│       │   │
│       │   └── report_generation/
│       │       ├── __init__.py
│       │       ├── mock.py
│       │       ├── real.py
│       │       └── schemas.py
│       │
│       ├── models/                   # 数据模型（已有）
│       ├── schemas/                  # Pydantic schemas（已有）
│       ├── services/                 # 业务服务（保留 storage/audit/report  service）
│       │   ├── storage_service.py
│       │   ├── report_service.py
│       │   └── audit_service.py
│       │
│       ├── config.py                # 配置（已有，需加 ADAPTER_MODE）
│       ├── database.py              # 数据库（已有）
│       └── main.py                  # 入口（已有）
│
├── analysis_scripts/                 # 外部 AI 脚本（已有，供 RealAdapter 调用）
│   ├── segmentation/
│   ├── gwas/
│   ├── mr/
│   ├── mediation_mr/
│   ├── risk_modeling/
│   ├── opengwas/
│   └── report/
│
├── storage/                          # 文件存储（已有）
│   └── projects/{project_id}/
│       ├── raw/                      # 上传原始文件
│       │   ├── mri/
│       │   ├── phenotype/
│       │   ├── covariates/
│       │   └── genotype/
│       ├── outputs/                  # 分析产出
│       │   ├── segmentation/
│       │   ├── gwas/
│       │   ├── opengwas/
│       │   ├── mr/
│       │   ├── mediation_mr/
│       │   ├── risk_modeling/
│       │   └── report/
│       └── report.md                # 最终报告
│
└── docs/                             # 文档
    ├── architecture.md
    ├── api.md
    ├── mock_skills.md
    ├── real_module_replacement.md
    └── AI_Integration_Architecture.md  # 本文件
```

---

## 三、数据流图（文字版）

### 3.1 完整数据流

```
User Action (Click "Run Analysis")
    │
    ▼
[1. Frontend Layer]
    ProjectWorkspacePage.tsx
    │  handleRun(taskType) 或 handleRunAll()
    │
    ▼
    taskStore.createTask(projectId, taskType, params)
    │  POST /api/v1/tasks  { project_id, task_type, parameters }
    │
    ▼
[2. BFF / API Layer]
    tasks.py :: create_task()
    │  1. 参数校验 (Pydantic TaskCreate schema)
    │  2. 鉴权预留 (Depends(get_current_user) — 当前为空)
    │  3. 审计日志
    │  4. BackgroundTasks.add_task(run_skill_task, task.id)
    │  5. 返回 TaskResponse (status=pending, progress=0)
    │
    ▼
[3. AI Orchestrator Layer]
    task_orchestrator.py :: run_skill_task(task_id)
    │  1. 获取独立 DB session
    │  2. orchestrator.mark_running(task_id)
    │  3. dispatch_skill(task, db)
    │     │
    │     ▼
    │  adapter_registry.py :: dispatch_skill()
    │     adapter = AdapterRegistry.get(task.task_type)
    │     if not adapter → mark_failed("ADAPTER_NOT_FOUND")
    │     adapter.execute(task, orchestrator, db)
    │
    ▼
[4. AI Skill Adapter Layer]
    adapters/<skill>/mock.py :: MockAdapter.execute()
    │  1. 从 task.input_json 解析参数
    │  2. 构建 CLI 命令 (或 HTTP / SDK 调用)
    │  3. orchestrator.update_progress(task.id, 30)
    │  4. subprocess.run(...) 或 HTTP post 或 SDK invoke
    │  5. orchestrator.update_progress(task.id, 70)
    │  6. 解析 stdout / response body
    │  7. orchestrator.mark_success(task.id, output)
    │     │
    │     ├─ 成功 → [5] status=success
    │     └─ 失败 → [5] status=failed + error_code
    │
    ▼
[5. Job / Task Layer]
    task_orchestrator.py :: mark_success()
    │  1. 更新 analysis_tasks 表：status=success, progress=100, finished_at=now
    │  2. 写入 analysis_results 表：summary_json + output_files_json
    │  3. 输出文件写入 storage/projects/{id}/outputs/{task_type}/
    │
    ▼
[6. Storage Layer]
    storage/projects/{id}/outputs/{task_type}/
    ├── segmentation_metrics.json
    ├── gwas_summary_stats.tsv
    ├── mr_results.csv
    ├── mediation_results.csv
    ├── risk_summary.json
    └── final_report.md
    │
    ▼
[Back to Frontend]
    taskStore.startPolling(projectId)  ← 每 2s 轮询 GET /projects/{id}/tasks
    │  检测到 all tasks done → stopPolling()
    │
    ▼
    用户点击 "查看结果" → resultStore.fetchResult(taskId)
    │  GET /tasks/{taskId}/result
    │
    ▼
    UnifiedResultView ← 渲染 summary_json + output_files_json
```

### 3.2 前端数据流（组件 → Store → API）

```
Component                 Store                 API
─────────                 ─────                 ───
ProjectWorkspacePage  →  taskStore          →  POST /tasks
                        resultStore         →  GET /tasks/{id}/result
                        projectStore        →  GET /projects/{id}

ImageProcessingModule
  ├─ 上传文件           →  (待对接)           →  POST /projects/{id}/files
  ├─ 脂肪表型指标       ←  resultStore        ←  GET /tasks/{id}/result
  └─ 分析进度           ←  taskStore          ←  GET /projects/{id}/tasks

GWASModule
  ├─ 曼哈顿图数据       ←  resultStore        ←  GET /tasks/{id}/result
  └─ SNP 统计数据       ←  resultStore

MRModule
  ├─ 散点图数据         ←  resultStore
  └─ MR 估计值表        ←  resultStore

MediationMRModule
  ├─ 机制流程数据       ←  resultStore
  └─ 中介 MR 结果表     ←  resultStore
```

---

## 四、接口命名规范

### 4.1 REST API（已有，保持不变）

```
Method  Path                                  Description
──────  ────                                  ───────────
POST    /api/v1/projects                      创建项目
GET     /api/v1/projects                      项目列表
GET     /api/v1/projects/{id}                 项目详情
DELETE  /api/v1/projects/{id}                 删除项目

POST    /api/v1/projects/{id}/files           上传文件
GET     /api/v1/projects/{id}/files           文件列表
GET     /api/v1/files/{id}/download           下载文件

POST    /api/v1/tasks                         创建并执行任务
GET     /api/v1/tasks/{id}                    任务状态
GET     /api/v1/projects/{id}/tasks           项目任务列表
POST    /api/v1/tasks/{id}/rerun              重跑任务
POST    /api/v1/projects/{id}/pipeline/run-all  全流程执行

GET     /api/v1/tasks/{id}/result             任务结果
GET     /api/v1/projects/{id}/results         项目结果列表

POST    /api/v1/projects/{id}/reports/generate 生成报告
GET     /api/v1/reports/{id}                  查看报告

POST    /api/v1/demo/seed                     创建 Demo 项目
GET     /api/v1/health                        健康检查
```

### 4.2 Task Type 枚举（已有）

```python
# backend/app/schemas/task.py
TASK_TYPES = [
    "image_segmentation",       # AI 影像分割
    "phenotype_quantification", # ★ 新增：脂肪表型定量（从 segmentation 中独立）
    "gwas_analysis",            # GWAS 分析
    "opengwas_fetch",           # OpenGWAS 数据获取
    "mendelian_randomization",  # 两样本孟德尔随机化
    "mediation_mr",             # 中介 MR 分析
    "risk_modeling",            # 风险建模
    "report_generation",        # 报告生成
]
```

### 4.3 Adapter 命名规范

```
目录命名：     adapters/{snake_case_skill_name}/
类命名：       {PascalCaseSkillName}Adapter
Mock 实现：    MockAdapter (每个 skill 包内的 mock.py)
Real 实现：    RealAdapter (每个 skill 包内的 real.py)
Schema 文件：  schemas.py  →  InputSchema / OutputSchema
```

示例：
```python
# adapters/image_segmentation/mock.py
class MockAdapter(ISkillAdapter):
    task_type = "image_segmentation"

# adapters/image_segmentation/real.py
class RealAdapter(ISkillAdapter):
    task_type = "image_segmentation"

# adapters/image_segmentation/schemas.py
class SegmentationInput(BaseModel): ...
class SegmentationOutput(BaseModel): ...
```

### 4.4 Python 模块命名

```
backend/app/orchestrator/   # 编排层
backend/app/adapters/       # 适配器层
backend/app/models/         # 数据模型（不变）
backend/app/schemas/        # Pydantic schemas（不变）
backend/app/services/       # 通用业务服务（不变）
backend/app/api/            # API 路由（不变）
```

---

## 五、各层详细设计

### 5.1 Frontend Layer（前端层）

**职责**：用户交互、状态展示、触发任务、展示结果

**关键文件**：
| 文件 | 职责 |
|------|------|
| `pages/ProjectWorkspacePage.tsx` | 工作区主控：触发任务、聚合状态、协调子模块 |
| `components/analysis/*.tsx` | 4 个分析模块：上传 + 触发 + 结果渲染 |
| `components/result/UnifiedResultView.tsx` | 通用结果展示（summary cards + file list） |
| `components/task/*.tsx` | 任务卡片、步骤指示器、日志查看器 |
| `stores/taskStore.ts` | 任务状态管理 + 轮询 |
| `stores/resultStore.ts` | 结果数据管理 |
| `stores/projectStore.ts` | 项目数据管理 |
| `services/apiClient.ts` | 统一 HTTP 客户端 |
| `types/index.ts` | TypeScript 类型定义 |

**数据流向规则**：
- 组件 **不直接** 包含 AI 计算逻辑
- 组件从 **Zustand Store** 获取状态和数据
- Store 通过 **apiClient** 调用后端
- 后端返回的 `summary_json` 由组件解析后渲染

**待改造**（不在此文档执行）：
- `ImageProcessingModule`：移除 `PHENOTYPE_DATA`/`SUMMARY_METRICS` 常量，从 store 取数据
- `GWASModule`：移除 `generateManhattanData()`，从 `result.summary_json` 取数据
- `MRModule`：移除 `generateMRData()`/`MR_ESTIMATES`，从 store 取数据
- `MediationMRModule`：移除 `RESULTS_DATA`，从 store 取数据

---

### 5.2 BFF / API Layer（后端 API 层）

**职责**：接收前端请求、参数校验、鉴权预留、创建任务并返回

**关键文件**：
| 文件 | 职责 |
|------|------|
| `api/projects.py` | 项目 CRUD |
| `api/files.py` | 文件上传/下载 |
| `api/tasks.py` | 任务创建/列表/详情/重跑/全流程 |
| `api/results.py` | 结果查询 |
| `api/reports.py` | 报告生成/查看 |
| `api/demo.py` | Demo 种子数据 |

**鉴权预留**：
```python
# 当前为空实现，预留接口
from fastapi import Depends

async def get_current_user():
    """预留：从 JWT / OAuth2 / Session 中提取用户身份"""
    return {"user_id": "anonymous", "role": "researcher"}
```

**请求 → 任务创建的完整链路**：
```python
# api/tasks.py
@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreate,                          # Pydantic 校验
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # user = Depends(get_current_user),        # 预留
):
    # 1. 编排器创建任务（写 DB，status=pending）
    task = TaskOrchestrator(db).create_task(
        project_id=body.project_id,
        task_type=body.task_type,
        parameters=body.parameters,
    )
    # 2. 审计日志
    log_audit(db, body.project_id, "create_task", ...)
    # 3. 后台异步执行
    background_tasks.add_task(run_skill_task, task.id)
    # 4. 立即返回任务对象（status=pending）
    return task
```

---

### 5.3 AI Orchestrator Layer（AI 编排层）

**职责**：根据 `task_type` 路由到对应的 AI Skill Adapter，管理执行生命周期

**关键文件**：
| 文件 | 职责 |
|------|------|
| `orchestrator/task_orchestrator.py` | 任务创建/状态更新/结果持久化 |
| `orchestrator/adapter_registry.py` | Adapter 注册表 + dispatch |

**AdapterRegistry 设计**：
```python
# orchestrator/adapter_registry.py

from typing import Dict, Optional
from backend.app.adapters.base import ISkillAdapter

class AdapterRegistry:
    _adapters: Dict[str, ISkillAdapter] = {}

    @classmethod
    def register(cls, adapter: ISkillAdapter):
        cls._adapters[adapter.task_type] = adapter

    @classmethod
    def get(cls, task_type: str) -> Optional[ISkillAdapter]:
        return cls._adapters.get(task_type)

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._adapters.keys())


def dispatch_skill(task, db):
    """根据 task_type 分发到对应 adapter"""
    orch = TaskOrchestrator(db)
    adapter = AdapterRegistry.get(task.task_type)
    if not adapter:
        orch.mark_failed(task.id, "ADAPTER_NOT_FOUND",
                         f"No adapter registered for '{task.task_type}'")
        return
    adapter.execute(task, orch, db)
```

**配置驱动的 Adapter 模式切换**：
```python
# config.py（新增配置项）
import os

# "mock" | "real" | "hybrid"（按 task_type 逐个配置）
ADAPTER_MODE = os.getenv("ADAPTER_MODE", "mock")

# hybrid 模式下，指定哪些 skill 使用 real
ADAPTER_REAL_SKILLS = set(
    os.getenv("ADAPTER_REAL_SKILLS", "").split(",")
    if os.getenv("ADAPTER_REAL_SKILLS") else []
)
```

---

### 5.4 AI Skill Adapter Layer（AI 技能适配层）

**职责**：封装每个 AI 能力的调用方式，提供统一的 Mock/Real 双实现

#### 5.4.1 基类接口

```python
# adapters/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class SkillOutput:
    """统一的 AI Skill 输出结构"""
    status: str                    # "success" | "failed"
    summary: Dict[str, Any]        # 展平后写入 summary_json
    output_files: List[str]        # 输出文件名列表
    error_code: str = ""
    error_message: str = ""


class ISkillAdapter(ABC):
    """AI Skill Adapter 抽象接口

    所有 Mock 和 Real 适配器必须实现此接口。
    前端永远不直接调用此接口——只通过 Orchestrator。
    """

    task_type: str                 # 如 "image_segmentation"
    task_name: str                 # 如 "AI Image Segmentation"

    @abstractmethod
    def validate_inputs(self, input_json: Dict[str, Any]) -> bool:
        """校验输入参数是否满足此 skill 的最低要求"""
        ...

    @abstractmethod
    def build_command(self, inputs: Dict[str, Any]) -> Any:
        """构建执行命令/请求。Mock 返回 CLI args；Real 可能返回 HTTP payload"""
        ...

    @abstractmethod
    def execute(
        self, task, orchestrator, db
    ) -> SkillOutput:
        """执行 AI 能力，返回标准化输出

        编排器调用此方法，不关心底层是 subprocess / HTTP / SDK。
        """
        ...
```

#### 5.4.2 7 个 Skill Adapter 规格

| # | task_type | task_name | 输入参数 | 输出 summary 关键字段 | 输出文件 |
|---|-----------|-----------|----------|----------------------|----------|
| 1 | `image_segmentation` | AI Image Segmentation | project_id, file_id (MRI NIfTI) | dice_liver, dice_visceral_fat, dice_subcutaneous_fat, dice_bone_marrow, qc_status | segmentation_metrics.json, fat_quantification.csv, overlay_preview.png |
| 2 | `phenotype_quantification` | Phenotype Quantification | project_id（依赖 segmentation 结果） | liver_pdff, visceral_fat_volume, subcutaneous_fat_volume, bone_marrow_fat_fraction, total_body_fat_pct, muscle_volume, sat_vat_ratio | phenotype_summary.json, phenotype_detail.csv |
| 3 | `gwas_analysis` | GWAS Analysis | project_id, phenotype (str) | phenotype, sample_size, significant_loci_count, lead_snps_count, lambda_gc | gwas_summary_stats.tsv, lead_snps.csv, significant_loci.csv, gwas_summary.json |
| 4 | `two_sample_mr` | Two-Sample Mendelian Randomization | project_id, exposure (str), outcome (str) | exposure, outcome, method, beta, or, ci_lower, ci_upper, p_value, cochran_q_p, egger_intercept_p | mr_results.csv, heterogeneity.csv, pleiotropy.csv, mr_summary.json |
| 5 | `mediation_mr` | Mediation MR | project_id, exposure, outcome, mediator_source (str) | exposure, outcome, mediator_source, tested_proteins, significant_mediators, top_mediators[] | mediation_results.csv, candidate_proteins.csv, mediation_summary.json |
| 6 | `risk_modeling` | Risk Modeling | project_id, exposure, outcome | pdff_quartile, osteopenia_aor, osteoporosis_aor, risk_level, model_type | ols_results.csv, rcs_results.csv, risk_summary.json |
| 7 | `report_generation` | Report Generation | project_id | report_path, sections | final_report.md |

#### 5.4.3 Mock Adapter 示例

```python
# adapters/gwas_analysis/mock.py

from backend.app.adapters.base import ISkillAdapter, SkillOutput
from backend.app.adapters.registry import register_adapter
from backend.app.config import ANALYSIS_SCRIPTS_DIR
import subprocess, json

@register_adapter
class MockGWASAdapter(ISkillAdapter):
    task_type = "gwas_analysis"
    task_name = "GWAS Analysis"

    def validate_inputs(self, input_json: dict) -> bool:
        return "project_id" in input_json

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        phenotype = params.get("phenotype", "Liver_PDFF")
        out_dir = f"storage/projects/{project_id}/outputs/gwas"
        return [
            "python",
            str(ANALYSIS_SCRIPTS_DIR / "gwas/mock_gwas.py"),
            "--phenotype", phenotype,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]

    def execute(self, task, orchestrator, db) -> SkillOutput:
        inputs = json.loads(task.input_json)
        if not self.validate_inputs(inputs):
            orchestrator.mark_failed(task.id, "INVALID_INPUT", "Missing project_id")
            return SkillOutput(status="failed", summary={}, output_files=[],
                               error_code="INVALID_INPUT", error_message="Missing project_id")

        orchestrator.update_progress(task.id, 10)
        cmd = self.build_command(inputs)
        orchestrator.update_progress(task.id, 20)

        # 创建输出目录
        out_dir = f"storage/projects/{task.project_id}/outputs/gwas"
        import os; os.makedirs(out_dir, exist_ok=True)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=out_dir)
        except subprocess.TimeoutExpired:
            orchestrator.mark_failed(task.id, "TASK_TIMEOUT", "Task exceeded 300s limit")
            return SkillOutput(status="failed", summary={}, output_files=[],
                               error_code="TASK_TIMEOUT", error_message="Timeout")
        except FileNotFoundError:
            orchestrator.mark_failed(task.id, "SCRIPT_NOT_FOUND", str(cmd[1]))
            return SkillOutput(status="failed", summary={}, output_files=[],
                               error_code="SCRIPT_NOT_FOUND", error_message=str(cmd[1]))

        orchestrator.update_progress(task.id, 70)
        if result.returncode != 0:
            orchestrator.mark_failed(task.id, "SCRIPT_EXECUTION_FAILED", result.stderr[:500])
            return SkillOutput(status="failed", summary={}, output_files=[],
                               error_code="SCRIPT_EXECUTION_FAILED", error_message=result.stderr[:500])

        try:
            output = json.loads(result.stdout.strip().split("\n")[-1])
        except (json.JSONDecodeError, IndexError):
            orchestrator.mark_failed(task.id, "OUTPUT_JSON_INVALID", "Failed to parse stdout JSON")
            return SkillOutput(status="failed", summary={}, output_files=[],
                               error_code="OUTPUT_JSON_INVALID", error_message="Bad JSON")

        orchestrator.mark_success(task.id, output)
        return SkillOutput(
            status="success",
            summary=output.get("summary", {}),
            output_files=output.get("output_files", []),
        )
```

#### 5.4.4 Real Adapter 接口预留

```python
# adapters/gwas_analysis/real.py

@register_adapter
class RealGWASAdapter(ISkillAdapter):
    task_type = "gwas_analysis"
    task_name = "GWAS Analysis"

    def validate_inputs(self, input_json: dict) -> bool:
        # 真实环境需校验：genotype 文件存在、phenotype 列合法
        return True

    def build_command(self, inputs: dict) -> list[str]:
        # 真实环境：调用 REGENIE / PLINK2 / SAIGE
        return [
            "regenie",
            "--step", "1",
            "--bed", f"storage/projects/{inputs['project_id']}/raw/genotype/data",
            "--phenoFile", f"storage/projects/{inputs['project_id']}/raw/phenotype/pheno.csv",
            "--out", f"storage/projects/{inputs['project_id']}/outputs/gwas/step1",
        ]

    def execute(self, task, orchestrator, db) -> SkillOutput:
        # 同 Mock 模式，但调用真实 CLI / HTTP API / Python SDK
        ...
```

---

### 5.5 Job / Task Layer（任务生命周期层）

**职责**：管理任务的完整生命周期状态机

**状态机**：
```
                    ┌─────────────┐
                    │   pending   │  ← create_task()
                    └──────┬──────┘
                           │ mark_running()
                    ┌──────▼──────┐
                    │   running   │  ← progress: 10 → 30 → 70 → 90
                    └──┬───┬───┬─┘
                       │   │   │
              ┌────────┘   │   └─────────┐
              │            │             │
     ┌────────▼───┐  ┌─────▼──────┐  ┌──▼──────────┐
     │  success   │  │  failed    │  │  cancelled   │
     │ progress=100│  │ error_code │  │ (预留)       │
     └────────────┘  └────────────┘  └─────────────┘
```

**状态转换规则**：
| 当前状态 | 允许转换到 |
|----------|-----------|
| pending | running, cancelled |
| running | success, failed, cancelled |
| success | (终态) |
| failed | running（通过 rerun 创建新 task） |
| cancelled | running（通过 rerun 创建新 task） |

**进度上报约定**：
| 进度值 | 含义 |
|--------|------|
| 0 | pending |
| 10 | 开始执行（mark_running） |
| 20 | 输入校验通过，命令构建完成 |
| 30 | 子进程/外部调用已启动 |
| 50 | 中间产出已生成 |
| 70 | 外部调用完成，开始解析 |
| 90 | 结果解析完成，开始持久化 |
| 100 | 全部完成（mark_success） |

**错误码枚举**（已有 + 新增）：
```
ADAPTER_NOT_FOUND      — 未找到对应 task_type 的 adapter
INVALID_INPUT          — 输入参数不满足最低要求
SCRIPT_NOT_FOUND       — 分析脚本路径不存在
SCRIPT_EXECUTION_FAILED — 脚本执行返回非零退出码
OUTPUT_JSON_INVALID    — stdout JSON 解析失败
OUTPUT_FILE_MISSING    — 预期输出文件不存在
TASK_TIMEOUT           — 超过 300s 时间限制
FILE_NOT_FOUND         — 上传文件不存在
DATABASE_ERROR         — 数据库写入失败
```

---

### 5.6 Storage Layer（存储层）

**职责**：管理上传文件、分析输出、图表、报告的物理存储

**目录结构**：
```
storage/
└── projects/
    └── {project_id}/
        ├── raw/                          # 原始上传文件
        │   ├── mri/                      # MRI 影像 (.nii.gz, .dcm)
        │   │   └── 20260517_143000_mri_T1.nii.gz
        │   ├── phenotype/                # 表型数据 (.csv, .tsv)
        │   │   └── 20260517_143001_phenotype_mock_phenotype.csv
        │   ├── covariates/               # 协变量
        │   │   └── 20260517_143002_covariates_mock_covariates.csv
        │   └── genotype/                 # 基因组数据
        │       └── 20260517_143003_genotype_mock_lead_snps.csv
        │
        ├── outputs/                      # 分析产出（按 task_type 分目录）
        │   ├── segmentation/
        │   │   ├── segmentation_metrics.json
        │   │   ├── fat_quantification.csv
        │   │   ├── overlay_preview.png
        │   │   ├── command.txt
        │   │   └── run.log
        │   ├── gwas/
        │   │   ├── gwas_summary_stats.tsv
        │   │   ├── lead_snps.csv
        │   │   ├── significant_loci.csv
        │   │   ├── gwas_summary.json
        │   │   ├── command.txt
        │   │   └── run.log
        │   ├── opengwas/
        │   ├── mr/
        │   ├── mediation_mr/
        │   ├── risk_modeling/
        │   └── report/
        │
        └── report.md                     # 最终汇总报告
```

**StorageService 接口**（已有，保持）：
```python
class StorageService:
    def ensure_dirs(project_id)            # 创建项目目录结构
    def save_upload(file, project_id, type) -> FileAsset  # 保存上传文件
    def get_project_root(project_id) -> Path
    def get_output_dir(project_id, task_type) -> Path
    def list_project_files(project_id) -> list[FileAsset]
    def get_file_path(file_id) -> Path
```

---

### 5.7 Mock/Real 双适配模式

**核心原则**：同一接口，两种实现，环境变量切换，零代码改动

**切换机制**：
```python
# config.py
ADAPTER_MODE = os.getenv("ADAPTER_MODE", "mock")  # "mock" | "real" | "hybrid"

# adapters/registry.py
def register_adapter(cls):
    """装饰器：根据 ADAPTER_MODE 决定注册 Mock 还是 Real"""
    inst = cls()
    mode = ADAPTER_MODE

    # hybrid 模式：按 skill 粒度切换
    if mode == "hybrid":
        is_real = cls.task_type in ADAPTER_REAL_SKILLS
    else:
        is_real = (mode == "real")

    # 命名约定：MockFooAdapter 和 RealFooAdapter
    # 只注册当前模式对应的实现
    if is_real and "Real" in cls.__name__:
        AdapterRegistry.register(inst)
    elif not is_real and "Mock" in cls.__name__:
        AdapterRegistry.register(inst)

    return cls
```

**跨 skill 依赖处理**：
```
image_segmentation ──→ phenotype_quantification
                                   │
gwas_analysis ←────────────────────┘
       │
       ├──→ opengwas_fetch ──→ two_sample_mr ──→ risk_modeling
       │                              │
       └──────────────────────────────┼──→ mediation_mr
                                      │
report_generation ←──────────────────┘
```

上游任务失败时，依赖它的下游任务自动跳过（由 Pipeline Runner 控制）。

---

## 六、错误处理全链路

```
┌─────────────────────────────────────────────────────────┐
│ 前端                              │ 后端                    │
│                                   │                        │
│ taskStore.createTask()            │ POST /tasks            │
│   .catch(e → store.error = e.msg) │   参数校验 → 422       │
│                                   │   DB 异常 → 500        │
│                                   │                        │
│ taskStore.fetchTasks()            │ GET /tasks/{id}        │
│   task.status === 'failed'        │   error_code           │
│   → ErrorAlert 展示              │   error_message        │
│                                   │                        │
│ resultStore.fetchResult()         │ GET /tasks/{id}/result │
│   .catch() → "暂无可查看结果"     │   404 → Result not     │
│                                   │   found                │
└─────────────────────────────────────────────────────────┘
```

---

## 七、与现有代码的对应关系

| 现有文件（v0.1.0） | 架构文档对应层 | 变更方向 |
|---------------------|---------------|----------|
| `frontend/src/components/analysis/*.tsx` | Frontend Layer | 数据源从硬编码改为 store |
| `backend/app/api/tasks.py` | BFF/API Layer | 几乎不变 |
| `backend/app/services/task_orchestrator.py` | AI Orchestrator Layer | 移至 `orchestrator/`，增加 adapter dispatch |
| `backend/app/tasks/base.py` | AI Skill Adapter Layer | 重构为 `adapters/base.py` ISkillAdapter ABC |
| `backend/app/tasks/*.py`（7 个 Runner） | AI Skill Adapter / Mock | 移至 `adapters/<skill>/mock.py` |
| `analysis_scripts/**/mock_*.py` | 外部脚本 | 不变（仍被 MockAdapter 调用） |
| `backend/app/models/*.py` | Job/Task + Storage | 不变 |
| `backend/app/services/storage_service.py` | Storage Layer | 不变 |
| `backend/app/config.py` | Infrastructure | 新增 ADAPTER_MODE 等配置 |

---

## 八、接入路线图

```
Phase 1 ── 创建 adapters/ 包结构和 ISkillAdapter ABC
        ── 将现有 7 个 Runner 迁移为 MockAdapter
        ── 创建 adapter_registry + 环境变量切换
        ── 验证：现有 7 个 task_type 全部通过新路径执行成功

Phase 2 ── 前端 4 个分析模块接收真实数据
        ── 组件从 resultStore 获取 summary_json
        ── 移除所有硬编码 mock 常量
        ── 文件上传组件对接 POST /projects/{id}/files

Phase 3 ── 逐个替换 MockAdapter → RealAdapter
        ── 优先替换 image_segmentation（TSSA-UNet）
        ── 以 hybrid 模式灰度切换

Phase 4 ── 任务状态下钻完善（中间进度、取消）
        ── 轮询优化（可选 SSE）
```
