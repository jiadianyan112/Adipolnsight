# AI接入前项目结构诊断

> 扫描时间：2026-05-17
> 项目版本：v0.1.0 Mock-First
> 扫描范围：全项目（frontend、backend、analysis_scripts、mock_data、docs）

---

## 一、技术栈总览

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vite + React 19 + TypeScript 6 | React 19.2.6, TS ~6.0.2 |
| 前端路由 | react-router-dom | 7.15.1 |
| 状态管理 | Zustand | 5.0.13 |
| UI 样式 | Tailwind CSS 4 + 自建 Design Tokens | 4.3.0 |
| HTTP 请求 | Axios（单实例 + 拦截器） | 1.16.1 |
| 图表库 | Recharts | 3.8.1 |
| Markdown 渲染 | react-markdown | 10.1.0 |
| 后端框架 | FastAPI | 0.115.6 |
| ORM | SQLAlchemy (sync) | 2.0.36 |
| 数据库 | SQLite（文件型，零配置） | — |
| 分析脚本 | Python CLI（subprocess 调用） | — |
| 任务执行 | FastAPI BackgroundTasks（进程内） | — |

---

## 二、前端现状

### 2.1 页面路由（App.tsx:13）

| 路由 | 页面组件 | 状态 |
|------|----------|------|
| `/` | ProjectListPage | 已完成 |
| `/projects/new` | ProjectCreatePage | 已完成 |
| `/projects/:id` | ProjectWorkspacePage | 已完成 |
| `/projects/:id/report` | ReportPage | 已完成 |

### 2.2 组件清单（共 24 个）

**Layout 组件**（2 个）：
- `AppLayout` — 顶部导航 + `<Outlet />`，不使用 Sidebar
- `TopNavbar` — 深色导航栏，硬编码路由链接

**页面组件**（4 个）：
- `ProjectListPage` — 项目列表 + 空状态 + loading
- `ProjectCreatePage` — 项目创建表单
- `ProjectWorkspacePage` — 核心工作区，集成所有分析模块
- `ReportPage` — Markdown 报告查看

**分析模块组件**（4 个）：
- `ImageProcessingModule` — MRI 上传 + 脂肪表型指标卡片
- `GWASModule` — GWAS 分析 + OpenGWAS 数据获取 + 曼哈顿图
- `MRModule` — 孟德尔随机化 + 散点图 + 估计值表
- `MediationMRModule` — 中介 MR 分析 + 机制流程图 + 结果表

**工作流/任务组件**（3 个）：
- `WorkflowSelectionPanel` — GWAS / MR / Mediation 三个工作流选择卡片
- `WorkflowStepper` — 7 步流水线步骤指示器
- `TaskCard` — 单个任务卡片（运行/查看/重跑按钮）
- `TaskLogViewer` — 任务日志终端风格展示

**结果/报告组件**（2 个）：
- `UnifiedResultView` — 统一结果查看（summary cards + output files）
- `ReportViewer` — Markdown 渲染报告

**共享组件**（11 个）：
- `DashboardCard`、`PageShell`、`StatusBadge`、`ProgressBar`
- `ErrorAlert`、`MetricSummaryCard`、`MiniChartCard`
- `PrimaryButton`、`SecondaryButton`、`SectionTitle`
- `UploadDropzone`

### 2.3 状态管理（3 个 Zustand Store）

| Store | 关键方法 | 调用后端 |
|-------|----------|----------|
| `projectStore` | fetchProjects, fetchProject, createProject, deleteProject, createDemo | 是 |
| `taskStore` | fetchTasks, createTask, rerunTask, runFullPipeline, startPolling, stopPolling | 是 |
| `resultStore` | fetchResult, fetchReport, generateReport | 是 |

### 2.4 API 请求层

- 文件：`services/apiClient.ts`
- 单实例 Axios，baseURL: `/api/v1`，timeout: 30s
- Vite proxy 将 `/api` 转发到 `http://localhost:8000`
- 响应拦截器统一提取 `err.response.data.detail` 作为错误消息

### 2.5 关键发现：前端与后端的脱节

**问题 1：硬编码 mock 数据**
- `ImageProcessingModule.tsx:17-76` — 4 组脂肪表型数据（PHENOTYPE_DATA）硬编码在前端
- `ImageProcessingModule.tsx:68-77` — 8 个 SUMMARY_METRICS 指标硬编码
- `GWASModule.tsx:16-36` — `generateManhattanData()` 生成伪造曼哈顿图数据
- `MRModule.tsx:15-39` — `generateMRData()` 生成伪造 MR 散点数据 + IVW_LINE + MR_ESTIMATES
- `MediationMRModule.tsx:24-55` — 6 条中介 MR 结果数据（RESULTS_DATA）硬编码
- `ImageProcessingModule.tsx:136-141` — `handleFileSelect` 用 `setInterval` 模拟上传进度

**问题 2：假的上传组件**
- `ImageProcessingModule`、`GWASModule`、`MRModule` 中的 `<input type="file">` 标签没有绑定到真实文件上传 API
- `UploadDropzone` 组件已完整封装，但未被分析模块使用

**问题 3：demo 种子数据写死**
- `api/demo.py:37-40` — mock 文件名写死在 demo controller 中

---

## 三、后端现状

### 3.1 API 端点（6 个 Router）

| Router | 路径前缀 | 端点 |
|--------|----------|------|
| projects | `/api/v1/projects` | CRUD 完整 |
| files | `/api/v1/projects/{id}/files` | 上传/列表/下载 |
| tasks | `/api/v1/tasks`, `/api/v1/projects/{id}/tasks` | 创建/列表/详情/重跑/全流水线 |
| results | `/api/v1/tasks/{id}/result`, `/api/v1/projects/{id}/results` | 按任务查/按项目列 |
| reports | `/api/v1/projects/{id}/reports/generate`, `/api/v1/reports/{id}` | 生成/查看 |
| demo | `/api/v1/demo/seed` | 一键创建示例项目 |

### 3.2 数据模型（7 张表）

```
projects ──┬── samples
           ├── file_assets
           ├── analysis_tasks ──── analysis_results
           ├── reports
           └── audit_logs
```

### 3.3 任务执行机制

```
POST /api/v1/tasks
  → TaskOrchestrator.create_task() → 写入 DB，status=pending
  → BackgroundTasks.add_task(run_skill_task, task.id)
    → orchestrator.mark_running()
    → dispatch_skill(task, db)
      → RUNNER_REGISTRY[task_type].execute()
        → BaseSkillRunner.execute()
          → subprocess.run(["python", "analysis_scripts/.../mock_xxx.py", ...])
          → 解析 stdout 最后一行 JSON
          → mark_success() 或 mark_failed()
```

### 3.4 Skill Runner 注册表（7 个）

| task_type | Runner 类 | 脚本路径 |
|-----------|-----------|----------|
| image_segmentation | SegmentationSkillRunner | segmentation/mock_segmentation.py |
| gwas_analysis | GWASSkillRunner | gwas/mock_gwas.py |
| opengwas_fetch | OpenGWASSkillRunner | opengwas/mock_opengwas_fetch.py |
| mendelian_randomization | MRSkillRunner | mr/mock_mr.py |
| mediation_mr | MediationMRSkillRunner | mediation_mr/mock_mediation_mr.py |
| risk_modeling | RiskModelSkillRunner | risk_modeling/mock_risk_modeling.py |
| report_generation | ReportSkillRunner | report/mock_report.py |

### 3.5 Mock 脚本契约（统一）

所有 mock 脚本遵循相同的 CLI 契约：
```
python mock_xxx.py --output-dir <path> --task-id <id> [--other-args]
→ stdout: 日志行 + 最后一行 JSON
→ JSON: {"task_id", "status", "summary": {...}, "output_files": [...], "finished_at"}
→ exit code: 0
→ 输出文件写入 --output-dir
```

---

## 四、AI 接入点分析

### 4.1 架构优势

已有的分层架构非常清晰，接入 AI 只需要替换三层中的一层：

```
前端触发 → 后端接口 → SkillRunner → 真实 AI 脚本
                              ↓
                        Mock Adapter（当前）
```

**关键文件**：`backend/app/tasks/base.py` 中的 `BaseSkillRunner` 定义了适配器接口。

### 4.2 推荐的 AI 接入点（按优先级排序）

#### 接入点 1：SkillRunner 层（推荐首选）

- **位置**：`backend/app/tasks/` 下的 7 个 Runner 类
- **方式**：将 `script_path` 从 `mock_xxx.py` 改为真实脚本路径
- **影响范围**：仅后端，前端无需任何改动
- **风险**：低，接口契约已经统一

#### 接入点 2：前端组件结果数据绑定

- **当前**：前端组件使用硬编码 mock 数据渲染图表
- **目标**：从 `resultStore` 的 `currentResult.summary_json` 解析真实数据
- **影响组件**：`ImageProcessingModule`、`GWASModule`、`MRModule`、`MediationMRModule`
- **风险**：中，需要重构组件 props 和数据结构

#### 接入点 3：文件上传真实对接

- **当前**：`<input type="file">` 只更新本地 state，不上传
- **目标**：使用 `apiClient.post(/projects/{id}/files, FormData)` 真实上传
- **影响组件**：`ImageProcessingModule`、`GWASModule`、`MRModule`
- **风险**：低，后端文件上传 API 已完整

#### 接入点 4：AI 适配器抽象层

- **位置**：新建 `backend/app/adapters/` 目录
- **方式**：定义 `AIAdapter` ABC，实现 `MockAdapter` 和预留 `RealAdapter`
- **目的**：满足用户要求的 "mock adapter + real adapter 接口预留"
- **风险**：低，纯后端扩展

#### 接入点 5：任务轮询与实时状态推送

- **当前**：前端用 `setInterval(2000ms)` 轮询
- **可选升级**：WebSocket / SSE 推送任务状态变化
- **风险**：中，需要前后端配合

---

## 五、数据流现状 vs 目标

### 现状（前端数据来源）

```
前端图表数据
  ├── 硬编码常量（80%）← 问题所在
  ├── 随机生成函数（15%）← Manhattan、MR Scatter
  └── 后端 API 数据（5%） ← 仅 task status + summary display
```

### 目标数据流

```
用户操作 → 前端组件
  → apiClient.post(/tasks, {project_id, task_type, parameters})
    → FastAPI BackgroundTasks
      → SkillRunner (Mock → Real)
        → subprocess → AI 脚本
          → 输出文件写入 storage/
          → stdout JSON → AnalysisResult 写入 DB
            → 前端轮询 taskStore.fetchTasks
              → 组件从 resultStore 取数据渲染
```

---

## 六、明确的改动边界（不应触碰）

1. **前端页面布局**：AppLayout、TopNavbar、PageShell 结构不变
2. **设计系统**：`index.css` 中的 Design Tokens 不变
3. **路由结构**：4 个路由不增不减
4. **组件层次**：共享组件接口不变
5. **DB 表结构**：当前 7 张表模式够用，不需加列
6. **API 端点签名**：当前请求/响应格式不变

---

## 七、推荐的接入顺序

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| Phase 1 | 建立 AI Adapter 抽象层（ABC + Mock + Real 接口） | P0 |
| Phase 2 | 前端组件从 resultStore 读取真实数据，移除硬编码 | P0 |
| Phase 3 | 文件上传组件对接真实后端 API | P1 |
| Phase 4 | 任务状态下钻：TaskCard → 中间进度 → 失败详情 | P1 |
| Phase 5 | 逐个替换 Mock Runner 为 Real Runner | P2 |
| Phase 6 | 轮询升级为 SSE/WebSocket | P3 |

---

## 八、关键文件索引

| 用途 | 文件 |
|------|------|
| 前端类型定义 | `frontend/src/types/index.ts` |
| API 客户端 | `frontend/src/services/apiClient.ts` |
| 状态管理 | `frontend/src/stores/*Store.ts` |
| 核心工作区（集成点） | `frontend/src/pages/ProjectWorkspacePage.tsx` |
| 分析模块（需改数据源） | `frontend/src/components/analysis/*.tsx` |
| 后端入口 | `backend/app/main.py` |
| 任务执行核心 | `backend/app/tasks/base.py` |
| 任务编排 | `backend/app/services/task_orchestrator.py` |
| 7 个 Runner | `backend/app/tasks/*.py`（除 base/__init__） |
| Mock 脚本 | `analysis_scripts/**/mock_*.py` |
| 设计规范 | `frontend/src/index.css` |
| 中文文案 | `frontend/src/constants/uiText.ts` |
