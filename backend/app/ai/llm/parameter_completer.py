"""
Parameter Completion Service — LLM 驱动的参数补全

输入用户已识别的意图和缺失参数，通过 LLM 建议合理的默认值，
对必须由用户提供的 ID 类字段（file_id, job_id, dataset_id）强制阻塞。

用法：
    from backend.app.ai.llm.parameter_completer import parameter_completer

    result = parameter_completer.complete(ParameterCompletionInput(
        intent="gwas",
        capability_type="gwas_analysis",
        extracted_params={"project_id": 1},
        missing_params=["phenotype", "covariates"],
        current_context={"exposure": "Liver_PDFF"},
    ))
    # result.message, result.suggested_inputs, result.blocked_fields
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.app.ai.llm.service import llm_service
from backend.app.ai.llm.schema_validator import schema_validator
from backend.app.schemas.llm import LLMRequest, LLMMessage, LLMParameterCompletion

logger = logging.getLogger("adipoinsight.parameter_completer")

# ===== 禁止 LLM 编造的字段（必须由用户操作提供） =====

BLOCKED_FIELDS: Dict[str, str] = {
    "file_id": "请先上传文件",
    "fileId": "请先上传文件",
    "job_id": "请从已有任务中选择",
    "jobId": "请从已有任务中选择",
    "dataset_id": "请从可用数据集中选择",
    "datasetId": "请从可用数据集中选择",
    "outcome_dataset_id": "请从 OpenGWAS 数据集中选择",
    "segmentation_job_id": "请从已完成的分割任务中选择",
}

# ===== 静态参数提示（LLM 失败时的 fallback） =====

_STATIC_HINTS: Dict[str, Dict[str, Any]] = {
    "image_segmentation": {
        "required": ["project_id", "file_id"],
        "suggestions": {
            "modality": {"value": "MRI", "label": "影像模态", "options": ["MRI", "CT"]},
            "target_structures": {
                "value": ["liver", "visceral_fat", "subcutaneous_fat", "bone_marrow"],
                "label": "分割目标",
                "options": ["liver", "pancreas", "visceral_fat", "subcutaneous_fat", "bone_marrow", "kidney", "muscle"],
            },
            "model_name": {"value": "TSSA-UNet", "label": "模型", "options": ["TSSA-UNet", "nnUNet", "SwinUNETR"]},
        },
    },
    "phenotype_quantification": {
        "required": ["project_id"],
        "suggestions": {},
    },
    "gwas_analysis": {
        "required": ["project_id", "phenotype"],
        "suggestions": {
            "phenotype": {"label": "表型名称", "hint": "如 Liver_PDFF"},
            "covariates": {"value": ["age", "sex", "bmi", "PC1-PC10"], "label": "协变量"},
            "population_filter": {"value": "EUR", "label": "人群", "options": ["EUR", "EAS", "AFR", "SAS", "AMR"]},
            "method": {"value": "REGENIE", "label": "方法", "options": ["REGENIE", "PLINK2", "SAIGE", "BOLT-LMM"]},
        },
    },
    "mendelian_randomization": {
        "required": ["project_id", "exposure", "outcome"],
        "suggestions": {
            "exposure": {"label": "暴露因素", "hint": "如 Liver_PDFF"},
            "outcome": {"label": "结局变量", "hint": "如 Osteoporosis"},
            "methods": {"value": ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"], "label": "MR 方法"},
        },
    },
    "mediation_mr": {
        "required": ["project_id", "exposure", "outcome", "mediator_source"],
        "suggestions": {
            "exposure": {"label": "暴露因素", "hint": "如 Liver_PDFF"},
            "outcome": {"label": "结局变量", "hint": "如 Osteoporosis"},
            "mediator_source": {"value": "decode_plasma", "label": "中介数据源", "options": ["decode_plasma", "metabolite_gwas", "gwas_catalog", "custom"]},
            "candidate_proteins": {"value": ["ACY1", "H6PD", "SHBG", "ADH1A", "POR", "NAAA"], "label": "候选蛋白"},
            "correction_method": {"value": "fdr", "label": "多重检验校正", "options": ["fdr", "bonferroni", "none"]},
        },
    },
    "risk_modeling": {
        "required": ["project_id", "exposure", "outcome"],
        "suggestions": {
            "exposure": {"label": "暴露因素", "hint": "如 Liver_PDFF"},
            "outcome": {"label": "结局变量", "hint": "如 Osteoporosis"},
            "outcomes": {"value": ["BMD", "TBS", "Osteopenia", "Osteoporosis"], "label": "结局变量列表"},
            "model_types": {"value": ["OLS", "RCS", "MultinomialLogistic"], "label": "模型类型"},
            "grouping": {"value": "quartile", "label": "分组方式", "options": ["quartile", "tertile", "median"]},
        },
    },
    "report_generation": {
        "required": ["project_id"],
        "suggestions": {
            "language": {"value": "zh-CN", "label": "语言", "options": ["zh-CN", "en"]},
            "report_type": {"value": "full", "label": "报告类型", "options": ["summary", "full", "competition"]},
            "title": {"label": "报告标题", "hint": "可选"},
        },
    },
}

# 常见推荐值（跨 capability 适用）
_RECOMMENDED_VALUES: Dict[str, Any] = {
    "exposure": "Liver_PDFF",
    "outcome": "Osteoporosis",
    "mediator_source": "decode_plasma",
    "candidate_proteins": ["ACY1", "H6PD", "SHBG", "ADH1A", "POR", "NAAA"],
    "method": "REGENIE",
    "covariates": ["age", "sex", "bmi", "PC1-PC10"],
    "population_filter": "EUR",
    "language": "zh-CN",
    "correction_method": "fdr",
    "grouping": "quartile",
}


# ===== 数据结构 =====

@dataclass
class ParameterCompletionInput:
    """参数补全请求"""
    intent: str = ""                           # 标准 intent（如 "gwas"）
    capability_type: str = ""                  # 能力类型（如 "gwas_analysis"）
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    missing_params: List[str] = field(default_factory=list)
    current_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SuggestedInput:
    """单个建议字段"""
    field: str                                 # 字段名
    label: str = ""                            # 人类可读标签
    suggested_value: Any = None                # 推荐值
    field_type: str = "text"                   # text | select | multi-select | upload
    options: List[Any] = field(default_factory=list)   # select/multi-select 的可选项
    hint: str = ""                             # 辅助提示


@dataclass
class ParameterCompletionOutput:
    """参数补全结果"""
    message: str = ""                          # 人类可读摘要
    missing_params: List[str] = field(default_factory=list)
    suggested_inputs: List[SuggestedInput] = field(default_factory=list)
    blocked_fields: List[str] = field(default_factory=list)


# ===== Service =====

class ParameterCompletionService:
    """参数补全服务

    优先通过 LLM 智能补全参数，LLM 不可用或校验失败时
    fallback 到静态 PARAM_HINTS。
    """

    def __init__(self):
        self._llm = llm_service

    # ===== 主入口 =====

    def complete(self, input_data: ParameterCompletionInput) -> ParameterCompletionOutput:
        """补全缺失参数。

        Args:
            input_data: 包含 intent、capability_type、已提取参数、缺失参数列表

        Returns:
            ParameterCompletionOutput（始终可用，不抛异常）
        """
        cap = input_data.capability_type

        # 1. 尝试 LLM 补全
        llm_result = self._try_llm_completion(input_data)

        # 2. 合并静态 hints（补充 LLM 可能遗漏的）
        merged = self._merge_with_static_hints(llm_result, input_data, cap)

        # 3. 标记阻塞字段（ID 类字段必须用户操作）
        blocked = self._identify_blocked_fields(merged.missing_params, input_data)

        merged.blocked_fields = blocked
        return merged

    # ===== LLM 路径 =====

    def _try_llm_completion(self, input_data: ParameterCompletionInput) -> Optional[ParameterCompletionOutput]:
        """尝试通过 LLM 补全参数。失败返回 None。"""
        cap = input_data.capability_type
        if not cap:
            logger.info("No capability_type provided, skipping LLM completion")
            return None

        try:
            from backend.app.ai.llm.prompts.parameter_completion import SYSTEM_PROMPT, build_user_prompt

            user_msg = build_user_prompt(
                capability_type=cap,
                extracted_params=input_data.extracted_params,
                missing_params=input_data.missing_params,
                project_context=str(input_data.current_context) if input_data.current_context else "",
            )

            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=SYSTEM_PROMPT),
                    LLMMessage(role="user", content=user_msg),
                ],
                taskType="parameter_completion",
                temperature=0.2,
            )

            response = self._llm.call_llm_json(request)

            if response.json_data is None:
                logger.warning("LLM parameter completion returned no JSON data")
                return None

            data = response.json_data
            return self._convert_llm_response(data, cap, input_data)

        except Exception as exc:
            logger.warning("LLM parameter completion failed: %s", exc)
            return None

    def _convert_llm_response(
        self,
        data: dict,
        capability_type: str,
        input_data: ParameterCompletionInput,
    ) -> ParameterCompletionOutput:
        """将 LLM JSON 响应转换为 ParameterCompletionOutput。"""
        completed = data.get("completedParams", {})
        suggested = data.get("suggestedDefaults", {})
        questions = data.get("questions", [])
        user_msg = data.get("userMessage", "")

        # 合并完成参数 + 建议默认值
        all_resolved = {**suggested, **completed}

        # 重新计算仍缺失的参数
        still_missing = [
            p for p in input_data.missing_params
            if p not in all_resolved
        ]

        # 构建 suggested_inputs
        suggested_inputs = []
        hints = _STATIC_HINTS.get(capability_type, {}).get("suggestions", {})

        # 已解析的字段 → 带推荐值
        for field, value in all_resolved.items():
            if field in ("project_id",):
                continue
            hint = hints.get(field, {})
            field_type = self._infer_field_type(field, value)
            suggested_inputs.append(SuggestedInput(
                field=field,
                label=hint.get("label", field),
                suggested_value=value,
                field_type=field_type,
                options=hint.get("options", []),
                hint=hint.get("hint", ""),
            ))

        # 仍缺失的字段 → 带占位 hint
        for field in still_missing:
            if field in ("project_id",):
                continue
            hint = hints.get(field, {})
            rec_value = _RECOMMENDED_VALUES.get(field)
            field_type = self._classify_missing_field(field)
            suggested_inputs.append(SuggestedInput(
                field=field,
                label=hint.get("label", field),
                suggested_value=rec_value,
                field_type=field_type,
                options=hint.get("options", []),
                hint=hint.get("hint", ""),
            ))

        return ParameterCompletionOutput(
            message=user_msg or f"还需要补充 {len(still_missing)} 个参数",
            missing_params=still_missing,
            suggested_inputs=suggested_inputs,
        )

    # ===== 静态 fallback =====

    def _build_static_output(
        self,
        input_data: ParameterCompletionInput,
        capability_type: str,
    ) -> ParameterCompletionOutput:
        """纯静态 hint，不调用 LLM。"""
        hints = _STATIC_HINTS.get(capability_type, {})
        required = hints.get("required", [])
        suggestions = hints.get("suggestions", {})

        # 计算缺失
        merged = {**input_data.current_context, **input_data.extracted_params}
        missing = [p for p in required if p not in merged or not merged[p]]

        suggested_inputs = []
        for field, hint_data in suggestions.items():
            rec_value = _RECOMMENDED_VALUES.get(field) or hint_data.get("value")
            field_type = self._infer_field_type(field, rec_value)
            suggested_inputs.append(SuggestedInput(
                field=field,
                label=hint_data.get("label", field),
                suggested_value=rec_value,
                field_type=field_type,
                options=hint_data.get("options", []),
                hint=hint_data.get("hint", ""),
            ))

        return ParameterCompletionOutput(
            message=f"请补充以下信息以继续「{capability_type}」分析",
            missing_params=missing,
            suggested_inputs=suggested_inputs,
        )

    def _merge_with_static_hints(
        self,
        llm_result: Optional[ParameterCompletionOutput],
        input_data: ParameterCompletionInput,
        capability_type: str,
    ) -> ParameterCompletionOutput:
        """合并 LLM 结果与静态 hints。LLM 结果为 None 时纯静态。"""
        if llm_result is None:
            return self._build_static_output(input_data, capability_type)

        # LLM 成功 → 用静态 hints 补充遗漏的字段
        hints = _STATIC_HINTS.get(capability_type, {}).get("suggestions", {})
        llm_fields = {s.field for s in llm_result.suggested_inputs}

        for field, hint_data in hints.items():
            if field in llm_fields:
                continue
            if field in ("project_id",):
                continue
            rec_value = _RECOMMENDED_VALUES.get(field) or hint_data.get("value")
            field_type = self._infer_field_type(field, rec_value)
            llm_result.suggested_inputs.append(SuggestedInput(
                field=field,
                label=hint_data.get("label", field),
                suggested_value=rec_value,
                field_type=field_type,
                options=hint_data.get("options", []),
                hint=hint_data.get("hint", ""),
            ))

        return llm_result

    # ===== 辅助方法 =====

    def _identify_blocked_fields(
        self,
        missing_params: List[str],
        input_data: ParameterCompletionInput,
    ) -> List[str]:
        """识别必须由用户操作提供的阻塞字段。"""
        blocked = []
        all_params = set(missing_params) | set(input_data.missing_params)
        for param in all_params:
            if param in BLOCKED_FIELDS:
                blocked.append(param)
        return blocked

    def _infer_field_type(self, field: str, value: Any) -> str:
        """推断字段的 UI 类型。"""
        if field in BLOCKED_FIELDS:
            return "upload" if "file" in field else "select"
        if isinstance(value, list):
            return "multi-select"
        if isinstance(value, bool):
            return "toggle"
        return "text"

    def _classify_missing_field(self, field: str) -> str:
        """对缺失字段分类。"""
        if field in BLOCKED_FIELDS:
            return "upload" if "file" in field else "select"
        return "text"


# ===== 全局单例 =====

parameter_completer = ParameterCompletionService()
