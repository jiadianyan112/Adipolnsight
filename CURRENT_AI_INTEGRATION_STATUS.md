# AdipoInsight AI 接入当前状态报告

> 自动生成：2026-05-18
> 项目版本：v0.2.0
> 分支：`master`（clean，无未提交修改）

---

## 一、技术栈总览

| 层级 | 技术 | 版本/说明 |
|------|------|-----------|
| 前端框架 | Vite + React 19 + TypeScript | React 19.2.6 |
| 前端路由 | react-router-dom | 7.15.1 |
| 状态管理 | Zustand | 5.0.13 |
| UI 样式 | Tailwind CSS 4 + 自建 Design Tokens | 4.3.0 |
| HTTP 请求 | Axios（单实例 + 拦截器） | 1.16.1 |
| 图表库 | Recharts | 3.8.1 |
| Markdown 渲染 | react-markdown | 10.1.0 |
| 后端框架 | FastAPI | 0.115.6 |
| ORM | SQLAlchemy (sync + aiosqlite) | 2.0.36 |
| 数据库 | SQLite（文件型） | `adipoinsight.db` |
| LLM SDK | openai (OpenAI 兼容协议) | 用于 DeepSeek Provider |
| 任务执行 | threading.Thread（后台线程） | daemon mode |
| AI 模式 | Mock（所有 7 个 Skill） | 各 `mode` 属性硬编码返回 `"mock"` |

---

## 二、后端 AI 架构

### 2.1 核心目录结构

```
backend/app/ai/
├── __init__.py                # 统一导出
├── base.py                    # Skill ABC, SkillOutput, SkillContext, SkillMode
├── registry.py                # SkillRegistry 单例（注册/查找/调度）
├── job_manager.py             # JobManager 单例（创建/运行/轮询/取消）
├── agent_orchestrator.py      # AgentOrchestrator 单例（NL→Job 全链路编排）
├── intent_parser.py           # RuleBasedIntentParser（关键词匹配，保留作为 fallback）
├── intent_types.py            # 共享 IntentParseResult / STANDARD_INTENT
├── test_agent_orchestrator.py # 16 个 pytest 测试用例
├── test_intent_parser.py      # 19 个场景测试 + 手动 demo
├── test_error_handling.py     # 5 种错误场景测试
├── skills/                    # 7 个 Skill Adapter 实现
│   ├── __init__.py            # import 时自动注册所有 skill
│   ├── image_segmentation.py  # C1
│   ├── phenotype_quantification.py # C2
│   ├── gwas_analysis.py       # C3
│   ├── two_sample_mr.py       # C4
│   ├── mediation_mr.py        # C5
│   ├── risk_modeling.py       # C6
│   └── report_generation.py   # C7
└── llm/
    ├── __init__.py            # 统一导出，自动注册 DeepSeekProvider（如果 API KEY 已设置）
    ├── provider.py            # LLMProvider ABC + MockProvider + ProviderRegistry
    ├── deepseek_provider.py   # DeepSeekProvider（OpenAI 兼容协议）
    ├── service.py             # LLMService 统一调用入口（provider 选择/超时/重试/错误转换）
    ├── deepseek_intent_parser.py  # LLMIntentParser（DeepSeek 驱动的意图识别）
    ├── hybrid_intent_parser.py    # HybridIntentParser（rule→LLM→fallback）
    └── tests/
        └── demo_provider.py   # LLM provider 演示
```

### 2.2 关键架构组件状态

| 组件 | 文件 | 状态 | 说明 |
|------|------|------|------|
| Skill 基类 | `ai/base.py` | 完成 | `Skill(ABC)` + `SkillOutput` + `SkillContext` |
| SkillRegistry | `ai/registry.py` | 完成 | 单例，7 个 skill 已注册，含 `dispatch()` 方法 |
| JobManager | `ai/job_manager.py` | 完成 | 单例，InMemoryJobStore，后台线程执行，支持进度/取消 |
| AgentOrchestrator | `ai/agent_orchestrator.py` | 完成 | 使用 `hybrid_intent_parser`，参数补全，二次校验 |
| RuleBasedIntentParser | `ai/intent_parser.py` | 完成 | 8 个意图模式 + query_status，保留作为 fallback |
| IntentParseResult | `ai/intent_types.py` | 完成 | 共享类型，source="rule"/"llm"/"hybrid" |
| LLMProvider ABC | `ai/llm/provider.py` | 完成 | `LLMProvider` + `MockProvider` + `ProviderRegistry` |
| DeepSeekProvider | `ai/llm/deepseek_provider.py` | 完成 | OpenAI 兼容 SDK，thinking 模式，重试，错误映射 |
| LLMService | `ai/llm/service.py` | 完成 | 统一调用入口，provider 选择、超时、重试、错误转换 |
| MockProvider | `ai/llm/provider.py` | 完成 | 自动注册到 ProviderRegistry，含 intent 模板响应 |
| LLMIntentParser | `ai/llm/deepseek_intent_parser.py` | 完成 | 通过 LLMService 调用，返回 IntentParseResult |
| HybridIntentParser | `ai/llm/hybrid_intent_parser.py` | 完成 | rule→LLM→fallback 策略，source 标记，参数合并 |
| ImageSegmentation Skill | `ai/skills/image_segmentation.py` | 完成 | mock 模式，真实 MRI 指标（DICE 0.82-0.96） |
| PhenotypeQuant Skill | `ai/skills/phenotype_quantification.py` | 完成 | mock 模式，8 项脂肪表型指标 |
| GWAS Analysis Skill | `ai/skills/gwas_analysis.py` | 完成 | mock 模式，贴合真实 GWAS 数据 |
| TwoSampleMR Skill | `ai/skills/two_sample_mr.py` | 完成 | mock 模式，4 种 MR 方法 + 异质性/多效性检验 |
| MediationMR Skill | `ai/skills/mediation_mr.py` | 完成 | mock 模式，12 种候选蛋白，deCODE pQTL 数据库 |
| RiskModeling Skill | `ai/skills/risk_modeling.py` | 完成 | mock 模式，OLS+RCS+MultiLogistic |
| ReportGeneration Skill | `ai/skills/report_generation.py` | 完成 | mock 模式，9 章节结构化报告 |
| AI Job API | `api/ai_jobs.py` | 完成 | 8 个端点（CRUD + agent + capabilities + llm/health） |
| LLM Schema | `schemas/llm.py` | 完成 | LLMRequest/Response/IntentResult/Error 等 Pydantic 模型 |
| AI Schema | `schemas/ai.py` | 完成 | 完整的 Pydantic 模型（7 个能力 + Job + Response Envelope） |
| 错误体系 | `errors.py` | 完成 | 10+ 错误码 + HTTP 状态映射 |
| 配置 | `config.py` | 完成 | 所有 LLM 环境变量已定义 |

---

## 三、前端 AI 接入方式

### 3.1 TypeScript 类型

| 文件 | 内容 |
|------|------|
| `types/ai.ts` | `AICapabilityType`、`AIAdapterMode`、`AI_CAPABILITY_LABELS`、依赖关系、Pipeline 顺序 |
| `types/job.ts` | `AIJobStatus`、`AIJobProgress`、`AIJobErrorCode`、`AIJob`、轮询配置 |
| `types/llm.ts` | `LLMProviderName`、`LLMRequest/Response`、`LLMIntentResult`、`StandardIntent` 等 |
| `types/analysis.ts` | 各分析模块的组件 Props 类型 |
| `types/segmentation.ts` | 分割结果专用类型 |

### 3.2 API 客户端

| 文件 | 内容 |
|------|------|
| `services/apiClient.ts` | Axios 单实例，baseURL `/api/v1`，30s timeout，响应拦截器 |
| `services/aiService.ts` | 完整的 AI API 封装：文件上传、7 个能力 Job 创建、Job 状态/结果、Agent 查询、Job 取消 |

### 3.3 AI 相关组件

| 组件 | 文件 | 状态 |
|------|------|------|
| ChatInput | `components/agent/ChatInput.tsx` | 完成：自然语言输入 → POST `/api/ai/agent` → 4 种 answerType 展示 + 进度轮询 |
| ImageProcessingModule | `components/analysis/ImageProcessingModule.tsx` | 待改造：硬编码 mock 数据 |
| GWASModule | `components/analysis/GWASModule.tsx` | 待改造：硬编码 mock 数据 |
| MRModule | `components/analysis/MRModule.tsx` | 待改造：硬编码 mock 数据 |
| MediationMRModule | `components/analysis/MediationMRModule.tsx` | 待改造：硬编码 mock 数据 |
| RiskModelingModule | `components/analysis/RiskModelingModule.tsx` | 待改造：硬编码 mock 数据 |

### 3.4 AI Store

| Store | 文件 | 说明 |
|-------|------|------|
| taskStore | `stores/taskStore.ts` | 任务 CRUD + 轮询 |
| resultStore | `stores/resultStore.ts` | 结果获取 |
| projectStore | `stores/projectStore.ts` | 项目管理 |

---

## 四、已完成任务清单

### Phase 1：AI 核心基础设施
- [x] **AI Job Manager** (`job_manager.py`) — InMemoryJobStore，后台线程执行，进度/取消/轮询
- [x] **AI Skill Registry** (`registry.py`) — 单例，7 个 skill 注册 + dispatch()
- [x] **7 个 AI Skill Adapter** — 全部实现，mock 模式，含 `validate_input()` + `run()` + `get_input_schema()`
- [x] **Skill 基类** (`base.py`) — `Skill(ABC)` + `SkillOutput` + `SkillContext`

### Phase 2：LLM Provider 抽象层
- [x] **LLMProvider ABC** (`provider.py`) — `chat()` / `chat_json()` / `stream_chat()`
- [x] **MockProvider** (`provider.py`) — 含 intent/keyword 匹配 + 多任务类型 mock 响应
- [x] **ProviderRegistry** (`provider.py`) — 注册/查找/默认 provider 切换

### Phase 3：DeepSeek 接入
- [x] **DeepSeekProvider** (`deepseek_provider.py`) — OpenAI 兼容 SDK，thinking 模式，重试，错误映射，JSON mode，日志脱敏
- [x] **LLMService** (`service.py`) — 统一调用入口，provider 选择，超时/重试/错误转换
- [x] **`/api/ai/llm/health`** (`api/ai_jobs.py`) — mock/deepseek 健康检查（含 ping 测试），自动检测 DEEPSEEK_API_KEY 是否配置

### Phase 4：意图识别三层
- [x] **RuleBasedIntentParser** (`intent_parser.py`) — 8 个意图模式 + keyword scoring + 参数提取，作为 fallback
- [x] **LLMIntentParser** (`deepseek_intent_parser.py`) — DeepSeek 驱动意图解析，system prompt 约束，禁止编造参数，schema validate
- [x] **HybridIntentParser** (`hybrid_intent_parser.py`) — rule→LLM→fallback 三级策略，source 标记，参数合并
- [x] **共享类型** (`intent_types.py`) — `IntentParseResult` + `STANDARD_INTENT`

### Phase 5：Agent Orchestrator
- [x] **AgentOrchestrator** (`agent_orchestrator.py`) — 使用 `hybrid_intent_parser`，参数补全 + 上下文合并 + 默认值注入
- [x] **Skill.validate_input 二次校验** — 在创建 Job 前执行（`_create_and_run_job` L314）
- [x] **POST `/api/ai/agent`** (`api/ai_jobs.py`) — 自然语言 → AgentOrchestrator 全链路
- [x] **4 种 answerType**：`job_created` / `need_more_info` / `unsupported` / `error`
- [x] **NextAction 引导**：查看结果、查看能力、补充参数、重试
- [x] **PARAM_HINTS** — 7 个能力的必需参数和提示

### Phase 6：前端 AI 对接
- [x] **ChatInput 组件** (`ChatInput.tsx`) — 自然语言输入 → agentQuery → 4 种结果状态展示 + Job 进度轮询
- [x] **aiService** (`aiService.ts`) — 完整的 AI API 封装（旧 `/api/v1/tasks` + 新 `/api/ai/*`）
- [x] **TypeScript 类型** — AI/Job/LLM/Analysis 完整类型定义
- [x] **后端所有端点** — `/api/ai/{capability}/jobs`、`/api/ai/jobs/{id}`、`/api/ai/jobs/{id}/result`、`/api/ai/jobs/{id}/cancel`、`/api/ai/agent`、`/api/ai/capabilities`、`/api/ai/llm/health`

### Phase 7：测试
- [x] **AgentOrchestrator 测试** (`test_agent_orchestrator.py`) — 16 个 pytest 用例
- [x] **IntentParser 测试** (`test_intent_parser.py`) — 19 个场景
- [x] **Error Handling 测试** (`test_error_handling.py`) — 5 个场景

### Phase 8：文档
- [x] `docs/AI_Integration_Architecture.md` — 7 层架构设计
- [x] `docs/AI_Capability_Map.md` — 8 个能力详细规格
- [x] `docs/DeepSeek接入点扫描报告.md` — 接入前诊断
- [x] `AI接入前项目结构诊断.md` — 项目结构与前端脱节问题诊断

---

## 五、未完成任务清单

### 5.1 高优先级（阻塞）
- [ ] **缺失 `.env` 文件** — 当前环境中只有 `.env.example`，没有 `.env`。DeepSeek API 无法使用（`DEEPSEEK_API_KEY` 为空）。需从 `.env.example` 复制并填入真实 `DEEPSEEK_API_KEY`
- [ ] **前端分析模块硬编码数据** — `ImageProcessingModule`、`GWASModule`、`MRModule`、`MediationMRModule` 中仍使用硬编码 mock 数据渲染图表，应从 `resultStore` 读取后端返回的 `summary_json`
- [ ] **文件上传真实对接** — 分析模块中的 `<input type="file">` 未绑定到真实上传 API

### 5.2 中优先级（功能增强）
- [ ] **流式输出（SSE）** — DeepSeekProvider 的 `stream_chat()` 方法仅抛出 `NotImplementedError`
- [ ] **对话历史持久化** — ChatInput 没有对话历史状态，页面刷新后丢失
- [ ] **Error Explainer** — LLM 驱动的错误解释（`ai/llm/` 目录中无此模块）
- [ ] **Result Interpreter** — LLM 驱动的结果解读（`ai/llm/` 目录中无此模块）
- [ ] **Report Enhancer** — LLM 驱动报告增强（`report_generation._run_real()` 返回 `NOT_IMPLEMENTED`）

### 5.3 低优先级（后续迭代）
- [ ] **JobStore 持久化** — 当前 InMemoryJobStore，重启丢失所有 Job
- [ ] **真实模式开关** — 所有 Skill 的 `mode` 属性硬编码返回 `"mock"`，未从环境变量 `AI_MODE_PER_SKILL` 读取
- [ ] **Pipeline 自动执行** — 当前前端 `runFullPipeline` 使用旧的 `/api/v1/projects/{id}/pipeline/run-all`，未使用新 AI Job API
- [ ] **WebSocket 推送** — Job 进度当前靠前端轮询（2s interval），未实现服务端推送

---

## 六、DeepSeek 接入状态

### 6.1 已完成的接入

| 模块 | 状态 | 文件 |
|------|------|------|
| Provider 封装 | 完成 | `ai/llm/deepseek_provider.py` |
| OpenAI 兼容 SDK | 完成 | 使用 `openai.OpenAI(api_key=, base_url=, timeout=)` |
| Thinking 模式 | 完成 | 环境变量 `DEEPSEEK_ENABLE_THINKING` + `DEEPSEEK_REASONING_EFFORT` |
| JSON Mode | 完成 | `response_format={"type": "json_object"}` |
| 错误处理 | 完成 | 6 种异常类型分类处理（Auth/RateLimit/Timeout/Connection/APIStatus/Generic） |
| 重试机制 | 完成 | 最多 `LLM_MAX_RETRIES` 次重试，指数退避 |
| 日志脱敏 | 完成 | `_sanitize_for_log()` 限制 120 字符 |
| 模型选择 | 完成 | 推理任务（report/interpretation）→ `DEEPSEEK_REASONING_MODEL`，其他 → `DEEPSEEK_MODEL` |
| 健康检查 | 完成 | `GET /api/ai/llm/health` — 三种状态（mock/no-key/ping-test） |
| 意图解析 | 完成 | `LLMIntentParser` — 通过 `LLMService` 调用，JSON 输出 schema 校验 |
| Hybrid Parser | 完成 | `HybridIntentParser` — 三层策略 |

### 6.2 当前生效状态

- **LLM_PROVIDER**: `mock`（默认，因为 `LLM_PROVIDER` 环境变量未设置）
- **DEEPSEEK_API_KEY**: 未配置（`.env` 文件不存在）
- **DeepSeekProvider 注册状态**: 未注册到 ProviderRegistry（`ai/llm/__init__.py` L27 中 `DeepSeekProvider()` 初始化抛出 `ValueError`，被静默捕获，因为它需要 `DEEPSEEK_API_KEY`）
- **HybridIntentParser 当前行为**: 仅使用 rule parser（LLM parser import 会成功，但 LLMService 只返回 mock provider 的结果或错误）

### 6.3 如何启用 DeepSeek

```bash
# 1. 创建 .env 文件
cp .env.example .env

# 2. 编辑 .env，填入真实 API Key
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-real-key-here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_REASONING_MODEL=deepseek-v4-pro
DEEPSEEK_ENABLE_THINKING=false

# 3. 重启后端
# DeepSeekProvider 初始化成功 → 注册到 ProviderRegistry
# LLMService 默认 provider → "deepseek"
# HybridIntentParser → rule → LLM(deepseek) → fallback
```

---

## 七、Hybrid Intent Parser 当前实现状态

### 7.1 完整实现

`HybridIntentParser`（`ai/llm/hybrid_intent_parser.py`）已完整实现三级策略：

```
Step 1: RuleBasedIntentParser.parse()
    ↓
  置信度 >= 0.85 且缺失参数 <= 2？
    YES → 返回，source="rule"
    NO  ↓
Step 2: LLMIntentParser.parse() (DeepSeek)
    ↓
  意图 != unsupported 且置信度 >= 0.70？
    YES → 返回，source="llm"，合并规则参数
    NO  ↓
Step 3: Fallback 到规则结果
    → 返回，source="hybrid"
```

### 7.2 关键阈值配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `RULE_CONFIDENCE_THRESHOLD` | 0.85 | 规则 parser 可直接采用的置信度 |
| `LLM_CONFIDENCE_THRESHOLD` | 0.70 | LLM 结果采纳的最低置信度 |
| `FINAL_CONFIDENCE_THRESHOLD` | 0.70 | `parse_with_threshold()` 的最低置信度 |
| `MAJOR_MISSING_PARAMS_LIMIT` | 2 | 严重参数缺失判定 |

### 7.3 参数合并策略

LLM 结果与规则结果合并时：规则提取的参数优先（不覆盖），LLM 提取的参数补充（不覆盖规则结果）。

---

## 八、Agent Orchestrator 当前调用链

### 8.1 完整数据流

```
前端 ChatInput 组件
  │  handleSubmit() → agentQuery({query, project_id, context, auto_run})
  │
  ▼
POST /api/ai/agent  (api/ai_jobs.py L331)
  │  AgentQueryRequest: {query, project_id, context, auto_run}
  │
  ▼
AgentOrchestrator.process(query, context, auto_run=True)  (agent_orchestrator.py L156)
  │
  ├─ 1. HybridIntentParser.parse(query)  (hybrid_intent_parser.py L42)
  │   ├─ 1a. RuleBasedIntentParser.parse(query)  (intent_parser.py L215)
  │   │   └─ 返回 IntentParseResult (source="rule"/"hybrid")
  │   ├─ 1b. [如果规则弱] LLMIntentParser.parse(query)  (deepseek_intent_parser.py L132)
  │   │   └─ LLMService.call_llm_json() → DeepSeekProvider.chat_json()
  │   │   └─ 返回 IntentParseResult (source="llm")
  │   └─ 1c. [如果 LLM 也失败] fallback 规则结果 (source="hybrid")
  │
  ├─ 2. intent 判定
  │   ├─ "unsupported" → _make_unsupported()
  │   ├─ "job_status" / "chat" → _handle_query_status()
  │   └─ 其他 → 继续
  │
  ├─ 3. 参数补全 _enrich_params()
  │   ├─ 从 context 预填 (project_id, exposure, outcome, file_id, mediator_source)
  │   └─ 默认值注入 (covariates, methods, model_types, grouping)
  │
  ├─ 4. 参数校验
  │   ├─ PARAM_HINTS 必填字段检查
  │   └─ 缺失 → _make_need_more_info()
  │
  ├─ 5. 创建 Job _create_and_run_job()
  │   ├─ 5a. Skill.validate_input(params) 二次校验 ← 已在代码中实现
  │   ├─ 5b. job_manager.create_job(capability_type, input_data, project_id)
  │   └─ 5c. job_manager.run_job(job_id)
  │       └─ 后台线程 _execute_job()
  │           ├─ skill_registry.get()
  │           ├─ skill.validate_input()  ← JobManager 也独立校验
  │           └─ skill.run(input, context) → SkillOutput
  │
  └─ 6. 返回 OrchestratorResult → JSON Response → ChatInput 渲染
```

### 8.2 调用链简图

```
ChatInput → POST /api/ai/agent → AgentOrchestrator
  → HybridIntentParser
    → RuleBasedIntentParser (优先)
    → LLMIntentParser → LLMService → DeepSeekProvider (LLM 增强)
    → Fallback rule result (兜底)
  → PARAM_HINTS 检查 + 参数补全
  → Skill.validate_input 二次校验
  → JobManager.create_job() + run_job()
    → SkillRegistry.get() → Skill.run() → SkillOutput
  → OrchestratorResult → Frontend ChatInput
```

### 8.3 两种 Job 创建路径（并存）

| 路径 | API | 入口 |
|------|-----|------|
| **新路径（Agent）** | `POST /api/ai/agent` | ChatInput 自然语言 → AgentOrchestrator → JobManager |
| **新路径（直接）** | `POST /api/ai/{capability}/jobs` | 前端直接指定 capability → JobManager |
| **旧路径** | `POST /api/v1/tasks` | 旧 TaskOrchestrator → SkillRunner registry → subprocess |

---

## 九、发现的问题

### 9.1 阻塞性问题

1. **无 `.env` 文件**
   - 位置：项目根目录仅有 `.env.example`，无 `.env`
   - 影响：DeepSeek 无法启用，`DEEPSEEK_API_KEY` 为空
   - 影响：`DeepSeekProvider` 初始化失败（被 `ai/llm/__init__.py` 静默捕获）
   - 解决：`cp .env.example .env` 并填写 `DEEPSEEK_API_KEY`

### 9.2 架构问题

1. **两套 Adapter 体系并存**
   - 旧体系：`backend/app/tasks/` — `BaseSkillRunner` + 7 个 Runner 类 + subprocess 调用
   - 新体系：`backend/app/ai/skills/` — `Skill(ABC)` + 7 个 Skill 类 + mock 内联实现
   - 影响：旧的任务执行路径（`POST /api/v1/tasks`）仍可用，但和新的 AI Job 体系独立运行
   - 建议：确认是否需废弃旧体系

2. **Skill mode 硬编码**
   - 所有 7 个 Skill 的 `mode` 属性硬编码返回 `"mock"`
   - `config.py` 中有 `get_skill_mode()` 函数和 `AI_MODE_PER_SKILL` 环境变量支持，但未被 Skill 使用
   - 每个 Skill 还保留 `_run_real()` 方法，但始终返回 `NOT_IMPLEMENTED`

3. **前端分析模块仍用硬编码数据**
   - `ImageProcessingModule`、`GWASModule`、`MRModule`、`MediationMRModule` 中图表的 mock 数据在前端硬编码
   - 虽然 ChatInput 组件已经正确对接了 Agent API，但手动操作模块仍用旧数据

### 9.3 功能缺口

1. **LLM 功能模块未实现**
   - `result_interpreter.py` — 未创建（分析结果 → 自然语言解读）
   - `error_explainer.py` — 未创建（错误码 → 友好解释）
   - `report_enhancer.py` — 未创建（LLM 增强报告章节）
   - `chat_responder.py` — 未创建（通用对话回复）

2. **流式输出未实现**
   - `DeepSeekProvider.stream_chat()` 抛出 `NotImplementedError`
   - ChatInput 没有流式展示逻辑

3. **JobStore 无持久化**
   - 当前 `InMemoryJobStore`，重启后端丢失所有 Job

4. **`/api/ai/llm/health` 路由前缀**
   - 实际挂载在 `/api/ai/llm/health`（`ai_jobs.py` router 的 prefix 是 `/api/ai`）
   - README.md 和项目描述中写的是 `/api/llm/health`，实际是 `/api/ai/llm/health`

### 9.4 代码质量问题

1. **旧测试脚本使用 print 而非 pytest**
   - `test_intent_parser.py` 使用 `print()` 断言，无 pytest fixture
   - `test_error_handling.py` 使用全局变量 `passed/failed`
   - `test_agent_orchestrator.py` 正确使用 pytest（16 个测试函数）

2. **`ai/llm/__init__.py` 中的静默异常**
   - `DeepSeekProvider()` 注册失败被静默吞掉（`except ValueError: pass`）
   - 无日志输出，调试困难

---

## 十、下一步建议

### 10.1 立即行动（启动 DeepSeek）

1. 创建 `.env` 文件：`cp .env.example .env`
2. 填写 `DEEPSEEK_API_KEY`，设置 `LLM_PROVIDER=deepseek`
3. 重启后端，验证 `GET /api/ai/llm/health` 返回 `reachable: true`
4. 测试 `POST /api/ai/agent` 验证 HybridIntentParser 的 LLM 路径生效

### 10.2 短期目标（完成 AI 接入闭环）

1. **前端数据绑定**：将 4 个分析模块的硬编码数据改为从 `resultStore` 读取
2. **文件上传对接**：将分析模块中的 `<input type="file">` 绑定到 `aiService.uploadMedicalImage()`
3. **LLM Result Interpreter**：新建 `ai/llm/result_interpreter.py`，实现分析结果解读
4. **LLM Report Enhancer**：在 `report_generation._run_real()` 中接入 DeepSeek 生成讨论/结论

### 10.3 中期目标（完善体验）

1. **JobStore 持久化**：实现基于 SQLite 的 JobStore
2. **流式输出**：实现 `DeepSeekProvider.stream_chat()` 和前端 SSE 接收
3. **对话历史**：ChatInput 增加对话历史状态管理和 local storage 持久化
4. **Error Explainer**：LLM 驱动的错误解释

### 10.4 决策点

1. **旧 Task 体系是否保留**：确认是废弃 `backend/app/tasks/` + `backend/app/services/task_orchestrator.py`，还是两者长期并存
2. **Skill mode 从环境变量读取**：将 `config.get_skill_mode()` 集成到各 Skill 的 `mode` 属性
3. **前端架构选择**：是否在 ChatInput 之外保留手动操作模块，还是全部改为 Agent 对话驱动

---

## 十一、结论

**当前可以继续执行后续 AI 接入任务**，但需要先完成以下前置条件：

1. **必须**：创建 `.env` 文件并配置 `DEEPSEEK_API_KEY`（DeepSeek 接入的基础前提）
2. **必须**：确认旧 Task 体系（`backend/app/tasks/`）是否保留（影响后续工作范围）
3. **建议**：将前端分析模块数据绑定作为下一优先任务（用户在 UI 上看到真实数据是价值感知的关键）

所有核心 AI 模块已完整实现并相互连接：
- Skill Registry → Job Manager → Agent Orchestrator → Hybrid Intent Parser 全链路已就绪
- DeepSeek Provider 代码完整，只缺 `.env` 中的 API Key
- 前端 ChatInput 已对接 Agent API，4 种 answerType 展示完备
- 7 个 Mock Skill 均可正常运行并返回结构化数据
- 测试覆盖 AgentOrchestrator、IntentParser、ErrorHandling
