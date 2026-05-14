# AdipoInsight Mock-First MVP 设计文档

## 元信息

- **项目**: AdipoInsight
- **文档类型**: 架构设计 spec
- **版本**: v1.0
- **日期**: 2026-05-14
- **策略**: Mock-First — 真实工程骨架 + 模拟计算核心
- **截止日期**: 17 天内可演示

---

## 1. 项目定位

AdipoInsight 是一个面向医学科研场景的 AI 分析平台。第一阶段采用 Mock-First 策略：页面、API、数据库、任务调度、文件存储、日志全是真实的，仅底层分析计算用 mock 脚本模拟。后续可逐模块替换为真实模型和真实数据。

**核心科研链路:**

```
创建项目 → 选择 mock 数据 → AI 影像分割 → GWAS 分析
→ OpenGWAS 数据获取 → 孟德尔随机化 → 中介 MR
→ 风险建模 → 科研报告生成
```

---

## 2. 技术栈

| 层 | 选型 | 说明 |
|---|------|------|
| 前端框架 | Vite + React 18 + TypeScript | 纯 SPA，无需 SSR |
| 样式 | Tailwind CSS | |
| 状态管理 | Zustand | 轻量，无 boilerplate |
| HTTP 客户端 | Axios | |
| 图表 | Recharts | |
| 后端框架 | Python FastAPI | |
| ORM | SQLAlchemy | |
| 数据校验 | Pydantic v2 | |
| 数据库 | SQLite | 零配置本地部署 |
| 任务调度 | FastAPI BackgroundTasks | 单进程内执行，无需 Redis |
| 分析脚本 | Python 3 (CLI) | subprocess 调用，统一 JSON I/O |
| 容器化 | 无 | 当前阶段不需要 |

---

## 3. 工程目录结构

```
adipoinsight/
├── frontend/                    # Vite + React + TypeScript
│   └── src/
│       ├── components/          # 通用 UI 组件
│       │   ├── layout/          # AppLayout, Sidebar
│       │   ├── project/         # ProjectCard, ProjectForm, ProjectHeader
│       │   ├── task/            # WorkflowStepper, TaskCard, TaskLogViewer
│       │   ├── result/          # UnifiedResultView (SummaryCards, ChartPanel, DataTable)
│       │   ├── report/          # ReportViewer
│       │   └── shared/          # StatusBadge, ProgressBar, ErrorAlert
│       ├── pages/               # 页面级组件
│       ├── stores/              # Zustand: projectStore, taskStore, resultStore
│       ├── services/            # Axios API client
│       └── types/               # TypeScript 类型
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, lifespan
│   │   ├── config.py            # 配置管理（从 .env 读取）
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── api/                 # 路由层
│   │   │   ├── projects.py
│   │   │   ├── files.py
│   │   │   ├── tasks.py
│   │   │   ├── results.py
│   │   │   ├── reports.py
│   │   │   └── demo.py
│   │   ├── models/              # SQLAlchemy ORM
│   │   │   ├── project.py
│   │   │   ├── sample.py
│   │   │   ├── file_asset.py
│   │   │   ├── analysis_task.py
│   │   │   ├── analysis_result.py
│   │   │   ├── report.py
│   │   │   └── audit_log.py
│   │   ├── schemas/             # Pydantic 请求/响应
│   │   ├── services/            # 业务逻辑
│   │   │   ├── task_orchestrator.py
│   │   │   ├── storage_service.py
│   │   │   └── report_service.py
│   │   ├── tasks/               # Skill Runner 体系
│   │   │   ├── base.py          # BaseSkillRunner
│   │   │   ├── segmentation.py
│   │   │   ├── gwas.py
│   │   │   ├── opengwas.py
│   │   │   ├── mr.py
│   │   │   ├── mediation_mr.py
│   │   │   ├── risk_modeling.py
│   │   │   └── report_gen.py
│   │   └── utils/               # 日志、错误码、工具
│   ├── scripts/
│   │   ├── seed_demo_project.py
│   │   └── run_all_demo_tasks.py
│   └── requirements.txt
├── analysis_scripts/            # 独立 CLI mock 脚本
│   ├── segmentation/mock_segmentation.py
│   ├── gwas/mock_gwas.py
│   ├── opengwas/mock_opengwas_fetch.py
│   ├── mr/mock_mr.py
│   ├── mediation_mr/mock_mediation_mr.py
│   ├── risk_modeling/mock_risk_modeling.py
│   └── report/mock_report.py
├── storage/                     # 本地文件存储（运行时生成）
│   └── projects/{project_id}/
│       ├── raw/                 # 原始文件
│       └── outputs/             # 各步骤输出
├── mock_data/                   # 预置 mock 数据集
│   ├── mri/
│   ├── phenotype/
│   ├── covariates/
│   └── genetics/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── database_schema.md
│   ├── mock_skills.md
│   └── real_module_replacement.md
└── README.md
```

---

## 4. 数据模型

### 4.1 Project

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | VARCHAR(255) | 项目名称 |
| research_goal | TEXT | 研究目标 |
| exposure | VARCHAR(255) | 暴露变量 |
| outcome | VARCHAR(255) | 结局变量 |
| mediator_set | VARCHAR(255) | 中介变量集（可选） |
| status | VARCHAR(32) | draft/active/completed |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### 4.2 Sample

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | INTEGER FK | |
| subject_id | VARCHAR(64) | |
| mri_file_path | VARCHAR(512) | |
| phenotype_file_path | VARCHAR(512) | |
| covariate_file_path | VARCHAR(512) | |
| genotype_file_path | VARCHAR(512) | |
| qc_status | VARCHAR(32) | pending/passed/failed |
| created_at | DATETIME | |

### 4.3 FileAsset

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | INTEGER FK | |
| sample_id | INTEGER FK | nullable |
| file_name | VARCHAR(255) | |
| file_type | VARCHAR(64) | mri/phenotype/covariates/genotype/output |
| file_path | VARCHAR(512) | 相对 storage 路径 |
| file_size | INTEGER | bytes |
| created_at | DATETIME | |

### 4.4 AnalysisTask

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | INTEGER FK | |
| task_type | VARCHAR(64) | 见 4.7 枚举 |
| task_name | VARCHAR(255) | 显示名 |
| status | VARCHAR(32) | pending/running/success/failed/cancelled |
| progress | INTEGER | 0-100 |
| input_json | TEXT | 输入参数 JSON |
| output_json | TEXT | 输出摘要 JSON |
| error_code | VARCHAR(64) | 失败时填充 |
| error_message | TEXT | |
| started_at | DATETIME | |
| finished_at | DATETIME | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### 4.5 AnalysisResult

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| task_id | INTEGER FK | |
| project_id | INTEGER FK | |
| result_type | VARCHAR(64) | 同 task_type |
| summary_json | TEXT | 结果摘要 |
| output_files_json | TEXT | 输出文件列表 JSON |
| created_at | DATETIME | |

### 4.6 Report

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | INTEGER FK | |
| title | VARCHAR(255) | |
| content_markdown | TEXT | 报告 Markdown 全文 |
| status | VARCHAR(32) | draft/final |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### 4.7 AuditLog

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| project_id | INTEGER FK | |
| task_id | INTEGER FK | nullable |
| action | VARCHAR(128) | 操作类型 |
| detail_json | TEXT | 操作详情 |
| created_at | DATETIME | |

### 4.8 枚举值

**task_type**: `image_segmentation` | `gwas_analysis` | `opengwas_fetch` | `mendelian_randomization` | `mediation_mr` | `risk_modeling` | `report_generation`

**task_status**: `pending` → `running` → `success` / `failed` / `cancelled`

**result_type**: 与 task_type 一一对应

## 5. 统一 JSON 协议

### 5.1 任务输入

```json
{
  "project_id": "1",
  "task_type": "mendelian_randomization",
  "input_files": {
    "exposure_stats": "storage/projects/1/outputs/gwas/gwas_summary_stats.tsv",
    "outcome_stats": "storage/projects/1/outputs/opengwas/outcome_summary_stats.tsv"
  },
  "parameters": {
    "exposure": "Liver_PDFF",
    "outcome": "Osteoporosis",
    "method": "IVW"
  }
}
```

### 5.2 任务输出

```json
{
  "task_id": "1",
  "status": "success",
  "summary": {
    "exposure": "Liver_PDFF",
    "outcome": "Osteoporosis",
    "beta": 0.184,
    "or": 1.20,
    "p_value": 0.004
  },
  "output_files": [
    "mr_results.csv",
    "forest_plot.png",
    "scatter_plot.png",
    "mr_summary.json"
  ],
  "finished_at": "2026-05-14T12:00:00"
}
```

### 5.3 错误输出

```json
{
  "task_id": "1",
  "status": "failed",
  "error_code": "SCRIPT_EXECUTION_FAILED",
  "error_message": "mock script returned non-zero exit code",
  "trace_id": "uuid"
}
```

---

## 6. API 设计

所有接口前缀 `/api/v1/`。

### 6.1 项目管理

```
POST   /api/v1/projects                # 创建项目
GET    /api/v1/projects                # 项目列表（支持 ?status=active）
GET    /api/v1/projects/{id}           # 项目详情
DELETE /api/v1/projects/{id}           # 删除项目（级联删除关联数据）
```

### 6.2 文件管理

```
POST   /api/v1/projects/{id}/files     # 上传文件 (multipart/form-data)
GET    /api/v1/projects/{id}/files     # 文件列表
GET    /api/v1/files/{id}/download     # 下载文件
```

### 6.3 任务管理

```
POST   /api/v1/tasks                      # 创建并启动单个任务
GET    /api/v1/tasks/{id}                 # 任务状态（进度 + 输出摘要）
GET    /api/v1/projects/{id}/tasks        # 项目下任务列表
POST   /api/v1/tasks/{id}/rerun           # 重跑任务
POST   /api/v1/projects/{id}/pipeline/run-all  # 一键顺序运行全流程
```

### 6.4 结果

```
GET    /api/v1/tasks/{id}/result          # 单个任务结果
GET    /api/v1/projects/{id}/results      # 项目聚合结果
```

### 6.5 报告

```
POST   /api/v1/projects/{id}/reports/generate  # 生成报告
GET    /api/v1/reports/{id}                    # 获取报告内容 (Markdown)
```

### 6.6 系统

```
GET    /api/v1/health                    # 健康检查
POST   /api/v1/demo/seed                 # 一键创建 demo 项目
```

---

## 7. 任务调度中心

### 7.1 调度流程

```
POST /api/v1/tasks
  → TaskOrchestrator.create_task()
    → 写入 AnalysisTask (status=pending)
    → BackgroundTasks.add_task(run_skill, task_id)
      → 查表获取 task 元信息
      → TaskOrchestrator.dispatch(task)
        → 根据 task_type 选择 SkillRunner
        → runner.prepare_inputs()   → 组装参数
        → runner.build_command()    → 拼接 CLI 命令
        → runner.run()              → subprocess.run()
        → runner.parse_outputs()    → 解析 stdout JSON
        → runner.save_results()     → 写入 AnalysisResult + storage 文件
        → 更新 AnalysisTask (status=success 或 failed)
```

### 7.2 BaseSkillRunner

```python
class BaseSkillRunner:
    task_type: str
    script_path: str

    def prepare_inputs(self, task: AnalysisTask) -> dict: ...
    def build_command(self, inputs: dict) -> list[str]: ...
    def run(self, cmd: list[str]) -> subprocess.CompletedProcess: ...
    def parse_outputs(self, stdout: str) -> dict: ...
    def save_results(self, task, output: dict) -> AnalysisResult: ...
    def execute(self, task: AnalysisTask): ...  # 串联上述步骤
```

### 7.3 7 个 Skill Runner

| Runner | task_type | 脚本路径 |
|--------|-----------|---------|
| SegmentationSkillRunner | image_segmentation | analysis_scripts/segmentation/mock_segmentation.py |
| GWASSkillRunner | gwas_analysis | analysis_scripts/gwas/mock_gwas.py |
| OpenGWASSkillRunner | opengwas_fetch | analysis_scripts/opengwas/mock_opengwas_fetch.py |
| MRSkillRunner | mendelian_randomization | analysis_scripts/mr/mock_mr.py |
| MediationMRSkillRunner | mediation_mr | analysis_scripts/mediation_mr/mock_mediation_mr.py |
| RiskModelSkillRunner | risk_modeling | analysis_scripts/risk_modeling/mock_risk_modeling.py |
| ReportSkillRunner | report_generation | analysis_scripts/report/mock_report.py |

### 7.4 Pipeline 顺序执行

`run-all` 接口按依赖链依次触发，前一个 success 后才启动下一个。失败时终止后续步骤。

```
segmentation → gwas → opengwas → mr → mediation_mr → risk_modeling → report
```

### 7.5 进度标记

```
0%   → created
10%  → preparing inputs
30%  → running script
70%  → parsing outputs
90%  → saving results
100% → success
```

---

## 8. Mock 分析脚本规范

### 8.1 通用 CLI 约定

每个 mock 脚本是独立的 Python CLI 程序：

```bash
python mock_xxx.py --input-data /path/to/input.json --output-dir /path/to/output --task-id 42
```

- `--input-data`: 包含 task.input_json 的 JSON 文件路径
- `--output-dir`: 输出目录绝对路径
- `--task-id`: 任务 ID（用于日志）

### 8.2 输出约定

- stdout 最后一行输出标准 JSON（同 5.2 格式），其余行视为日志
- 所有图表/数据文件写入 `--output-dir`
- 退出码 0 = 成功，非 0 = 失败

### 8.3 各脚本输出内容

**segmentation**: mask 路径、overlay_preview.png、segmentation_metrics.json、fat_quantification.csv、包含 liver_pdff / visceral_fat_volume / subcutaneous_fat_volume / bone_marrow_fat_fraction / dice 指标

**gwas**: gwas_summary_stats.tsv、lead_snps.csv、significant_loci.csv、manhattan_plot.png、qq_plot.png、gwas_summary.json

**opengwas**: outcome_summary_stats.tsv、harmonised_preview.csv、opengwas_metadata.json

**mr**: mr_results.csv、heterogeneity.csv、pleiotropy.csv、forest_plot.png、scatter_plot.png、mr_summary.json

**mediation_mr**: mediation_results.csv、candidate_proteins.csv、mediation_barplot.png、mediation_summary.json

**risk_modeling**: ols_results.csv、rcs_results.csv、rcs_curve.png、risk_summary.json

**report**: final_report.md（聚合所有上游结果生成结构化 Markdown 报告）

---

## 9. 前端设计

### 9.1 路由

```
/                          → ProjectListPage      项目列表
/projects/new              → ProjectCreatePage    创建项目
/projects/:id              → ProjectWorkspacePage 项目工作台
/projects/:id/report       → ReportPage           科研报告
```

### 9.2 核心组件

**WorkflowStepper**: 7 步流程步骤条，每步显示 task_type 名称 + 状态灯（灰色=未开始，蓝色=运行中，绿色=完成，红色=失败）

**TaskCard**: 单个步骤的操作卡片，包含模块名称、输入摘要、运行状态、进度条、启动/查看结果/重跑按钮

**UnifiedResultView** (方案 A 核心): 根据 result_type 自适应渲染：
- SummaryCards — 从 summary_json 自动渲染指标卡片
- ChartPanel — 展示 PNG 图片
- DataTable — 从 CSV/JSON 文件渲染数据表格

**TaskLogViewer**: 展示 stdout/stderr、exit_code、start_time、finish_time

**ReportViewer**: Markdown 渲染器，展示最终科研报告

### 9.3 Zustand Stores

```
projectStore:  projects[], currentProject, loading, error
taskStore:     tasks[], pollingTimer, fetchTasks(), startPolling(), stopPolling()
resultStore:   currentResult, fetchResult()
```

### 9.4 任务状态轮询

- `taskStore` 启动 2 秒间隔轮询 `GET /api/v1/projects/{id}/tasks`
- 当所有任务 status 不再是 running 时停止轮询
- 任务完成后自动加载对应结果

---

## 10. 文件存储

### 10.1 目录布局

```
storage/projects/{project_id}/
├── raw/
│   ├── mri/
│   ├── phenotype/
│   ├── covariates/
│   └── genotype/
└── outputs/
    ├── segmentation/
    ├── gwas/
    ├── opengwas/
    ├── mr/
    ├── mediation_mr/
    ├── risk_modeling/
    └── report/
```

### 10.2 StorageService

```python
class StorageService:
    def get_project_root(project_id: int) -> Path: ...
    def get_output_dir(project_id: int, task_type: str) -> Path: ...
    def save_upload(file, project_id: int, file_type: str) -> FileAsset: ...
    def list_project_files(project_id: int) -> list[Path]: ...
    def ensure_dirs(project_id: int): ...  # 创建目录结构
```

### 10.3 适配器模式

```python
class StorageAdapter(ABC):
    @abstractmethod
    def save(self, file, path): ...
    @abstractmethod
    def get(self, path) -> bytes: ...

class LocalStorageAdapter(StorageAdapter): ...  # 当前实现
# class S3StorageAdapter(StorageAdapter): ...    # 预留
```

---

## 11. 错误处理

### 11.1 错误码

| 错误码 | 说明 |
|--------|------|
| SCRIPT_NOT_FOUND | mock 脚本文件缺失 |
| SCRIPT_EXECUTION_FAILED | 脚本返回非零退出码 |
| OUTPUT_JSON_INVALID | stdout JSON 解析失败 |
| OUTPUT_FILE_MISSING | 预期输出文件未生成 |
| TASK_TIMEOUT | 执行超过 300 秒 |
| FILE_NOT_FOUND | 输入文件路径无效 |
| DATABASE_ERROR | 数据库操作异常 |

### 11.2 后端统一响应格式

```json
{
  "error_code": "OUTPUT_JSON_INVALID",
  "message": "The mock script output JSON could not be parsed.",
  "trace_id": "uuid"
}
```

### 11.3 前端错误展示

ErrorAlert 组件展示 error_code + message，每个 TaskCard 在失败时显示错误信息并提供重跑按钮。

---

## 12. 日志与审计

### 12.1 任务级日志

每个任务执行时在 output 目录生成：

- `run.log` — stdout + stderr 全文
- `command.txt` — 实际执行的完整命令
- `output_manifest.json` — 所有输出文件清单及路径

### 12.2 审计记录

每次关键操作写入 audit_logs 表：
- 创建项目 / 上传文件 / 启动任务 / 取消任务 / 重跑任务 / 生成报告

前端项目详情页展示操作时间线。

---

## 13. Demo 流程

1. 用户访问首页，点击 "一键创建 Demo 项目"
2. 后端 `POST /api/v1/demo/seed` 创建项目 + 关联 mock 数据文件
3. 自动跳转项目工作台
4. 用户点击 "Run Full Pipeline"
5. 后端 `POST /api/v1/projects/{id}/pipeline/run-all` 顺序执行 7 个任务
6. 前端 WorkflowStepper 实时更新状态灯，每步完成即可点 "查看结果"
7. 全部完成后点击 "生成报告"
8. 报告页展示完整结构化 Markdown 报告，标注 mock 数据来源

---

## 14. 后续真实模块替换接口

替换策略：每个 mock 脚本的 CLI 参数和输出 JSON schema 构成契约边界。替换时只需：
1. 编写新的真实脚本，保持相同的 CLI 参数
2. 保持相同的 stdout JSON 输出格式
3. 更新 SkillRunner 的 `script_path` 指向新脚本

| 模块 | Mock 脚本 | 真实替换 |
|------|----------|---------|
| 影像分割 | mock_segmentation.py | TSSA-UNet inference |
| GWAS | mock_gwas.py | REGENIE pipeline |
| OpenGWAS | mock_opengwas_fetch.py | IEU OpenGWAS API |
| MR | mock_mr.py | TwoSampleMR R 包 |
| 中介 MR | mock_mediation_mr.py | 真实 pQTL + TwoStepMR |
| 风险建模 | mock_risk_modeling.py | 真实临床风险模型 |

---

## 15. 验收标准

1. 用户能创建项目并看到项目列表
2. 一键 Demo 能创建完整项目 + 关联 mock 数据
3. 每个分析任务能从 pending → running → success
4. 每个任务的输出文件真实写入 storage
5. 7 个步骤的 UnifiedResultView 能展示结果
6. Run Full Pipeline 能顺序执行全部 7 个任务
7. 科研报告生成并包含所有模块结果
8. 任务失败时展示错误信息和重跑按钮
9. 审计时间线记录关键操作
10. README 包含完整的本地启动步骤
