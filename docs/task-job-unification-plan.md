# AdipoInsight 任务体系统合方案

> 版本: v0.3.0 — 草案  
> 最后更新: 2026-05-19

## 1. 两套系统概述

目前后端存在两套并列运行的任务跟踪机制：

| 维度 | TaskOrchestrator (旧) | JobManager (新) |
|------|----------------------|-----------------|
| 存储 | SQLite (AnalysisTask 表) | 内存 dict (InMemoryJobStore) |
| 创建入口 | `POST /api/v1/tasks` | `POST /api/ai/{capability}/jobs` |
| 查询入口 | `GET /api/v1/projects/{pid}/tasks` | `GET /api/ai/jobs/{job_id}` |
| 前端轮询 | `taskStore.ts` (2s 退避) | `usePolling` (ReportPage 等) |
| 执行方式 | BackgroundTasks + dispatch_skill | 线程池 + SkillRegistry |
| 状态值 | pending / running / success / failed | queued / running / succeeded / failed |
| Job ID 格式 | 自增整数 | UUID 前 8 位字符串 |
| 流水线 | run_full_pipeline (串行 BackgroundTasks) | 每个 step 独立 Job |
| 废止 | 已弃用（无阻塞） | 有（ReportGenerationSkill 等） |

## 2. 当前依赖关系

### 2.1 仍依赖 AnalysisTask (TaskOrchestrator) 的功能

| 功能 | 原因 |
|----------|--------|
| `POST /api/v1/tasks` | 手动创建单步任务（旧前端"运行"按钮） |
| `POST /api/v1/projects/{pid}/pipeline/run-all` | 串行流水线执行（BackgroundTasks） |
| `GET /api/v1/projects/{pid}/tasks` | 前端 `fetchTasks` 和流水线概览 |
| `GET /api/v1/tasks/{id}/result` | 旧 GWAS/MR 等分析模块的结果查看 |
| `POST /api/v1/tasks/{id}/rerun` | 重新运行单个任务 |
| 前端 `taskStore` | tasks 数组、`fetchTasks`、`startPolling` |
| 前端 `pipelineProgress` | 基于 AnalysisTask[] 的去重进度计算 |
| 前端 `TaskCard` / `WorkflowStepper` | 渲染 AnalysisTask.status |

### 2.2 已迁移至 JobManager 的功能

| 功能 | 入口 |
|----------|--------|
| GWAS 分析 | `POST /api/ai/gwas/jobs` |
| MR 分析 | `POST /api/ai/mr/jobs` |
| 中介 MR | `POST /api/ai/mediation-mr/jobs` |
| 风险建模 | `POST /api/ai/risk-modeling/jobs` |
| 影像分割 | `POST /api/ai/segmentation/jobs` |
| 报告生成 | `POST /api/ai/report/jobs` |
| AI 解读 | `POST /api/ai/result-interpretation/jobs` |
| 报告页面轮询 | `ReportPage.tsx` (`usePolling`) |
| AI 聊天任务创建 | `ChatInput.tsx` |

## 3. 直接删除旧系统的风险

1. **前端流水线概览崩溃** — `taskStore` + `pipelineProgress` 完全依赖 `AnalysisTask[]`；删除后整个进度条、Stepper、TaskCard 网格将无法渲染。
2. **运行完整流水线功能消失** — 当前 `run-all` 通过 BackgroundTasks 串行执行 7 步；JobManager 没有对应的批量编排能力。
3. **旧项目历史数据不可用** — SQLite 中已有大量 AnalysisTask 记录，直接删除会丢失历史。
4. **前端 4+ 个组件直接读取 `task.status`** — `ProjectWorkspacePage`、`TaskCard`、`WorkflowStepper`、`GWASModule` 等组件均依赖 `AnalysisTask.status` 字段。
5. **`GET /api/v1/projects/{pid}/tasks` 是前端唯一任务列表来源** — 删除后前端将看不到任何任务记录。

## 4. 推荐统合方案（分阶段）

### 阶段 1：统一查询 Adapter（本 PR）

新增 `GET /api/v1/projects/{project_id}/jobs/unified` 端点：
- 同时查询 `AnalysisTask` (SQLite) 和 `JobManager.get_jobs_by_project()`。
- 将两者的不同状态值归一化为 `UnifiedJob` 结构。
- 保留 `GET /api/v1/projects/{pid}/tasks` 不变。
- 前端暂时不强制切换到新端点，仅在工作区页面新增可选调用。

### 阶段 2：前端渐进迁移

- `taskStore.fetchTasks` 在后台额外调用统一端点。
- `pipelineProgress` 逐步支持 `UnifiedJob` 输入。
- `TaskCard` 和 `WorkflowStepper` 适配新结构。

### 阶段 3：JobManager 持久化

- 将 `InMemoryJobStore` 替换为 SQLite 实现。
- AnalysisTask 和 JobManager Job 写入同一张 `job` 表。
- 逐步将旧 `create_task` 端点迁移至 JobManager。

### 阶段 4：移除旧代码

- 删除 `TaskOrchestrator`、`AnalysisTask` 模型。
- 清理 `BackgroundTasks` 相关代码。
- 前端不再依赖 `AnalysisTask` 类型。

## 5. 统一任务结构 (`UnifiedJob`)

```json
{
  "job_id": "string",          // AnalysisTask: "task-{id}"; JobManager: "job-{uuid}"
  "project_id": 1,
  "job_type": "gwas_analysis",   // 与 PIPELINE_ORDER 对齐
  "pipeline_step": "gwas_analysis",
  "status": "running",           // 归一化: queued | running | succeeded | failed | cancelled
  "progress": 45,
  "progress_stage": "处理中",
  "input": {},
  "result": {},
  "error_code": "",
  "error_message": "",
  "created_at": "2026-05-19T12:00:00Z",
  "updated_at": "2026-05-19T12:00:30Z",
  "started_at": "...",
  "finished_at": "...",
  "source": "analysis_task"    // 或其名称 "ai_job"
}
```

## 6. 状态映射

| 旧值 (AnalysisTask) | 新值 (JobManager) | 统一值 (UnifiedJob) |
|---------------------|-------------------|---------------------|
| pending | queued | **queued** |
| running | running | **running** |
| success | succeeded | **succeeded** |
| failed | failed | **failed** |
| cancelled | cancelled | **cancelled** |

## 7. 兼容性保障

- 所有现有 API 端点路径均保留。
- `AnalysisTask` 模型不下线；仅新增 `UnifiedJob` 视图。
- 前端可逐步迁移，不强制一次性切换。
- 旧 `TASK_TYPE_LABELS` 和 `PIPELINE_ORDER` 继续用于统一视图中的 step 映射。
