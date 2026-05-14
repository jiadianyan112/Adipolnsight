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
