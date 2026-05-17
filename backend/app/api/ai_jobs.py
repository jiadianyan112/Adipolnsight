"""
AI Job API Router — /api/ai/*

实现 AI 能力的异步任务接口：
- POST   /api/ai/{capability}/jobs     创建并启动 Job
- GET    /api/ai/jobs/{job_id}         查询 Job 状态（前端轮询）
- GET    /api/ai/jobs/{job_id}/result  获取 Job 结果
- POST   /api/ai/jobs/{job_id}/cancel  取消 Job
"""

import logging
import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException, Path, Body

from backend.app.ai import job_manager, registry
from backend.app.schemas.ai import (
    URL_CAPABILITY_MAP,
    VALID_URL_CAPABILITIES,
    CreateJobRequest,
    JobStatusResponse,
    JobResultResponse,
    CancelJobResponse,
    ApiResponse,
    ApiError,
)

logger = logging.getLogger("adipoinsight.ai_api")

router = APIRouter(prefix="/api/ai", tags=["AI Jobs"])


# ===== 辅助 =====

def _make_response(success: bool, data: dict = None, error: ApiError = None) -> dict:
    """构造统一 response envelope"""
    return {
        "success": success,
        "data": data,
        "error": error.model_dump() if error else None,
        "request_id": str(uuid.uuid4())[:8],
    }


def _capability_from_path(capability: str) -> str:
    """URL path capability → 内部 task_type"""
    task_type = URL_CAPABILITY_MAP.get(capability)
    if task_type is None:
        valid = list(URL_CAPABILITY_MAP.keys())
        raise HTTPException(
            status_code=400,
            detail=_make_response(
                success=False,
                error=ApiError(
                    code="INVALID_PARAMETER",
                    message=f"Unknown capability '{capability}'. Valid: {valid}",
                ),
            ),
        )
    return task_type


# =====================================================================
# POST /api/ai/{capability}/jobs
# =====================================================================

@router.post("/{capability}/jobs", status_code=201)
def create_ai_job(
    capability: VALID_URL_CAPABILITIES = Path(..., description="AI 能力名称"),
    body: CreateJobRequest = Body(...),
):
    """
    创建并启动一个 AI Job。

    URL path capability 映射到内部 task_type 后，通过 JobManager
    创建 Job、启动后台线程执行，立即返回 Job 状态。
    """
    task_type = _capability_from_path(capability)

    # 校验 Skill 已注册
    if not registry.has(task_type):
        return _make_response(
            success=False,
            error=ApiError(
                code="ADAPTER_NOT_FOUND",
                message=f"No skill registered for '{task_type}'",
            ),
        )

    logger.info(
        "[AI API] Create job: capability=%s task_type=%s project_id=%s params=%s",
        capability, task_type, body.project_id, list(body.parameters.keys()),
    )

    # 合并 project_id 到 parameters
    input_data = {**body.parameters, "project_id": body.project_id}

    # 创建 Job
    try:
        job = job_manager.create_job(
            capability_type=task_type,
            input_data=input_data,
            project_id=body.project_id,
        )
    except ValueError as exc:
        return _make_response(
            success=False,
            error=ApiError(code="INVALID_PARAMETER", message=str(exc)),
        )

    # 启动后台执行
    started = job_manager.run_job(job.job_id)
    if not started:
        return _make_response(
            success=False,
            error=ApiError(
                code="INTERNAL_ERROR",
                message=f"Failed to start job {job.job_id}",
            ),
        )

    logger.info(
        "[AI API] Job started: job_id=%s capability=%s",
        job.job_id, task_type,
    )

    return _make_response(
        success=True,
        data={
            "job_id": job.job_id,
            "capability_type": job.capability_type,
            "status": job.status,
            "progress": job.progress,
            "progress_stage": job.progress_stage,
            "input": job.input,
            "created_at": job.created_at,
            "project_id": job.project_id,
        },
    )


# =====================================================================
# GET /api/ai/jobs/{job_id}
# =====================================================================

@router.get("/jobs/{job_id}")
def get_ai_job_status(
    job_id: str = Path(..., min_length=1, max_length=64, description="Job ID"),
):
    """
    查询 Job 当前状态与进度。

    前端通过轮询此接口获取进度更新。
    返回字段与前端 types/job.ts 中的 AIJob 对齐。
    """
    logger.debug("[AI API] Get job status: job_id=%s", job_id)

    status = job_manager.get_job_status(job_id)
    if status is None:
        return _make_response(
            success=False,
            error=ApiError(
                code="JOB_NOT_FOUND",
                message=f"Job '{job_id}' not found",
            ),
        )

    return _make_response(success=True, data=status)


# =====================================================================
# GET /api/ai/jobs/{job_id}/result
# =====================================================================

@router.get("/jobs/{job_id}/result")
def get_ai_job_result(
    job_id: str = Path(..., min_length=1, max_length=64, description="Job ID"),
):
    """
    获取 Job 执行结果。

    仅在 Job status=succeeded 时返回完整 result。
    如果 Job 仍在运行中，返回 404 + RESULT_NOT_FOUND。
    """
    logger.debug("[AI API] Get job result: job_id=%s", job_id)

    job = job_manager.get_job(job_id)
    if job is None:
        return _make_response(
            success=False,
            error=ApiError(
                code="JOB_NOT_FOUND",
                message=f"Job '{job_id}' not found",
            ),
        )

    if job.status == "queued" or job.status == "running":
        return _make_response(
            success=False,
            error=ApiError(
                code="RESULT_NOT_FOUND",
                message=f"Job '{job_id}' is still {job.status}. Result not yet available.",
                details={"job_id": job_id, "current_status": job.status},
            ),
        )

    if job.status == "failed":
        return _make_response(
            success=False,
            error=ApiError(
                code=job.error_code or "SKILL_EXECUTION_ERROR",
                message=job.error_message or "Job execution failed",
                details={"job_id": job_id},
            ),
        )

    if job.status == "cancelled":
        return _make_response(
            success=False,
            error=ApiError(
                code="JOB_ALREADY_CANCELLED",
                message=f"Job '{job_id}' was cancelled",
                details={"job_id": job_id},
            ),
        )

    result = job_manager.get_result(job_id)
    if result is None:
        return _make_response(
            success=False,
            error=ApiError(
                code="RESULT_NOT_FOUND",
                message=f"Result for job '{job_id}' is empty",
            ),
        )

    logger.info("[AI API] Result returned: job_id=%s capability=%s summary_keys=%s",
                job_id, job.capability_type,
                list(result.get("result", {}).keys()) if result.get("result") else [])

    return _make_response(success=True, data=result)


# =====================================================================
# POST /api/ai/jobs/{job_id}/cancel
# =====================================================================

@router.post("/jobs/{job_id}/cancel")
def cancel_ai_job(
    job_id: str = Path(..., min_length=1, max_length=64, description="Job ID"),
):
    """
    取消一个 queued 或 running 的 Job。

    取消操作是异步的——对于 running 的 Job，取消在下一个检查点生效。
    已处于终态（succeeded/failed/cancelled）的 Job 无法取消。
    """
    logger.info("[AI API] Cancel job: job_id=%s", job_id)

    job = job_manager.get_job(job_id)
    if job is None:
        return _make_response(
            success=False,
            error=ApiError(
                code="JOB_NOT_FOUND",
                message=f"Job '{job_id}' not found",
            ),
        )

    if job.status in ("succeeded", "failed", "cancelled"):
        return _make_response(
            success=False,
            error=ApiError(
                code="JOB_ALREADY_CANCELLED" if job.status == "cancelled" else "INVALID_PARAMETER",
                message=f"Job '{job_id}' is already in terminal state: {job.status}",
                details={"job_id": job_id, "current_status": job.status},
            ),
        )

    ok = job_manager.cancel_job(job_id)
    if not ok:
        return _make_response(
            success=False,
            error=ApiError(
                code="INTERNAL_ERROR",
                message=f"Failed to cancel job '{job_id}'",
            ),
        )

    job = job_manager.get_job(job_id)
    return _make_response(
        success=True,
        data={
            "job_id": job.job_id,
            "capability_type": job.capability_type,
            "status": job.status,
            "message": "Job cancelled successfully",
        },
    )


# =====================================================================
# 辅助：列出已注册能力
# =====================================================================

@router.get("/capabilities")
def list_capabilities():
    """列出所有已注册的 AI 能力及其元信息"""
    return _make_response(
        success=True,
        data={"capabilities": registry.list_all()},
    )


# =====================================================================
# POST /api/ai/agent — AI Agent 自然语言入口
# =====================================================================

from typing import Any, Dict as DictType
from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="用户自然语言输入")
    project_id: int = Field(default=0, ge=0, description="当前项目 ID")
    context: DictType[str, Any] = Field(default_factory=dict, description="额外上下文（exposure, outcome 等）")
    auto_run: bool = Field(default=True, description="参数齐全时是否自动创建并运行 Job")


@router.post("/agent")
def agent_query(body: AgentQueryRequest):
    """
    AI Agent 自然语言交互入口。

    接收用户自然语言 query + 项目上下文，通过 Agent Orchestrator
    完成「意图识别 → 参数补全 → 任务创建」全链路。

    返回 answerType 告知前端应如何展示：
    - job_created:     参数齐全，任务已创建，前端展示进度卡片
    - need_more_info:  参数不足，前端展示缺失字段表单
    - unsupported:     意图无法识别，前端展示能力列表
    - error:           执行异常，前端展示错误原因
    """
    from backend.app.ai.agent_orchestrator import agent_orchestrator

    logger.info(
        "[AI Agent] query=%s project=%s auto_run=%s",
        body.query[:80], body.project_id, body.auto_run,
    )

    ctx = {**body.context}
    if body.project_id:
        ctx["project_id"] = body.project_id

    result = agent_orchestrator.process(
        query=body.query,
        context=ctx,
        auto_run=body.auto_run,
    )

    return _make_response(
        success=True,
        data={
            "answer_type": result.answer_type,
            "message": result.message,
            "capability_type": result.capability_type,
            "job_id": result.job_id,
            "job_status": result.job_status,
            "extracted_params": result.extracted_params,
            "missing_params": result.missing_params,
            "clarification_question": result.clarification_question,
            "intent_confidence": result.intent_confidence,
            "next_actions": [
                {"label": a.label, "action": a.action, "params": a.params}
                for a in result.next_actions
            ],
        },
    )


# =====================================================================
# GET /api/ai/llm/health — LLM 健康检查
# =====================================================================

@router.get("/llm/health")
def llm_health_check():
    """
    LLM Provider 健康检查。

    返回当前配置的 LLM provider 状态：
    - mock 模式：永远返回 reachable=true
    - deepseek 模式：发送最小 ping 请求验证连通性
    """
    from backend.app.config import LLM_PROVIDER, DEEPSEEK_API_KEY, DEEPSEEK_MODEL

    provider_name = LLM_PROVIDER or "mock"
    model = DEEPSEEK_MODEL if provider_name == "deepseek" else "mock-v1"

    # 1. Mock provider — always available
    if provider_name == "mock":
        return _make_response(success=True, data={
            "provider": "mock",
            "model": "mock-v1",
            "configured": True,
            "reachable": True,
            "error": None,
            "latency_ms": 0,
        })

    # 2. DeepSeek but no API key — not configured
    if not DEEPSEEK_API_KEY:
        return _make_response(success=True, data={
            "provider": "deepseek",
            "model": "",
            "configured": False,
            "reachable": False,
            "error": "DEEPSEEK_API_KEY is not set. Add it to .env or switch LLM_PROVIDER=mock.",
            "latency_ms": 0,
        })

    # 3. DeepSeek with API key — ping test
    import time
    try:
        from backend.app.ai.llm.deepseek_provider import DeepSeekProvider
        provider = DeepSeekProvider()

        from backend.app.schemas.llm import LLMRequest, LLMMessage
        ping_req = LLMRequest(
            messages=[
                LLMMessage(role="user", content="ping"),
            ],
            taskType="chat",
            temperature=0.0,
        )

        start = time.time()
        response = provider.chat(ping_req)
        elapsed_ms = int((time.time() - start) * 1000)

        # 检查响应是否包含 "pong"
        is_reachable = response.provider == "deepseek" and len(response.content) > 0

        return _make_response(success=True, data={
            "provider": "deepseek",
            "model": response.model,
            "configured": True,
            "reachable": is_reachable,
            "error": None if is_reachable else "Unexpected response from DeepSeek",
            "latency_ms": elapsed_ms,
        })

    except Exception as exc:
        logger.error("LLM health check failed: %s", exc)
        return _make_response(success=True, data={
            "provider": "deepseek",
            "model": DEEPSEEK_MODEL,
            "configured": True,
            "reachable": False,
            "error": f"{type(exc).__name__}: {str(exc)}",
            "latency_ms": 0,
        })
