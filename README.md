# AdipoInsight

医学科研 AI 分析平台 — Mock-First MVP

## 快速启动

在项目目录下运行命令行窗口
### 后端

```bash
cd backend
python -m venv .venv
Windows: .venv\Scripts\activate   # Linux:source .venv/bin/activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --port 8000
```

### 前端
在项目目录下新运行一个命令行窗口
```bash
cd frontend
npm install
npm run dev
```

### 网址
打开 http://localhost:5173


## 技术栈

- 后端: FastAPI + SQLAlchemy + SQLite
- 前端: Vite + React + TypeScript + Tailwind CSS + Zustand
- 分析: Python mock CLI scripts

## 文档

- [架构设计](docs/architecture.md)
- [API 文档](docs/api.md)
- [Mock Skills](docs/mock_skills.md)
- [真实模块替换](docs/real_module_replacement.md)
