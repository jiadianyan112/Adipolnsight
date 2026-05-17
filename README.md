# AdipoInsight

医学科研 AI 分析平台 — Mock-First MVP

## 快速启动

```bash
# 1. 克隆项目
git clone <repo-url> && cd AdipoInsight

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少确认 AI_MODE=mock

# 3. 启动后端
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --port 8000

# 4. 启动前端（新终端窗口）
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173

### 切换为 DeepSeek

```bash
# 编辑 .env 文件
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key-here   # 替换为实际 Key
DEEPSEEK_MODEL=deepseek-v4-flash
```

> **安全警告**: `DEEPSEEK_API_KEY` 只能在后端环境变量中配置，绝对不能进入前端环境变量或提交到 Git。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AI_MODE` | `mock` | AI 运行模式：mock / script / api / model |
| `AI_MODE_PER_SKILL` | — | 各能力单独模式 |
| `LLM_PROVIDER` | `mock` | LLM 提供商：mock / deepseek / openai |
| `DEEPSEEK_API_KEY` | — | DeepSeek API Key（仅后端，不暴露前端） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek API 地址 |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | DeepSeek 默认模型 |
| `DEEPSEEK_REASONING_MODEL` | `deepseek-v4-pro` | DeepSeek 推理模型 |
| `LLM_TIMEOUT_MS` | `60000` | LLM 超时（毫秒） |
| `LLM_MAX_RETRIES` | `2` | LLM 最大重试次数 |
| `LLM_MAX_TOKENS` | `4096` | LLM 最大输出 token |
| `LLM_JSON_TEMPERATURE` | `0.2` | JSON 结构化输出温度 |
| `LLM_TEXT_TEMPERATURE` | `0.4` | 文本生成温度 |
| `MAX_UPLOAD_SIZE` | `209715200` | 最大上传文件大小（200MB） |
| `OPENGWAS_API_BASE` | `https://gwas-api.mrcieu.ac.uk` | OpenGWAS API 地址 |
| `API_PORT` | `8000` | 后端端口 |
| `FRONTEND_PORT` | `5173` | 前端端口 |

完整环境变量列表见 `.env.example`。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vite + React 19 + TypeScript + Tailwind CSS 4 + Zustand
- **AI 能力**: 7 个 Mock Skill Adapter（可替换为真实模型/脚本/API）
- **任务系统**: JobManager + SkillRegistry + Agent Orchestrator

## AI 能力

| # | 能力 | 模式 | 说明 |
|---|------|------|------|
| C1 | MRI 影像分割 | mock | TSSA-UNet 多器官分割 |
| C2 | 脂肪表型量化 | mock | 9 项定量指标提取 |
| C3 | GWAS 分析 | mock | REGENIE 全基因组关联 |
| C4 | 双样本 MR | mock | IVW/MR-Egger/Weighted Median |
| C5 | 中介 MR | mock | deCODE pQTL 两步法 |
| C6 | 风险建模 | mock | OLS + RCS + Logistic |
| C7 | 报告生成 | mock | 结构化科研报告 |

## 项目结构

```
AdipoInsight/
├── frontend/                # React 前端
│   └── src/
│       ├── components/      # analysis/result/task/agent/shared
│       ├── pages/           # 4 个页面
│       ├── services/        # apiClient + aiService
│       ├── stores/          # Zustand stores
│       └── types/           # TypeScript 类型
├── backend/app/
│   ├── ai/                  # AI 核心模块
│   │   ├── skills/          # 7 个 Skill Adapter
│   │   ├── intent_parser.py # 意图识别
│   │   ├── agent_orchestrator.py # Agent 编排
│   │   ├── job_manager.py   # 任务管理
│   │   └── registry.py      # Skill 注册表
│   ├── api/                 # FastAPI 路由
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 校验
│   └── services/            # 业务服务
├── analysis_scripts/        # Mock 分析脚本
├── docs/                    # 文档
│   ├── AI_Integration_Architecture.md
│   ├── AI_Capability_Map.md
│   ├── API_CONTRACT_AI.md
│   └── api.md
├── storage/                 # 上传文件 + 分析输出
├── .env.example             # 环境变量模板
└── README.md
```

## 文档

- [架构设计](docs/architecture.md)
- [API 文档](docs/api.md)
- [AI 接入架构](docs/AI_Integration_Architecture.md)
- [AI 能力清单](docs/AI_Capability_Map.md)
- [AI API 契约](docs/API_CONTRACT_AI.md)
- [Mock Skills](docs/mock_skills.md)
- [真实模块替换](docs/real_module_replacement.md)

## API 端点

### REST API (/api/v1/*)

| Method | Path | 说明 |
|--------|------|------|
| POST | /projects | 创建项目 |
| GET | /projects | 项目列表 |
| POST | /projects/{id}/files | 上传文件 |
| POST | /tasks | 创建任务 (旧) |
| GET | /tasks/{id}/result | 任务结果 |

### AI API (/api/ai/*)

| Method | Path | 说明 |
|--------|------|------|
| POST | /ai/{capability}/jobs | 创建 AI Job |
| GET | /ai/jobs/{id} | 查询状态 |
| GET | /ai/jobs/{id}/result | 获取结果 |
| POST | /ai/jobs/{id}/cancel | 取消任务 |
| POST | /ai/agent | AI Agent 自然语言交互 |
| GET | /ai/capabilities | 列出所有能力 |
| GET | /ai/llm/health | LLM 健康检查 |

### 测试 LLM 健康

```bash
# mock 模式（默认）
curl http://localhost:8000/api/ai/llm/health
# → {"success":true, "data":{"provider":"mock","reachable":true}}

# deepseek 模式（需先设置 DEEPSEEK_API_KEY）
curl http://localhost:8000/api/ai/llm/health
# → {"success":true, "data":{"provider":"deepseek","reachable":true,"latencyMs":1234}}
```
