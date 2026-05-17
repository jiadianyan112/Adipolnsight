from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.database import init_db
import backend.app.ai.skills  # noqa: F401 — 触发 Skill 注册
from backend.app.api import projects, files, tasks, results, reports, demo, ai_jobs
from backend.app.errors import AdipoInsightError, make_error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AdipoInsight", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 统一异常处理 =====

@app.exception_handler(AdipoInsightError)
async def adipoinsight_error_handler(request: Request, exc: AdipoInsightError):
    return JSONResponse(
        status_code=exc.http_status,
        content=make_error_response(exc.code, exc.message, exc.details),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=make_error_response(
            "INTERNAL_ERROR",
            f"{type(exc).__name__}: {str(exc)}",
        ),
    )

# ===== Routers =====

app.include_router(projects.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(ai_jobs.router)  # /api/ai/* prefix is set in the router itself


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "0.2.0"}
