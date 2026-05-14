from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database import init_db
from backend.app.api import projects, files, tasks, results, reports, demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AdipoInsight", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
