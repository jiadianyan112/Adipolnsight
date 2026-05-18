"""
Error Explanation Service — 将技术错误翻译为用户友好解释

通过 LLM 生成可操作的错误解释，LLM 不可用时 fallback 到静态模板。

约束：
- 不隐藏真实错误码
- 不编造"已修复"状态
- 不建议危险操作
- 不绕过安全机制
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger("adipoinsight.error_explainer")


# ============================================================
# 数据结构
# ============================================================

@dataclass
class ErrorExplanationInput:
    error_code: str = ""
    technical_message: str = ""
    job_type: str = ""
    stage: str = ""
    user_action: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorExplanationOutput:
    user_message: str = ""
    possible_reasons: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    technical_summary: str = ""


# ============================================================
# 静态 fallback（每个错误码一条）
# ============================================================

_STATIC_EXPLANATIONS: Dict[str, Dict[str, Any]] = {
    "ADAPTER_NOT_FOUND": {
        "user_message": "该分析能力尚未配置或未注册，无法执行。",
        "possible_reasons": [
            "该分析类型的 Skill Adapter 未在后端注册",
            "task_type 参数传递错误",
            "后端启动时 Skill 注册失败",
        ],
        "next_actions": [
            "联系管理员确认该能力是否已部署",
            "尝试其他可用的分析类型",
            "查看 /api/ai/capabilities 确认可用能力列表",
        ],
    },
    "INVALID_INPUT": {
        "user_message": "输入参数不满足分析的最低要求。",
        "possible_reasons": [
            "缺少必填字段（如 phenotype、exposure、outcome）",
            "参数类型不正确（如传入了字符串而非数字）",
            "参数值超出允许范围",
        ],
        "next_actions": [
            "检查输入参数是否完整",
            "对照输入格式重新提交",
            "使用 AI 助手补全缺失参数",
        ],
    },
    "FILE_NOT_FOUND": {
        "user_message": "找不到指定的文件。",
        "possible_reasons": [
            "文件已被删除或移动",
            "文件 ID 不正确",
            "存储路径配置错误",
        ],
        "next_actions": [
            "重新上传文件",
            "检查文件 ID 是否正确",
            "确认存储目录存在且可访问",
        ],
    },
    "SCRIPT_NOT_FOUND": {
        "user_message": "分析脚本未找到，无法执行。",
        "possible_reasons": [
            "分析脚本未安装或路径配置错误",
            "服务器环境缺少必要的 Python/R 依赖",
        ],
        "next_actions": [
            "联系管理员安装对应的分析脚本",
            "检查 backend/app/config.py 中的脚本路径配置",
            "确认 ANALYSIS_SCRIPTS_DIR 指向正确目录",
        ],
    },
    "SCRIPT_EXECUTION_FAILED": {
        "user_message": "分析脚本执行失败（异常退出）。",
        "possible_reasons": [
            "输入数据格式不兼容",
            "脚本依赖缺失",
            "内存不足或计算资源不足",
        ],
        "next_actions": [
            "检查输入数据的格式是否正确",
            "查看后端日志获取详细的脚本错误信息",
            "减少数据量后重试",
        ],
    },
    "OUTPUT_JSON_INVALID": {
        "user_message": "分析脚本的输出格式异常，无法解析结果。",
        "possible_reasons": [
            "脚本执行被中断，输出不完整",
            "脚本输出格式不符合预期 JSON schema",
        ],
        "next_actions": [
            "重新提交任务",
            "检查脚本日志排查异常退出原因",
        ],
    },
    "OUTPUT_FILE_MISSING": {
        "user_message": "预期的输出文件未生成。",
        "possible_reasons": [
            "脚本执行完成但未写入输出文件",
            "输出路径权限不足",
            "磁盘空间已满",
        ],
        "next_actions": [
            "检查输出目录的磁盘空间和写权限",
            "重新提交任务",
            "联系管理员检查存储配置",
        ],
    },
    "TASK_TIMEOUT": {
        "user_message": "任务执行超时（超过时间限制）。",
        "possible_reasons": [
            "输入数据量过大，计算时间超限",
            "网络请求超时（外部 API 调用）",
            "LLM 响应时间过长",
        ],
        "next_actions": [
            "减少样本量或 SNP 数量后重试",
            "检查网络连接状态",
            "如果使用 LLM 功能，可增加 LLM_TIMEOUT_MS 配置",
        ],
    },
    "DATABASE_ERROR": {
        "user_message": "数据库操作失败。",
        "possible_reasons": [
            "磁盘空间不足",
            "数据库文件权限问题",
            "数据库连接异常",
        ],
        "next_actions": [
            "稍后重试",
            "联系管理员检查数据库状态",
        ],
    },
    "UPSTREAM_DEPENDENCY_FAILED": {
        "user_message": "前置依赖任务执行失败，当前任务无法继续。",
        "possible_reasons": [
            "上游分析任务未成功完成",
            "依赖的上传文件或数据缺失",
        ],
        "next_actions": [
            "先检查并修复上游任务的错误",
            "确认所有前置任务的状态为 succeeded",
            "按 pipeline 顺序逐个执行分析",
        ],
    },
    "JOB_NOT_FOUND": {
        "user_message": "未找到指定的任务。",
        "possible_reasons": [
            "任务 ID 不正确",
            "任务已被清理（当前使用内存存储，重启后丢失）",
        ],
        "next_actions": [
            "检查任务 ID 是否正确",
            "重新创建分析任务",
        ],
    },
    "JOB_ALREADY_CANCELLED": {
        "user_message": "该任务已被取消，无法执行此操作。",
        "possible_reasons": ["用户或系统手动取消了该任务"],
        "next_actions": ["重新创建任务", "查看其他可用任务"],
    },
    "MODEL_SERVICE_ERROR": {
        "user_message": "AI 模型服务异常。",
        "possible_reasons": [
            "GPU 资源不足或模型加载失败",
            "推理请求超时",
        ],
        "next_actions": [
            "稍后重试",
            "如果持续失败，切换到 mock 模式",
            "联系管理员检查 GPU/模型状态",
        ],
    },
    "LLM_API_ERROR": {
        "user_message": "LLM API 调用失败。",
        "possible_reasons": [
            "API Key 未配置或无效",
            "API 服务暂时不可用",
            "请求频率超限",
        ],
        "next_actions": [
            "检查 .env 中 DEEPSEEK_API_KEY 是否正确",
            "查看 /api/ai/llm/health 确认 LLM 状态",
            "切换到 mock 模式 (LLM_PROVIDER=mock)",
        ],
    },
    "SCHEMA_VALIDATION_FAILED": {
        "user_message": "LLM 输出格式校验失败，已使用安全 fallback 替代。",
        "possible_reasons": [
            "LLM 返回了不符合预期 JSON schema 的数据",
            "LLM 输出缺少必填字段",
        ],
        "next_actions": [
            "系统已自动回退到模板/Mock 结果，功能不受影响",
            "重试请求可能得到不同的结果",
            "如果频繁出现，联系管理员检查 LLM prompt 配置",
        ],
    },
    "UNKNOWN_ERROR": {
        "user_message": "发生未知错误，请稍后重试。",
        "possible_reasons": ["未分类的系统异常"],
        "next_actions": ["稍后重试", "查看后端日志获取详细错误信息", "联系管理员"],
    },
    "FILE_TOO_LARGE": {
        "user_message": "上传文件超过大小限制。",
        "possible_reasons": ["文件体积超过 MAX_UPLOAD_SIZE 配置（默认 200MB）"],
        "next_actions": ["压缩文件后重新上传", "分割大文件分批上传", "联系管理员调整上传限制"],
    },
    "UNSUPPORTED_FILE_TYPE": {
        "user_message": "不支持的文件格式。",
        "possible_reasons": ["文件格式不在允许列表中（允许 .nii, .nii.gz, .dcm, .csv, .tsv 等）"],
        "next_actions": ["将文件转换为支持的格式", "查看 ALLOWED_IMAGE_FORMATS 和 ALLOWED_DATA_FORMATS 配置"],
    },
    "MISSING_REQUIRED_PARAM": {
        "user_message": "缺少必填参数。",
        "possible_reasons": ["请求中未包含必填字段"],
        "next_actions": ["补全缺失的参数后重新提交", "使用 AI 助手补全参数"],
    },
    "INVALID_PARAMETER": {
        "user_message": "参数值不合法。",
        "possible_reasons": ["参数类型错误", "参数值超出允许范围"],
        "next_actions": ["检查参数格式和取值范围", "参考 API 文档修正参数"],
    },
    "RESULT_NOT_FOUND": {
        "user_message": "未找到分析结果。",
        "possible_reasons": ["任务尚未完成", "任务 ID 不正确", "结果已被清理"],
        "next_actions": ["等待任务完成后重试", "检查任务 ID 是否正确"],
    },
    "PROJECT_NOT_FOUND": {
        "user_message": "未找到指定的项目。",
        "possible_reasons": ["项目 ID 不正确", "项目已被删除"],
        "next_actions": ["检查项目 ID", "返回项目列表重新选择"],
    },
    "JOB_FAILED": {
        "user_message": "任务执行失败。",
        "possible_reasons": ["脚本执行异常", "输入数据问题", "资源不足"],
        "next_actions": ["查看错误详情确定具体原因", "修复问题后重新运行"],
    },
    "JOB_ALREADY_TERMINAL": {
        "user_message": "该任务已处于终态，无法执行此操作。",
        "possible_reasons": ["任务已完成、失败或已被取消"],
        "next_actions": ["使用 rerun 重新创建任务", "查看任务结果"],
    },
    "SKILL_NOT_AVAILABLE": {
        "user_message": "该 AI 能力当前不可用。",
        "possible_reasons": ["Skill Adapter 未注册", "服务暂时不可用"],
        "next_actions": ["检查 /api/ai/capabilities 确认可用能力", "稍后重试"],
    },
    "SKILL_EXECUTION_ERROR": {
        "user_message": "AI 能力执行异常。",
        "possible_reasons": ["Skill run() 方法抛出未捕获异常", "输入数据与 Skill 不兼容"],
        "next_actions": ["检查输入数据格式", "查看后端日志定位异常", "尝试其他参数"],
    },
    "SCRIPT_EXECUTION_ERROR": {
        "user_message": "脚本执行异常。",
        "possible_reasons": ["脚本运行时错误", "系统资源不足", "依赖缺失"],
        "next_actions": ["查看 script 的 stderr 输出", "确认运行环境配置正确", "减少数据量重试"],
    },
    "EXTERNAL_API_ERROR": {
        "user_message": "外部 API 调用失败。",
        "possible_reasons": ["外部服务不可用", "API 配额超限", "网络连接问题"],
        "next_actions": ["稍后重试", "检查网络连接", "确认外部服务状态"],
    },
    "NOT_IMPLEMENTED": {
        "user_message": "该功能尚未实现，当前仅可用 mock 模式。",
        "possible_reasons": ["真实分析模式尚未接入", "对应的 Real Adapter 未部署"],
        "next_actions": ["切换到 mock 模式使用模拟数据", "等待后续版本更新"],
    },
    "INTERNAL_ERROR": {
        "user_message": "服务器内部错误。",
        "possible_reasons": ["未预期的系统异常", "代码逻辑错误"],
        "next_actions": ["稍后重试", "查看后端日志获取完整堆栈", "联系管理员"],
    },
    "NETWORK_ERROR": {
        "user_message": "网络连接异常。",
        "possible_reasons": ["后端服务不可达", "网络代理配置问题", "DNS 解析失败"],
        "next_actions": ["检查后端服务是否运行", "确认 API 地址和端口配置", "检查防火墙/代理设置"],
    },
    "EMPTY_RESPONSE": {
        "user_message": "后端返回空响应。",
        "possible_reasons": ["服务端异常中断", "请求超时", "数据未就绪"],
        "next_actions": ["稍后重试", "检查服务端日志", "减少请求数据量"],
    },
    # 通用 fallback
    "_DEFAULT": {
        "user_message": "任务执行过程中出现异常。",
        "possible_reasons": ["系统异常，请检查后端日志"],
        "next_actions": ["稍后重试", "联系管理员"],
    },
}


# ============================================================
# Service
# ============================================================

class ErrorExplanationService:
    """错误解释服务 —— LLM 优先，静态 fallback。"""

    def explain(self, input_data: ErrorExplanationInput) -> ErrorExplanationOutput:
        """生成用户友好的错误解释。

        Args:
            input_data: 错误上下文信息

        Returns:
            ErrorExplanationOutput（始终可用，不抛异常）
        """
        # 1. 尝试 LLM 路径
        llm_result = self._try_llm(input_data)
        if llm_result is not None:
            return llm_result

        # 2. Fallback 到静态解释
        return self._static_explain(input_data)

    # ===== LLM 路径 =====

    def _try_llm(self, input_data: ErrorExplanationInput) -> ErrorExplanationOutput | None:
        """通过 LLM 生成解释。失败返回 None。"""
        try:
            from backend.app.ai.llm.service import llm_service
            from backend.app.ai.llm.prompts.error_explainer import (
                SYSTEM_PROMPT,
                build_user_prompt,
            )
            from backend.app.schemas.llm import LLMRequest, LLMMessage

            user_msg = build_user_prompt(
                error_code=input_data.error_code,
                error_message=input_data.technical_message,
                capability_type=input_data.job_type,
                job_id=input_data.context.get("job_id", ""),
            )

            # 附加用户操作上下文
            if input_data.user_action:
                user_msg += f"\nUser was trying to: {input_data.user_action}"
            if input_data.stage:
                user_msg += f"\nFailed at stage: {input_data.stage}"

            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=SYSTEM_PROMPT),
                    LLMMessage(role="user", content=user_msg),
                ],
                taskType="error_explanation",
                temperature=0.2,
            )

            response = llm_service.call_llm_json(request)

            if response.json_data is None or not isinstance(response.json_data, dict):
                return None

            data = response.json_data

            # 只取有实际内容的结果
            if not data.get("friendly_message") and not data.get("error_code"):
                return None

            return ErrorExplanationOutput(
                user_message=data.get("friendly_message", ""),
                possible_reasons=data.get("possible_causes", []),
                next_actions=data.get("suggested_actions", []),
                technical_summary=(
                    f"[{data.get('error_code', input_data.error_code)}] "
                    f"{input_data.technical_message[:200]}"
                ),
            )

        except Exception as exc:
            logger.warning("LLM error explanation failed: %s", exc)
            return None

    # ===== 静态路径 =====

    def _static_explain(self, input_data: ErrorExplanationInput) -> ErrorExplanationOutput:
        """使用静态模板生成解释。"""
        code = input_data.error_code or "UNKNOWN_ERROR"
        tmpl = _STATIC_EXPLANATIONS.get(code) or _STATIC_EXPLANATIONS["_DEFAULT"]

        user_msg = tmpl["user_message"]
        # 附加上下文信息
        if input_data.job_type:
            user_msg += f"（分析类型: {input_data.job_type}）"
        if input_data.stage:
            user_msg += f"（失败阶段: {input_data.stage}）"

        return ErrorExplanationOutput(
            user_message=user_msg,
            possible_reasons=list(tmpl.get("possible_reasons", [])),
            next_actions=list(tmpl.get("next_actions", [])),
            technical_summary=f"[{code}] {input_data.technical_message[:200]}",
        )


# ===== 全局单例 =====

error_explainer = ErrorExplanationService()
