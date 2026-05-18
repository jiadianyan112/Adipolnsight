"""
DeepSeek LLM Provider

使用 OpenAI 兼容 SDK 调用 DeepSeek API。
实现 LLMProvider 接口，支持：
- 普通文本 / JSON 输出
- thinking 模式
- reasoning_effort
- 超时 / 重试 / 错误映射
- 日志脱敏
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Type

from openai import OpenAI, APIStatusError, APITimeoutError, APIConnectionError, RateLimitError, AuthenticationError

from backend.app.ai.llm.provider import LLMProvider
from backend.app.schemas.llm import (
    LLMRequest,
    LLMResponse,
    LLMUsage,
    LLMMessage,
)
from backend.app.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_REASONING_MODEL,
    DEEPSEEK_ENABLE_THINKING,
    DEEPSEEK_REASONING_EFFORT,
    LLM_TIMEOUT_MS,
    LLM_MAX_RETRIES,
    LLM_MAX_TOKENS,
    LLM_JSON_TEMPERATURE,
    LLM_TEXT_TEMPERATURE,
)

logger = logging.getLogger("adipoinsight.llm.deepseek")

# ===== 错误码映射 =====

DEEPSEEK_ERROR_MAP: Dict[str, str] = {
    "MISSING_API_KEY": "MISSING_API_KEY",
    "UNAUTHORIZED": "UNAUTHORIZED",
    "RATE_LIMIT": "RATE_LIMIT",
    "TIMEOUT": "TIMEOUT",
    "INVALID_JSON": "INVALID_JSON",
    "SCHEMA_VALIDATION_FAILED": "SCHEMA_VALIDATION_FAILED",
    "PROVIDER_ERROR": "PROVIDER_ERROR",
    "EMPTY_RESPONSE": "EMPTY_RESPONSE",
}


def _sanitize_for_log(text: str, max_len: int = 120) -> str:
    """截断日志内容，避免打印完整医学数据"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"...[{len(text)} chars]"


# ===== DeepSeek Provider =====

class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM Provider (OpenAI 兼容协议)"""

    def __init__(self):
        self._validate_config()

    @property
    def name(self) -> str:
        return "deepseek"

    # ===== 配置校验 =====

    def _validate_config(self):
        if not DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY is not set. "
                "Set it in .env or switch LLM_PROVIDER=mock."
            )

    def _build_client(self, timeout_ms: int) -> OpenAI:
        return OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            timeout=timeout_ms / 1000.0,
            max_retries=0,  # 我们自己管理重试
        )

    # ===== 公开方法 =====

    def chat(self, request: LLMRequest) -> LLMResponse:
        """发送文本对话请求"""
        return self._execute(request, json_mode=False)

    def chat_json(self, request: LLMRequest, output_schema: Type = None) -> LLMResponse:
        """发送 JSON 对话请求（原生 JSON mode）"""
        return self._execute(request, json_mode=True, output_schema=output_schema)

    def stream_chat(self, request: LLMRequest):
        """流式对话（预留）"""
        raise NotImplementedError("DeepSeek streaming not yet implemented")

    # ===== 核心执行 =====

    def _execute(
        self,
        request: LLMRequest,
        json_mode: bool = False,
        output_schema: Type = None,
    ) -> LLMResponse:
        """核心执行：构建请求 → 发送 → 解析 → 校验"""
        client = self._build_client(LLM_TIMEOUT_MS)
        model = self._select_model(request)
        messages = self._build_messages(request, json_mode)
        temperature = self._select_temperature(request, json_mode)
        max_tokens = request.max_tokens or LLM_MAX_TOKENS

        extra_body: Dict[str, Any] = {}
        if DEEPSEEK_ENABLE_THINKING:
            extra_body["thinking"] = {"type": "enabled"}
            if DEEPSEEK_REASONING_EFFORT:
                extra_body["thinking"]["effort"] = DEEPSEEK_REASONING_EFFORT

        logger.info(
            "DeepSeek call: model=%s task=%s json=%s msgs=%d temp=%.2f max_tokens=%d",
            model, request.task_type, json_mode, len(messages), temperature,
            max_tokens,
        )

        last_error = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "extra_body": extra_body if extra_body else None,
                }

                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                # 过滤 None 值
                kwargs = {k: v for k, v in kwargs.items() if v is not None}

                start = time.time()
                completion = client.chat.completions.create(**kwargs)
                elapsed_ms = int((time.time() - start) * 1000)

                choice = completion.choices[0]
                content = choice.message.content or ""

                if not content:
                    logger.warning("DeepSeek returned empty content")
                    return self._error_response("EMPTY_RESPONSE", "DeepSeek returned empty content")

                usage = LLMUsage(
                    prompt_tokens=completion.usage.prompt_tokens if completion.usage else 0,
                    completion_tokens=completion.usage.completion_tokens if completion.usage else 0,
                    total_tokens=completion.usage.total_tokens if completion.usage else 0,
                )

                logger.info(
                    "DeepSeek success: model=%s elapsed=%dms tokens=%s",
                    model, elapsed_ms, usage.total_tokens,
                )

                if json_mode:
                    return self._parse_json_response(content, model, usage, output_schema)
                else:
                    return LLMResponse(
                        content=content,
                        provider="deepseek",
                        model=model,
                        usage=usage,
                    )

            except AuthenticationError as exc:
                logger.error("DeepSeek auth error: %s", exc)
                return self._error_response("UNAUTHORIZED", "Invalid API Key", str(exc))

            except RateLimitError as exc:
                logger.warning("DeepSeek rate limit (attempt %d/%d)", attempt + 1, LLM_MAX_RETRIES + 1)
                last_error = exc
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(2 * (attempt + 1))
                    continue

            except APITimeoutError as exc:
                logger.warning("DeepSeek timeout (attempt %d/%d)", attempt + 1, LLM_MAX_RETRIES + 1)
                last_error = exc
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(1 * (attempt + 1))
                    continue

            except APIConnectionError as exc:
                logger.warning("DeepSeek connection error (attempt %d/%d)", attempt + 1, LLM_MAX_RETRIES + 1)
                last_error = exc
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(1 * (attempt + 1))
                    continue

            except APIStatusError as exc:
                logger.error("DeepSeek API error: status=%s", exc.status_code)
                return self._error_response("PROVIDER_ERROR", f"API status {exc.status_code}", str(exc))

            except Exception as exc:
                logger.error("DeepSeek unexpected error: %s", type(exc).__name__)
                return self._error_response("PROVIDER_ERROR", f"{type(exc).__name__}: {str(exc)}")

        return self._error_response(
            "TIMEOUT" if isinstance(last_error, APITimeoutError) else "RATE_LIMIT",
            f"Failed after {LLM_MAX_RETRIES + 1} attempts",
            str(last_error) if last_error else None,
        )

    # ===== JSON 解析与校验 =====

    def _parse_json_response(
        self,
        content: str,
        model: str,
        usage: LLMUsage,
        output_schema: Type = None,
    ) -> LLMResponse:
        """解析 JSON 响应 + schema 校验"""
        # 1. 提取 JSON（处理可能的 markdown code block）
        json_str = content.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            json_str = "\n".join(lines)

        # 2. JSON.parse
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error("DeepSeek JSON parse failed: len=%d", len(content))
            return self._error_response("INVALID_JSON", f"JSON parse error: {exc}", _sanitize_for_log(content, 200))

        # 3. Schema validate（可选）
        if output_schema is not None:
            try:
                if isinstance(parsed, dict):
                    validated = output_schema(**parsed)
                    parsed = validated.model_dump() if hasattr(validated, 'model_dump') else dict(validated)
                elif isinstance(parsed, list):
                    validated = [output_schema(**item) for item in parsed]
                    parsed = [v.model_dump() if hasattr(v, 'model_dump') else dict(v) for v in validated]
            except Exception as exc:
                logger.warning(
                    "DeepSeek schema validation failed: %s data_keys=%s",
                    exc, list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__,
                )
                return self._error_response(
                    "SCHEMA_VALIDATION_FAILED",
                    f"Schema validation failed: {exc}",
                    _sanitize_for_log(str(parsed), 200),
                )

        return LLMResponse(
            content=content,
            json_data=parsed,
            provider="deepseek",
            model=model,
            usage=usage,
        )

    # ===== 消息构建 =====

    def _build_messages(self, request: LLMRequest, json_mode: bool) -> List[Dict[str, str]]:
        """构建 OpenAI 兼容的消息列表"""
        messages: List[Dict[str, str]] = []
        for msg in request.messages:
            m: Dict[str, str] = {"role": msg.role, "content": msg.content}
            if msg.name:
                m["name"] = msg.name
            messages.append(m)

        # JSON mode 要求 system prompt 明确指示只返回 JSON
        if json_mode:
            has_system = any(m["role"] == "system" for m in messages)
            json_instruction = (
                "You MUST respond with a single valid JSON object. "
                "No markdown fences, no explanations outside the JSON. "
                "The JSON must conform to the requested schema."
            )
            if has_system:
                for m in messages:
                    if m["role"] == "system":
                        m["content"] = f"{m['content']}\n\n{json_instruction}"
                        break
            else:
                messages.insert(0, {"role": "system", "content": json_instruction})

        return messages

    # ===== 模型选择 =====

    def _select_model(self, request: LLMRequest) -> str:
        """根据 task_type 选择合适的模型"""
        if request.model:
            return request.model
        # 报告生成和深度解读使用推理模型
        reasoning_tasks = {"report_generation", "result_interpretation"}
        if request.task_type in reasoning_tasks and DEEPSEEK_REASONING_MODEL:
            return DEEPSEEK_REASONING_MODEL
        return DEEPSEEK_MODEL

    # ===== 温度选择 =====

    def _select_temperature(self, request: LLMRequest, json_mode: bool) -> float:
        if request.temperature is not None:
            return request.temperature
        return LLM_JSON_TEMPERATURE if json_mode else LLM_TEXT_TEMPERATURE

    # ===== 错误响应 =====

    def _error_response(self, code: str, message: str, raw: Any = None) -> LLMResponse:
        return LLMResponse(
            content=f"[DeepSeek Error] {code}: {message}",
            provider="deepseek",
            model="error",
        )
