"""
LLM Service — 统一 LLM 调用入口

封装 provider 选择、超时、重试、错误转换、日志。
所有 LLM 调用必须经过此 service，不允许直接调用 provider。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Type

from backend.app.schemas.llm import (
    LLMRequest,
    LLMResponse,
    LLMError as LLMErrorSchema,
)
from backend.app.ai.llm.provider import (
    LLMProvider,
    MockProvider,
    provider_registry,
)
from backend.app.config import (
    LLM_PROVIDER as CONFIG_LLM_PROVIDER,
    LLM_TIMEOUT_MS,
    LLM_MAX_RETRIES,
    LLM_MAX_TOKENS,
    LLM_JSON_TEMPERATURE,
    LLM_TEXT_TEMPERATURE,
)

# ===== 安全约束：每类 task 的 max_tokens 上限 =====

_MAX_TOKENS_LIMITS: Dict[str, int] = {
    "intent_parse": 1024,
    "parameter_completion": 1024,
    "error_explanation": 1024,
    "chat": 2048,
    "result_interpretation": 2048,
    "report_generation": 8192,
    "summary": 1024,
}

logger = logging.getLogger("adipoinsight.llm")


class LLMService:
    """
    统一 LLM 调用服务

    - 自动选择 provider（环境变量 > 默认）
    - 统一超时和重试
    - 统一错误转换为 LLMError
    - 统一日志
    """

    def __init__(
        self,
        default_provider: str = None,
        timeout_seconds: int = None,
        max_retries: int = None,
    ):
        self._default_provider = default_provider or CONFIG_LLM_PROVIDER or "mock"
        self._timeout_ms = timeout_seconds * 1000 if timeout_seconds else LLM_TIMEOUT_MS
        self._max_retries = max_retries if max_retries is not None else LLM_MAX_RETRIES
        self._json_temperature = LLM_JSON_TEMPERATURE
        self._text_temperature = LLM_TEXT_TEMPERATURE

    # ===== 安全约束 =====

    @staticmethod
    def _enforce_limits(request: LLMRequest) -> None:
        """强制安全约束：max_tokens 上限 + 禁止 tool calls。"""
        task = request.task_type or "unknown"

        # 1. max_tokens 上限（防止 token 耗尽）
        limit = _MAX_TOKENS_LIMITS.get(task, LLM_MAX_TOKENS)
        requested = request.max_tokens or LLM_MAX_TOKENS
        if requested > limit:
            logger.warning(
                "LLM max_tokens capped: task=%s requested=%d limit=%d",
                task, requested, limit,
            )
            request.max_tokens = limit
        elif not request.max_tokens:
            request.max_tokens = limit

        # 2. 禁止 function calling / tool use
        # LLMRequest schema 目前不包含 tools/function_call 字段，
        # 如果将来添加，必须在此处拦截

    # ===== 公开方法 =====

    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """
        调用 LLM 返回纯文本。

        LLM 输出仅作为展示内容，不会被直接执行。调用前强制执行安全约束。

        Args:
            request: LLMRequest（provider 字段可选，默认从配置读取）

        Returns:
            LLMResponse
        """
        self._enforce_limits(request)

        provider_name = request.provider or self._default_provider
        if not provider_registry.has(provider_name):
            available = provider_registry.list_all()
            logger.warning(
                "Provider '%s' not found, falling back to '%s'. Available: %s",
                provider_name, provider_registry.get_default().name, available,
            )
            provider_name = provider_registry.get_default().name

        provider = provider_registry.get(provider_name)
        if provider is None:
            return self._make_error_response(
                "PROVIDER_NOT_FOUND",
                f"No LLM provider available. Checked: {provider_name}",
                provider_name,
            )

        return self._execute_with_retry(provider, request, provider_name)

    def call_llm_json(
        self,
        request: LLMRequest,
        output_schema: Type = None,
    ) -> LLMResponse:
        """
        调用 LLM 返回 JSON。

        强制 schema 校验。LLM 输出仅作为数据使用，不会被直接执行。

        Schema 校验失败时自动 fallback，不抛异常。

        Args:
            request: LLMRequest
            output_schema: 可选的手动指定 Pydantic model，留空则自动解析

        Returns:
            LLMResponse (response.json_data 一定可用)
        """
        self._enforce_limits(request)
        from backend.app.ai.llm.schema_validator import schema_validator

        provider_name = request.provider or self._default_provider
        if not provider_registry.has(provider_name):
            provider_name = provider_registry.get_default().name

        provider = provider_registry.get(provider_name)
        if provider is None:
            return self._make_error_response(
                "PROVIDER_NOT_FOUND",
                f"No LLM provider available. Checked: {provider_name}",
                provider_name,
            )

        # 自动解析 schema（如果调用方未显式传入）
        resolved_schema = output_schema
        if resolved_schema is None:
            resolved_schema = schema_validator.get_schema(request.task_type)
            if resolved_schema is None:
                logger.warning(
                    "No schema registered for task_type '%s', proceeding without validation",
                    request.task_type,
                )

        json_request = request.model_copy(update={"response_format": "json"})
        try:
            response = provider.chat_json(json_request, resolved_schema)
            response.provider = provider_name
        except Exception as exc:
            logger.error("LLM JSON error: %s", exc)
            return self._make_error_response(
                "LLM_SERVICE_ERROR", f"{type(exc).__name__}: {str(exc)}", provider_name,
            )

        # 集中式 Schema 校验 + fallback
        if response.json_data is not None and isinstance(response.json_data, dict):
            ok, data, errors = schema_validator.validate(
                request.task_type, response.json_data,
            )
            if ok:
                response.json_data = data
                logger.info(
                    "LLM JSON success: provider=%s task=%s schema=validated",
                    provider_name, request.task_type,
                )
            else:
                # 校验失败 → 使用 fallback，不崩溃
                response.json_data = data
                logger.warning(
                    "SCHEMA_VALIDATION_FAILED: task=%s errors=%s — using fallback",
                    request.task_type, errors,
                )
        elif response.json_data is None:
            # LLM 没有返回 JSON → 使用 fallback
            _, data, __ = schema_validator.validate(request.task_type, {})
            response.json_data = data
            logger.warning(
                "SCHEMA_VALIDATION_FAILED: task=%s json_data is None — using fallback",
                request.task_type,
            )

        return response

    # ===== 内部方法 =====

    def _execute_with_retry(
        self,
        provider: LLMProvider,
        request: LLMRequest,
        provider_name: str,
    ) -> LLMResponse:
        """带重试的执行逻辑"""
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                logger.debug(
                    "LLM call: provider=%s task=%s attempt=%d/%d",
                    provider_name, request.task_type, attempt + 1, self._max_retries + 1,
                )
                response = provider.chat(request)
                response.provider = provider_name
                logger.info(
                    "LLM success: provider=%s task=%s tokens=%s",
                    provider_name, request.task_type,
                    response.usage.total_tokens if response.usage else "N/A",
                )
                return response

            except NotImplementedError:
                return self._make_error_response(
                    "NOT_IMPLEMENTED",
                    f"Provider '{provider_name}' does not support this operation",
                    provider_name,
                )
            except Exception as exc:
                last_error = exc
                logger.error(
                    "LLM error: provider=%s task=%s attempt=%d error=%s",
                    provider_name, request.task_type, attempt + 1, exc,
                )
                if attempt < self._max_retries and self._is_retryable(exc):
                    import time
                    time.sleep(1 * (attempt + 1))
                    continue
                break

        return self._make_error_response(
            "LLM_SERVICE_ERROR",
            f"{type(last_error).__name__}: {str(last_error)}" if last_error else "Unknown error",
            provider_name,
            retryable=False,
        )

    def _make_error_response(
        self,
        code: str,
        message: str,
        provider_name: str,
        retryable: bool = True,
    ) -> LLMResponse:
        return LLMResponse(
            content=f"[LLM Error] {code}: {message}",
            provider=provider_name,
            model="error",
        )

    def _is_retryable(self, exc: Exception) -> bool:
        retryable_types = (
            "timeout", "connection", "rate_limit", "server_error",
            "Timeout", "ConnectionError", "RateLimitError",
        )
        exc_str = str(exc)
        return any(t.lower() in exc_str.lower() for t in retryable_types)


# 全局单例
llm_service = LLMService()
