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
    LLM_JSON_TEMPERATURE,
    LLM_TEXT_TEMPERATURE,
)

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

    # ===== 公开方法 =====

    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """
        调用 LLM 返回纯文本。

        Args:
            request: LLMRequest（provider 字段可选，默认从配置读取）

        Returns:
            LLMResponse

        Raises:
            LLMError: 所有错误统一转换为 LLMError schema
        """
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

        MockProvider 会根据 taskType 返回对应的结构化 JSON。
        真实 Provider 会强制 JSON mode + 解析 + 可选 schema validate。

        Args:
            request: LLMRequest
            output_schema: 可选的 Pydantic model 用于校验

        Returns:
            LLMResponse (response.json_data 已填充)
        """
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

        json_request = request.model_copy(update={"response_format": "json"})
        try:
            response = provider.chat_json(json_request, output_schema)
            response.provider = provider_name
            logger.info("LLM JSON success: provider=%s task=%s", provider_name, request.task_type)
        except Exception as exc:
            logger.error("LLM JSON error: %s", exc)
            return self._make_error_response(
                "LLM_SERVICE_ERROR", f"{type(exc).__name__}: {str(exc)}", provider_name,
            )

        # Schema 校验
        if output_schema is not None and response.json_data is not None:
            try:
                validated = output_schema(**response.json_data)
                response.json_data = validated.model_dump() if hasattr(validated, 'model_dump') else dict(validated)
            except Exception as exc:
                logger.warning("LLM JSON schema validation failed: %s", exc)

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
