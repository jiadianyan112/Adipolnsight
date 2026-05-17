"""
统一错误处理测试 — 5 个错误场景
运行: python backend/app/ai/test_error_handling.py
"""

import backend.app.ai.skills  # noqa
from backend.app.errors import (
    ErrorCode,
    AdipoInsightError,
    InvalidInputError,
    JobNotFoundError,
    SkillNotAvailableError,
    ScriptExecutionError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    ModelServiceError,
    make_error_response,
    make_success_response,
    ERROR_HTTP_STATUS,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} — {detail}")


# ===== 场景 1: INVALID_INPUT =====
print("Scenario 1: INVALID_INPUT")
err = InvalidInputError("缺少 phenotype 参数", {"missing": ["phenotype"]})
check("error code", err.code == ErrorCode.INVALID_INPUT)
check("http status", err.http_status == 400)
check("message contains detail", "phenotype" in err.message)
check("details is dict", isinstance(err.details, dict))
resp = make_error_response(err.code, err.message, err.details)
check("response envelope", resp["success"] is False and resp["error"]["code"] == ErrorCode.INVALID_INPUT)

# ===== 场景 2: JOB_NOT_FOUND =====
print("\nScenario 2: JOB_NOT_FOUND")
err = JobNotFoundError("abc123def")
check("error code", err.code == ErrorCode.JOB_NOT_FOUND)
check("http status", err.http_status == 404)
check("job_id in message", "abc123def" in err.message)
check("job_id in details", err.details.get("job_id") == "abc123def")

# ===== 场景 3: SKILL_NOT_AVAILABLE + MODEL_SERVICE_ERROR =====
print("\nScenario 3: SKILL_NOT_AVAILABLE / MODEL_SERVICE_ERROR")
err = SkillNotAvailableError("image_segmentation")
check("skill not available", err.code == ErrorCode.SKILL_NOT_AVAILABLE)
check("http status 503", err.http_status == 503)

err = ModelServiceError("TSSA-UNet inference failed: CUDA OOM", {"gpu_memory_mb": 4096})
check("model service error", err.code == ErrorCode.MODEL_SERVICE_ERROR)
check("http status 502", err.http_status == 502)

# ===== 场景 4: 文件相关错误 =====
print("\nScenario 4: FILE_TOO_LARGE / UNSUPPORTED_FILE_TYPE")
err = FileTooLargeError(300_000_000, 209_715_200)
check("file too large", err.code == ErrorCode.FILE_TOO_LARGE)
check("http status 413", err.http_status == 413)
check("size in details", err.details["file_size"] == 300_000_000)

err = UnsupportedFileTypeError(".mp4", [".nii", ".nii.gz", ".dcm"])
check("unsupported type", err.code == ErrorCode.UNSUPPORTED_FILE_TYPE)
check("http status 415", err.http_status == 415)
check("file_type in details", err.details["file_type"] == ".mp4")

# ===== 场景 5: SCRIPT_EXECUTION_ERROR =====
print("\nScenario 5: SCRIPT_EXECUTION_ERROR")
err = ScriptExecutionError("GWAS script exit code 1: phenotype column not found", {"exit_code": 1})
check("script error", err.code == ErrorCode.SCRIPT_EXECUTION_ERROR)
check("http status 500", err.http_status == 500)
check("stderr in message", "exit code 1" in err.message)
check("exit_code in details", err.details["exit_code"] == 1)

# ===== 错误码覆盖检查 =====
print("\n=== Error Code Coverage ===")
all_codes = [v for k, v in ErrorCode.__dict__.items() if not k.startswith("_") and isinstance(v, str)]
mapped = sum(1 for c in all_codes if c in ERROR_HTTP_STATUS)
print(f"  Defined: {len(all_codes)} error codes")
print(f"  HTTP mapped: {mapped}/{len(all_codes)}")
check("all codes have HTTP status", mapped == len(all_codes),
      f"unmapped: {[c for c in all_codes if c not in ERROR_HTTP_STATUS]}")

# ===== 异常继承链 =====
print("\n=== Exception Hierarchy ===")
err = InvalidInputError("test")
check("InvalidInputError is AdipoInsightError", isinstance(err, AdipoInsightError))
check("AdipoInsightError is Exception", isinstance(err, Exception))
check("can catch as AdipoInsightError", True)

# ===== 成功响应 =====
print("\n=== Success Response ===")
resp = make_success_response({"job_id": "abc"})
check("success envelope", resp["success"] is True and resp["error"] is None)
check("data present", resp["data"]["job_id"] == "abc")

print(f"\n{'='*50}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'='*50}")
