"""
统一 LLM 输出 Schema 校验器

职责：
- 维护 task_type → Pydantic output schema 的映射（单一事实来源）
- 提供 validate() 方法：校验 LLM JSON 输出
- 校验失败时生成安全的 fallback 响应，不让调用方崩溃
- 记录 SCHEMA_VALIDATION_FAILED 日志

用法：
    from backend.app.ai.llm.schema_validator import schema_validator

    ok, data, errors = schema_validator.validate("intent_parse", json_data)
    if not ok:
        # data 已经是 fallback 了，可以直接使用
        logger.warning("Schema validation failed, using fallback: %s", errors)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError

from backend.app.schemas.llm import (
    LLMIntentResult,
    LLMResultInterpretation,
    LLMErrorExplanation,
    LLMReportEnhancement,
    LLMReportOutput,
    LLMParameterCompletion,
    LLMChatAnswer,
    LLMSummary,
)

logger = logging.getLogger("adipoinsight.llm.schema_validator")


# ===== task_type → Pydantic Schema 映射 =====

_SCHEMA_MAP: Dict[str, Type[BaseModel]] = {
    "intent_parse": LLMIntentResult,
    "parameter_completion": LLMParameterCompletion,
    "report_generation": LLMReportOutput,
    "result_interpretation": LLMResultInterpretation,
    "chat": LLMChatAnswer,
    "error_explanation": LLMErrorExplanation,
    "summary": LLMSummary,
}

# 确保 7 个 task_type 都有对应 schema
assert len(_SCHEMA_MAP) == 7, f"Schema map incomplete: {len(_SCHEMA_MAP)}/7"


# ===== Fallback 响应（按 task_type） =====

def _make_fallback(task_type: str) -> Dict[str, Any]:
    """为每个 task_type 生成安全的 fallback 响应。

    原则：
    - 不编造数据
    - 所有字段使用合理的空值/默认值
    - 前端可以正常渲染而不会崩溃
    """
    if task_type == "intent_parse":
        return {
            "intent": "unsupported",
            "confidence": 0.0,
            "capabilityType": "",
            "extractedParams": {},
            "missingParams": [],
            "nextAction": "clarify",
            "userMessage": "意图解析暂时不可用，请重试或使用菜单选择分析类型",
        }
    elif task_type == "parameter_completion":
        return {
            "completedParams": {},
            "suggestedDefaults": {},
            "questions": ["请提供缺失的参数"],
            "isReadyToCreate": False,
            "userMessage": "参数补全暂时不可用，请手动填写所需参数",
        }
    elif task_type == "report_generation":
        return {
            "title": "AdipoInsight 科研分析报告",
            "sections": [
                {"title": "报告生成失败", "content": "LLM 输出格式校验未通过，已使用模板报告替代。请重试或切换到 mock 模式。"},
            ],
            "limitations": ["LLM 输出校验失败"],
            "nextSteps": ["重试报告生成", "检查 LLM Provider 状态", "切换到 mock 模式"],
        }
    elif task_type == "result_interpretation":
        return {
            "capability_type": "",
            "summary": "结果解读暂时不可用（LLM 输出校验失败），请查看原始数据。",
            "key_findings": [],
            "clinical_significance": "",
            "statistical_notes": "",
            "limitations": ["LLM 输出格式校验失败，无法提供完整解读"],
            "suggested_next_steps": ["查看原始分析数据", "重试请求"],
        }
    elif task_type == "chat":
        return {
            "reply": "抱歉，AI 对话服务暂时遇到问题，请稍后重试。",
            "suggestedActions": [],
            "references": [],
        }
    elif task_type == "error_explanation":
        return {
            "error_code": "UNKNOWN_ERROR",
            "friendly_message": "无法解析错误详情，请查看后端日志获取更多信息。",
            "possible_causes": ["LLM 输出格式校验失败"],
            "suggested_actions": ["查看原始错误信息", "联系管理员"],
            "is_retryable": True,
        }
    elif task_type == "summary":
        return {
            "projectStatus": "未知",
            "completedAnalyses": [],
            "runningAnalyses": [],
            "failedAnalyses": [],
            "recommendedNext": None,
            "summaryText": "项目摘要暂时不可用（LLM 输出校验失败）",
            "pipelineProgress": {"completed": 0, "total": 7, "percent": 0},
        }
    else:
        logger.error("Unknown task_type '%s', no fallback defined", task_type)
        return {"_error": f"Unknown task_type: {task_type}"}


# ===== Schema Validator =====

class LLMSchemaValidator:
    """LLM 输出 Schema 校验器（全局单例）

    每个 task_type 有唯一对应的 Pydantic schema，
    校验失败时返回预定义的 fallback 响应，不抛出异常。
    """

    def __init__(self):
        self._schema_map = _SCHEMA_MAP

    # ===== 主入口 =====

    def validate(
        self,
        task_type: str,
        json_data: dict,
    ) -> Tuple[bool, dict, List[str]]:
        """校验 LLM JSON 输出。

        Args:
            task_type: LLM 任务类型（如 "intent_parse"）
            json_data: LLM 返回的 JSON dict

        Returns:
            (ok, data, errors)
            - ok=True: data 是通过 schema 校验的 dict
            - ok=False: data 是 fallback dict，errors 是校验失败原因列表
        """
        schema_cls = self._schema_map.get(task_type)
        if schema_cls is None:
            logger.error("No schema registered for task_type '%s'", task_type)
            return False, _make_fallback(task_type), [f"No schema for '{task_type}'"]

        if not isinstance(json_data, dict):
            logger.warning(
                "SCHEMA_VALIDATION_FAILED: task_type=%s reason=not_a_dict type=%s",
                task_type, type(json_data).__name__,
            )
            return False, _make_fallback(task_type), [f"Expected dict, got {type(json_data).__name__}"]

        try:
            validated = schema_cls(**json_data)
            # 转回 dict（使用 alias，保持 camelCase）
            data = validated.model_dump(by_alias=True)
            return True, data, []
        except ValidationError as exc:
            error_details = self._format_errors(exc)
            logger.warning(
                "SCHEMA_VALIDATION_FAILED: task_type=%s errors=%d details=%s data_keys=%d",
                task_type,
                exc.error_count(),
                error_details,
                len(json_data) if isinstance(json_data, dict) else 0,
            )
            return False, _make_fallback(task_type), error_details

    # ===== Schema 查询 =====

    def get_schema(self, task_type: str) -> Optional[Type[BaseModel]]:
        """获取 task_type 对应的 Pydantic schema 类"""
        return self._schema_map.get(task_type)

    def has_schema(self, task_type: str) -> bool:
        """检查 task_type 是否有注册的 schema"""
        return task_type in self._schema_map

    def list_schemas(self) -> Dict[str, str]:
        """列出所有 task_type → schema 类名"""
        return {k: v.__name__ for k, v in self._schema_map.items()}

    # ===== 内部 =====

    @staticmethod
    def _format_errors(exc: ValidationError) -> List[str]:
        """格式化 Pydantic ValidationError 为人类可读列表"""
        errors = []
        for err in exc.errors():
            loc = ".".join(str(l) for l in err["loc"])
            msg = err["msg"]
            errors.append(f"{loc}: {msg}")
        return errors


# ===== 全局单例 =====

schema_validator = LLMSchemaValidator()
