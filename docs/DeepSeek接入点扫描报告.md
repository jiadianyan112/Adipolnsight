# DeepSeek 接入点扫描报告

> 扫描日期：2026-05-17
> 扫描范围：全项目（backend + frontend）
> 原则：不删除、不重构，只在空白处增加

---

## 一、10 个关键位置扫描结果

### 1. AI Job Manager

| 项目 | 内容 |
|------|------|
| 路径 | `backend/app/ai/job_manager.py` |
| 核心类 | `JobManager` (单例 `job_manager`) |
| 关键方法 | `create_job()`, `run_job()`, `get_job()`, `get_result()`, `cancel_job()` |
| 依赖 | `SkillRegistry`, `JobStore` (InMemoryJobStore) |
| 对接 DeepSeek | **不改** — JobManager 只管任务生命周期，不管 LLM |

### 2. AI Skill Registry

| 项目 | 内容 |
|------|------|
| 路径 | `backend/app/ai/registry.py` |
| 核心类 | `SkillRegistry` (单例 `registry`) |
| 关键方法 | `register()`, `get()`, `dispatch()`, `list_all()` |
| 依赖 | `Skill` ABC (base.py) |
| 对接 DeepSeek | **不改** — 只注册 skill，不注册 LLM |

### 3. Agent Orchestrator

| 项目 | 内容 |
|------|------|
| 路径 | `backend/app/ai/agent_orchestrator.py` |
| 核心类 | `AgentOrchestrator` (单例 `agent_orchestrator`) |
| 关键方法 | `process(query, context, auto_run)` → `OrchestratorResult` |
| 当前 Intent Parser | 硬编码 import `IntentParser` (rule-based) |
| 对接 DeepSeek | **需改造** — 将 `intent_parser` 替换为 `HybridIntentParser` |

### 4. Rule-Based Intent Parser

| 项目 | 内容 |
|------|------|
| 路径 | `backend/app/ai/intent_parser.py` |
| 核心类 | `IntentParser` (单例 `intent_parser`) |
| 输出结构 | `IntentResult` (intent, confidence, capability_type, extracted_params, missing_params, clarification_needed) |
| 依赖 | `INTENT_PATTERNS` (9 个规则) |
| 对接 DeepSeek | **不改** — 保留作为 fallback，新 HybridParser 包装它 |

### 5. Report Generation Skill

| 项目 | 内容 |
|------|------|
| 路径 | `backend/app/ai/skills/report_generation.py` |
| 核心类 | `ReportGenerationSkill` |
| Mock 实现 | `_run_mock()` — 模板生成 9 个章节 |
| Real 预留 | `_run_real()` — 空实现，已预留 LLM 接口注释 |
| 对接 DeepSeek | **需改造** — 在 `_run_real()` 中接入 DeepSeek 生成讨论/结论 |

### 6. 前端 AI 助手/聊天框

| 项目 | 内容 |
|------|------|
| 路径 | `frontend/src/components/agent/ChatInput.tsx` |
| 组件 | `ChatInput` — 输入框 + 4 种 answerType 展示 |
| API | 调用 `agentQuery()` → `POST /api/ai/agent` |
| 对接 DeepSeek | **轻改造** — 增加对话消息气泡展示、流式输出预留 |

### 7. API 路由目录

| 项目 | 内容 |
|------|------|
| 路径 | `backend/app/api/` |
| AI 路由 | `ai_jobs.py` — POST `/api/ai/agent`, POST `/api/ai/{cap}/jobs`, GET `/api/ai/jobs/{id}` 等 |
| 注册位置 | `backend/app/main.py` L31 |
| 对接 DeepSeek | **轻改造** — agent 路由已存在，需扩展支持 chat 模式 |

### 8. Types/Interfaces 目录

| 项目 | 前端 | 后端 |
|------|------|------|
| 路径 | `frontend/src/types/` | `backend/app/schemas/` |
| AI 类型 | `ai.ts`, `job.ts`, `segmentation.ts`, `analysis.ts` | `ai.py`, `task.py`, `result.py`, `report.py` |
| 报告类型 | `ReportGenerationRequest/Result`, `ReportSection/Figure/Table/Reference` | 同名 Pydantic models |
| 对接 DeepSeek | **增补** — 新增 `ChatMessage`, `LLMIntentResult`, `LLMExplanation` 等类型 |

### 9. 环境变量

| 项目 | 内容 |
|------|------|
| 模板文件 | `.env.example` |
| 实际配置 | `backend/app/config.py` |
| LLM 变量 | `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` (已预留) |
| 其他预留 | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `LLM_LOCAL_URL` |
| 对接 DeepSeek | **增补** — 添加 `DEEPSEEK_API_KEY`, `DEEPSEEK_API_BASE`, `DEEPSEEK_MODEL` |

### 10. 测试目录与测试框架

| 项目 | 内容 |
|------|------|
| 测试文件 | `backend/app/ai/test_intent_parser.py`, `test_agent_orchestrator.py`, `test_error_handling.py` |
| 测试风格 | 纯 Python assert，无 pytest/unittest 依赖 |
| 前端测试 | 无独立 test 文件（通过 tsc --noEmit 验证） |
| 对接 DeepSeek | **新增** — `backend/app/ai/llm/tests/` 目录 |

---

## 二、现有架构关键接口签名

### IntentParser.parse() → IntentResult
```python
# backend/app/ai/intent_parser.py
def parse(text: str) -> IntentResult:
    # 返回: intent, confidence, capability_type, extracted_params, missing_params, clarification_needed

# 单例: intent_parser = IntentParser()
```

### AgentOrchestrator.process() → OrchestratorResult
```python
# backend/app/ai/agent_orchestrator.py
def process(query: str, context: dict, auto_run: bool = True) -> OrchestratorResult:
    # 1. intent_parser.parse(query)
    # 2. 参数补全
    # 3. job_manager.create_job() + run_job()
    # 返回: answer_type, message, capability_type, job_id, extracted_params, missing_params, next_actions

# 单例: agent_orchestrator = AgentOrchestrator()
```

### ReportGenerationSkill._run_real() — 预留接口
```python
# backend/app/ai/skills/report_generation.py
def _run_real(self, input_data, context) -> SkillOutput:
    # 当前: return SkillOutput(status="failed", error_code="NOT_IMPLEMENTED")
    # 预留: LLM 生成讨论段落
```

### ChatInput 组件 Props
```typescript
// frontend/src/components/agent/ChatInput.tsx
interface Props {
  projectId: number;
  context?: Record<string, unknown>;
  className?: string;
}
```

### Agent API 请求/响应结构
```typescript
// frontend/src/services/aiService.ts
agentQuery({ query, project_id, context, auto_run }) → AgentQueryResponse {
  answer_type, message, capability_type, job_id,
  extracted_params, missing_params, clarification_question,
  next_actions: [{ label, action, params }]
}
```

---

## 三、推荐新增目录结构

```
backend/app/ai/llm/                          # ★ 新增 LLM 子模块
├── __init__.py                              # 导出所有 LLM 组件
├── provider.py                              # DeepSeek API 封装（兼容 OpenAI SDK）
├── schemas.py                               # LLM 输出 JSON Schema (Pydantic)
├── deepseek_intent_parser.py               # DeepSeek Intent Parser
├── hybrid_intent_parser.py                  # DeepSeek + rule + fallback
├── result_interpreter.py                    # 分析结果 → 自然语言解读
├── error_explainer.py                       # 错误码 → 友好解释
├── report_enhancer.py                       # LLM 增强报告生成（供 report skill 调用）
├── chat_responder.py                        # 通用对话回复
└── tests/                                   # LLM 模块测试
    ├── __init__.py
    ├── test_provider.py
    ├── test_hybrid_parser.py
    ├── test_result_interpreter.py
    ├── test_error_explainer.py
    └── test_schemas.py
```

---

## 四、需要修改的文件（按优先级）

| 优先级 | 文件 | 改动类型 | 改动量 |
|--------|------|---------|--------|
| P0 | `backend/app/ai/llm/provider.py` | **新增** | DeepSeek API 封装 |
| P0 | `backend/app/ai/llm/schemas.py` | **新增** | LLM 输出 Schema 定义 |
| P1 | `backend/app/ai/llm/deepseek_intent_parser.py` | **新增** | LLM 意图解析 |
| P1 | `backend/app/ai/llm/hybrid_intent_parser.py` | **新增** | Hybrid Parser |
| P2 | `backend/app/ai/agent_orchestrator.py` | **修改** | L28: 替换 intent_parser 为 hybrid |
| P2 | `backend/app/ai/llm/result_interpreter.py` | **新增** | 结果解释 |
| P2 | `backend/app/ai/llm/error_explainer.py` | **新增** | 错误解释 |
| P3 | `backend/app/ai/llm/report_enhancer.py` | **新增** | 报告增强 |
| P3 | `backend/app/ai/skills/report_generation.py` | **修改** | `_run_real` 调用 report_enhancer |
| P3 | `backend/app/ai/llm/chat_responder.py` | **新增** | 对话回复 |
| P3 | `backend/app/api/ai_jobs.py` | **修改** | agent 路由扩展 chat 模式 |
| P3 | `frontend/src/components/agent/ChatInput.tsx` | **修改** | 对话气泡 + 流式预留 |
| P3 | `backend/app/config.py` | **修改** | +`DEEPSEEK_API_KEY/BASE/MODEL` |
| P3 | `.env.example` | **修改** | +DeepSeek 环境变量 |
| P4 | `frontend/src/types/ai.ts` | **修改** | +ChatMessage 等类型 |
| P4 | `backend/app/schemas/ai.py` | **修改** | +LLM 相关 schema |

---

## 五、禁止修改的文件

| 文件 | 原因 |
|------|------|
| `backend/app/ai/intent_parser.py` | Rule parser 必须保留作为 fallback |
| `backend/app/ai/registry.py` | Skill 注册机制不变 |
| `backend/app/ai/job_manager.py` | 任务管理不变 |
| `backend/app/ai/base.py` | Skill 基类不变 |
| `backend/app/ai/skills/image_segmentation.py` | 分割 skill 不变 |
| `backend/app/ai/skills/gwas_analysis.py` | GWAS skill 不变 |
| `backend/app/ai/skills/two_sample_mr.py` | MR skill 不变 |
| `backend/app/ai/skills/mediation_mr.py` | 中介 MR skill 不变 |
| `backend/app/ai/skills/risk_modeling.py` | 风险建模 skill 不变 |
| `backend/app/ai/skills/phenotype_quantification.py` | 表型量化 skill 不变 |
| `backend/app/errors.py` | 错误体系不变（可增补 1 个 LLM 错误码） |
| `frontend/src/components/analysis/*.tsx` | 5 个分析模块 UI 不变 |
| `frontend/src/pages/ProjectWorkspacePage.tsx` | 工作区布局不变（ChatInput 挂载位置不变） |

---

## 六、应尽量少改的文件（≤ 5 行改动）

| 文件 | 最大改动 | 说明 |
|------|---------|------|
| `backend/app/ai/agent_orchestrator.py` | 1 行 | 替换 `intent_parser` → `hybrid_intent_parser` |
| `backend/app/config.py` | 3 行 | +`DEEPSEEK_API_KEY/BASE/MODEL` |
| `.env.example` | 5 行 | +DeepSeek 配置段 |
| `backend/app/api/ai_jobs.py` | 15 行 | agent 路由增加 chat 模式分支 |
| `frontend/src/components/agent/ChatInput.tsx` | 30 行 | 对话气泡展示 |
| `backend/app/errors.py` | 1 行 | +`LLM_SERVICE_ERROR` |

---

## 七、关键数据流（DeepSeek 接入后）

```
用户输入
  → ChatInput (前端, 不变)
    → POST /api/ai/agent (后端路由, 轻改造)
      → AgentOrchestrator.process() (改 1 行)
        → HybridIntentParser.parse() (新增)
          ├── DeepSeekIntentParser.parse() (新增, 优先)
          │   └── provider.chat() → DeepSeek API
          │       ├── 成功 → schema validate → IntentResult
          │       └── 失败 ↓
          └── IntentParser.parse() (不变, fallback)
        → (意图识别后流程不变)
          → SkillRegistry.dispatch()
          → JobManager.create_job() + run_job()

结果展示 (新增 3 个 LLM 能力):
  - ResultInterpreter.explain(result) → 自然语言解读
  - ErrorExplainer.explain(error_code) → 友好错误解释
  - ReportEnhancer.enhance(sections) → LLM 讨论章节
```

---

## 八、环境变量补充建议

```bash
# .env.example 新增
DEEPSEEK_API_KEY=           # DeepSeek API 密钥
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_TEMPERATURE=0.1        # 意图解析用低温
LLM_REPORT_TEMPERATURE=0.3 # 报告生成用中温
LLM_CHAT_TEMPERATURE=0.5   # 聊天用高温
```

---

## 九、风险点

| 风险 | 缓解措施 |
|------|---------|
| DeepSeek API 不可用 | HybridParser 自动 fallback 到 rule parser |
| JSON 输出格式错误 | Pydantic schema validate + retry + fallback |
| API KEY 泄露 | 仅后端读取环境变量，前端零接触 |
| LLM 生成不安全的操作指令 | system prompt 约束 + 仅返回文本/JSON |
| 报告生成质量差 | mock template 作为 fallback |
| 对话响应慢 | 非流式先实现，预留 SSE 接口 |
