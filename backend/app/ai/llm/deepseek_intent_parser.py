"""
LLM Intent Parser — DeepSeek 驱动的意图解析

通过 LLM Service 调用 DeepSeek（不直接 import DeepSeekProvider），
将用户自然语言输入解析为标准 IntentParseResult。

约束：
- 只负责理解用户意图，不创建 Job
- 不允许 LLM 编造 fileId/jobId/datasetId/真实分析结果/上传文件路径
- 所有输出必须 schema validate
- LLM 不可用时自动 fallback 返回 unsupported
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.app.ai.llm.service import llm_service
from backend.app.schemas.llm import LLMRequest, LLMMessage, LLMIntentResult
from backend.app.ai.intent_types import IntentParseResult, STANDARD_INTENT

logger = logging.getLogger("adipoinsight.llm.intent_parser")

# ===== System Prompt (sourced from centralized prompts module) =====

from backend.app.ai.llm.prompts.intent_parser import SYSTEM_PROMPT  # noqa: E402

CAPABILITY_MAP: Dict[str, str] = {
    "segmentation": "image_segmentation",
    "phenotype": "phenotype_quantification",
    "gwas": "gwas_analysis",
    "mr": "mendelian_randomization",
    "mediation_mr": "mediation_mr",
    "risk_modeling": "risk_modeling",
    "report": "report_generation",
}

# LLM 禁止编造的字段
FORBIDDEN_PARAMS = {
    "fileId", "file_id", "jobId", "job_id",
    "datasetId", "dataset_id", "result", "results",
    "filePath", "file_path", "url", "path",
    "dice_score", "p_value", "beta", "odds_ratio", "effect_size",
}


class LLMIntentParser:
    """
    LLM 驱动的意图解析器。

    通过 LLM Service 调用（不直接依赖 DeepSeekProvider），
    将自然语言输入解析为标准 IntentParseResult。
    """

    def __init__(self):
        self._llm = llm_service

    def parse(self, text: str) -> IntentParseResult:
        """
        解析用户输入。

        Args:
            text: 用户自然语言输入

        Returns:
            IntentParseResult（source="llm" 或 source="rule" 如果 fallback）
        """
        if not text or not text.strip():
            return IntentParseResult(
                intent="unsupported",
                confidence=0.0,
                source="llm",
                user_message="请输入您想要执行的分析任务描述",
                raw_input=text,
            )

        try:
            return self._parse_with_llm(text)
        except Exception as exc:
            logger.warning("LLM intent parse failed, returning unsupported: %s", exc)
            return IntentParseResult(
                intent="unsupported",
                confidence=0.0,
                source="llm",
                user_message="意图解析暂时不可用，请重试或使用菜单选择分析类型",
                warnings=[f"LLM parse error: {type(exc).__name__}"],
                raw_input=text,
            )

    def _parse_with_llm(self, text: str) -> IntentParseResult:
        """通过 LLM Service 解析意图"""
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=text),
            ],
            taskType="intent_parse",
            temperature=0.1,
        )

        response = self._llm.call_llm_json(request, LLMIntentResult)

        if response.json_data is None:
            logger.warning("LLM returned no JSON data for intent parse")
            return IntentParseResult(
                intent="unsupported",
                confidence=0.0,
                source="llm",
                user_message="意图解析失败，请尝试用更具体的描述",
                warnings=["LLM returned no valid JSON"],
                raw_input=text,
            )

        return self._validate_and_convert(response.json_data, text)

    def _validate_and_convert(
        self, data: Dict[str, Any], raw_input: str
    ) -> IntentParseResult:
        """Schema validate LLM 输出并转换为 IntentParseResult"""
        warnings: List[str] = []

        # 1. 校验 intent 枚举
        intent = data.get("intent", "unsupported")
        if intent not in STANDARD_INTENT:
            warnings.append(f"LLM returned invalid intent '{intent}', falling back to 'unsupported'")
            intent = "unsupported"

        # 2. 校验 confidence 范围
        confidence = data.get("confidence", 0.0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            warnings.append(f"Invalid confidence {confidence}, clamping to 0.0-1.0")
            confidence = max(0.0, min(1.0, float(confidence or 0)))

        # 3. 校验 capabilityType
        capability_type = data.get("capabilityType", "")
        if intent in CAPABILITY_MAP and capability_type != CAPABILITY_MAP[intent]:
            capability_type = CAPABILITY_MAP[intent]

        # 4. 校验 extractedParams
        extracted_params = data.get("extractedParams", {})
        if not isinstance(extracted_params, dict):
            warnings.append("extractedParams is not a dict, resetting")
            extracted_params = {}

        # 5. 过滤 LLM 编造的禁止字段
        sanitized_params = {}
        for key, value in extracted_params.items():
            if key in FORBIDDEN_PARAMS:
                warnings.append(f"LLM attempted to invent forbidden param '{key}', removed")
                continue
            sanitized_params[key] = value
        extracted_params = sanitized_params

        # 6. 校验 missingParams
        missing_params = data.get("missingParams", [])
        if not isinstance(missing_params, list):
            warnings.append("missingParams is not a list, resetting")
            missing_params = []

        # 7. nextAction
        next_action = data.get("nextAction", "")
        if next_action not in ("create_job", "provide_param", "clarify", ""):
            next_action = "clarify"

        # 8. userMessage
        user_message = data.get("userMessage", "")

        return IntentParseResult(
            intent=intent,
            confidence=round(float(confidence), 3),
            capability_type=capability_type,
            extracted_params=extracted_params,
            missing_params=missing_params,
            next_action=next_action,
            user_message=user_message,
            source="llm",
            warnings=warnings,
            raw_input=raw_input,
        )


# 全局单例
llm_intent_parser = LLMIntentParser()
