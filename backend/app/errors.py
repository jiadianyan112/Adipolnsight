"""
AdipoInsight 统一错误码与异常处理

所有 AI 接口返回的错误必须使用此处定义的错误码。
前端根据错误码展示对应的中文提示，不允许硬编码。
"""

from typing import Any, Dict, Optional


# ===== 错误码枚举 =====

class ErrorCode:
    """统一错误码"""

    # 输入校验 (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    MISSING_REQUIRED_PARAM = "MISSING_REQUIRED_PARAM"
    INVALID_PARAMETER = "INVALID_PARAMETER"

    # 资源不存在 (4xx)
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    RESULT_NOT_FOUND = "RESULT_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"

    # 任务状态冲突 (4xx)
    JOB_FAILED = "JOB_FAILED"
    JOB_ALREADY_CANCELLED = "JOB_ALREADY_CANCELLED"
    JOB_ALREADY_TERMINAL = "JOB_ALREADY_TERMINAL"
    UPSTREAM_DEPENDENCY_FAILED = "UPSTREAM_DEPENDENCY_FAILED"

    # Skill / Adapter (5xx)
    SKILL_NOT_AVAILABLE = "SKILL_NOT_AVAILABLE"
    ADAPTER_NOT_FOUND = "ADAPTER_NOT_FOUND"
    SKILL_EXECUTION_ERROR = "SKILL_EXECUTION_ERROR"

    # 脚本执行 (5xx)
    SCRIPT_NOT_FOUND = "SCRIPT_NOT_FOUND"
    SCRIPT_EXECUTION_FAILED = "SCRIPT_EXECUTION_FAILED"
    SCRIPT_EXECUTION_ERROR = "SCRIPT_EXECUTION_ERROR"
    OUTPUT_JSON_INVALID = "OUTPUT_JSON_INVALID"
    OUTPUT_FILE_MISSING = "OUTPUT_FILE_MISSING"

    # 外部服务 (5xx)
    MODEL_SERVICE_ERROR = "MODEL_SERVICE_ERROR"
    LLM_API_ERROR = "LLM_API_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"

    # 系统 (5xx)
    DATABASE_ERROR = "DATABASE_ERROR"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

    # 网络 (0xx)
    NETWORK_ERROR = "NETWORK_ERROR"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"


# ===== HTTP 状态码映射 =====

ERROR_HTTP_STATUS: Dict[str, int] = {
    ErrorCode.INVALID_INPUT: 400,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.UNSUPPORTED_FILE_TYPE: 415,
    ErrorCode.MISSING_REQUIRED_PARAM: 400,
    ErrorCode.INVALID_PARAMETER: 400,
    ErrorCode.JOB_NOT_FOUND: 404,
    ErrorCode.RESULT_NOT_FOUND: 404,
    ErrorCode.FILE_NOT_FOUND: 404,
    ErrorCode.PROJECT_NOT_FOUND: 404,
    ErrorCode.JOB_FAILED: 409,
    ErrorCode.JOB_ALREADY_CANCELLED: 409,
    ErrorCode.JOB_ALREADY_TERMINAL: 409,
    ErrorCode.UPSTREAM_DEPENDENCY_FAILED: 409,
    ErrorCode.SKILL_NOT_AVAILABLE: 503,
    ErrorCode.ADAPTER_NOT_FOUND: 500,
    ErrorCode.SKILL_EXECUTION_ERROR: 500,
    ErrorCode.SCRIPT_NOT_FOUND: 500,
    ErrorCode.SCRIPT_EXECUTION_FAILED: 500,
    ErrorCode.SCRIPT_EXECUTION_ERROR: 500,
    ErrorCode.OUTPUT_JSON_INVALID: 500,
    ErrorCode.OUTPUT_FILE_MISSING: 500,
    ErrorCode.MODEL_SERVICE_ERROR: 502,
    ErrorCode.LLM_API_ERROR: 502,
    ErrorCode.EXTERNAL_API_ERROR: 502,
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.TASK_TIMEOUT: 504,
    ErrorCode.NOT_IMPLEMENTED: 501,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.UNKNOWN_ERROR: 500,
    # 前端/网络侧（无对应 HTTP 状态码，用 0 表示）
    ErrorCode.NETWORK_ERROR: 0,
    ErrorCode.EMPTY_RESPONSE: 0,
}


# ===== 异常类 =====

class AdipoInsightError(Exception):
    """基础异常"""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.http_status = ERROR_HTTP_STATUS.get(code, 500)
        super().__init__(message)


class InvalidInputError(AdipoInsightError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(ErrorCode.INVALID_INPUT, message, details)


class JobNotFoundError(AdipoInsightError):
    def __init__(self, job_id: str):
        super().__init__(ErrorCode.JOB_NOT_FOUND, f"Job '{job_id}' not found", {"job_id": job_id})


class SkillNotAvailableError(AdipoInsightError):
    def __init__(self, capability: str):
        super().__init__(ErrorCode.SKILL_NOT_AVAILABLE, f"Skill '{capability}' is not available", {"capability": capability})


class ScriptExecutionError(AdipoInsightError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(ErrorCode.SCRIPT_EXECUTION_ERROR, message, details)


class FileTooLargeError(AdipoInsightError):
    def __init__(self, size: int, max_size: int):
        super().__init__(
            ErrorCode.FILE_TOO_LARGE,
            f"File size {size} exceeds maximum {max_size} bytes",
            {"file_size": size, "max_size": max_size},
        )


class UnsupportedFileTypeError(AdipoInsightError):
    def __init__(self, file_type: str, allowed: list):
        super().__init__(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            f"Unsupported file type '{file_type}'. Allowed: {allowed}",
            {"file_type": file_type, "allowed": allowed},
        )


class ModelServiceError(AdipoInsightError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(ErrorCode.MODEL_SERVICE_ERROR, message, details)


# ===== 错误响应构造 =====

def make_error_response(code: str, message: str, details: dict = None, request_id: str = "") -> dict:
    """构造统一错误响应"""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "request_id": request_id,
    }


def make_success_response(data: dict, request_id: str = "") -> dict:
    """构造统一成功响应"""
    return {
        "success": True,
        "data": data,
        "error": None,
        "request_id": request_id,
    }
