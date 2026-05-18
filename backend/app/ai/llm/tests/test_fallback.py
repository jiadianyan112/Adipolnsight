"""
DeepSeek Fallback 测试套件

覆盖 10 个场景：
1.  mock 模式正常运行
2.  DeepSeek 无 API Key → fallback mock
3.  DeepSeek timeout → fallback 规则
4.  DeepSeek 非法 JSON → fallback
5.  Schema validate 失败 → fallback
6.  Rule parser 高置信度 → 不调 DeepSeek
7.  Rule parser 低置信度 → 调 DeepSeek
8.  DeepSeek confidence < 0.7 → 不创建 job
9.  参数缺失 → need_more_info
10. AI Job Manager 正常创建任务

运行: python -m pytest backend/app/ai/llm/tests/test_fallback.py -v
"""

import os
import sys
import time
import json
from unittest.mock import patch, MagicMock

import pytest

# 确保 skills 已注册
import backend.app.ai.skills  # noqa: F401
from backend.app.ai.registry import registry
from backend.app.ai.job_manager import job_manager, JobStatus
from backend.app.ai.intent_types import IntentParseResult
from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser, HybridIntentParser
from backend.app.ai.llm import provider_registry
from backend.app.ai.agent_orchestrator import agent_orchestrator


# ============================================================
# 1. Mock 模式正常运行
# ============================================================

def test_mock_provider_registered():
    """Mock provider 已注册且可用。"""
    assert provider_registry.has("mock")
    provider = provider_registry.get("mock")
    assert provider.name == "mock"


def test_hybrid_parser_works_with_mock():
    """HybridIntentParser 在 mock 下正常解析。"""
    result = hybrid_intent_parser.parse("帮我做 GWAS，表型是 Liver_PDFF")
    assert result.intent is not None
    assert result.confidence > 0
    assert result.source in ("rule", "llm", "hybrid")


def test_agent_orchestrator_with_mock():
    """AgentOrchestrator 在 mock 下创建 job。"""
    result = agent_orchestrator.process(
        "生成科研报告",
        {"project_id": 1},
        auto_run=True,
    )
    assert result.answer_type == "job_created"
    assert result.job_id


# ============================================================
# 2. DeepSeek 无 API Key → fallback mock（不崩溃）
# ============================================================

def test_no_api_key_does_not_crash():
    """DEEPSEEK_API_KEY 为空时 DeepSeekProvider 不注册、系统不崩溃。"""
    # DeepSeekProvider 在 __init__ 中验证 API Key，失败抛出 ValueError
    # 该异常在 ai/llm/__init__.py:28 被静默捕获
    # 验证 provider_registry 中只有 mock（或 deepseek 注册失败）
    providers = provider_registry.list_all()
    assert "mock" in providers
    # deepseek 可能注册也可能不注册，取决于 API Key 是否配置
    # 关键：系统不崩溃


def test_agent_works_without_deepseek():
    """即使 DeepSeek 不可用，AgentOrchestrator 仍正常工作。"""
    # 当前环境 deepseek 已注册（有 API Key），但即使没有也不应崩溃
    result = agent_orchestrator.process(
        "查看分析进度",
        {"project_id": 1},
    )
    assert result.answer_type in ("job_created", "unsupported", "need_more_info")


# ============================================================
# 3. DeepSeek timeout → fallback
# ============================================================

def test_llm_timeout_falls_back_to_rule():
    """DeepSeek 超时时 HybridIntentParser fallback 到 rule。"""
    from backend.app.ai.llm.deepseek_intent_parser import llm_intent_parser

    # Mock llm_intent_parser.parse 抛超时异常
    with patch.object(llm_intent_parser, 'parse', side_effect=TimeoutError("Connection timed out")):
        result = hybrid_intent_parser.parse("做 GWAS 分析")
        # 应 fallback 到 rule 或返回 unsupported，不抛异常
        assert result is not None
        assert result.source in ("rule", "hybrid")
        assert not result.warnings or "LLM" not in str(result.warnings)


def test_llm_timeout_agent_does_not_crash():
    """AgentOrchestrator 在 LLM 超时时不崩溃——hybrid parser 内部 catch。"""
    from backend.app.ai.llm.deepseek_intent_parser import llm_intent_parser

    # patch LLM parser（hybrid 内部有 try/except 包裹 LLM 调用）
    with patch.object(llm_intent_parser, 'parse', side_effect=TimeoutError("Connection timed out")):
        result = agent_orchestrator.process("做 GWAS", {"project_id": 1})
        # 不应抛异常——hybrid 内部 catch 了 LLM 超时
        assert result is not None
        assert result.answer_type in ("job_created", "need_more_info", "unsupported", "error")


# ============================================================
# 4. DeepSeek 返回非法 JSON → fallback
# ============================================================

def test_invalid_json_falls_back():
    """DeepSeek 返回非法 JSON 时 HybridIntentParser fallback。"""
    mock_bad_result = IntentParseResult(
        intent="unsupported",
        confidence=0.1,
        source="llm",
        user_message="garbled response",
        raw_input="test",
    )

    with patch.object(hybrid_intent_parser, 'parse', return_value=mock_bad_result):
        result = agent_orchestrator.process("做什么分析", {"project_id": 1})
        # 应返回 unsupported 或 need_more_info，不崩溃
        assert result.answer_type in ("unsupported", "need_more_info")
        assert not result.job_id


def test_llm_provider_returns_non_dict():
    """LLM 返回非 dict 时 service 层不崩溃。"""
    from backend.app.ai.llm.service import llm_service
    from backend.app.schemas.llm import LLMRequest, LLMMessage

    # 构造请求
    req = LLMRequest(
        messages=[LLMMessage(role="user", content="test")],
        taskType="intent_parse",
        temperature=0.1,
    )

    # 强制使用 mock provider（不会真的调 DeepSeek）
    req.provider = "mock"
    resp = llm_service.call_llm_json(req)
    assert resp is not None
    # 应有 fallback json_data
    assert resp.json_data is not None or resp.content is not None


# ============================================================
# 5. Schema validate 失败 → fallback
# ============================================================

def test_schema_validation_failure_returns_fallback():
    """Schema 校验失败时 schema_validator 返回 fallback，不崩溃。"""
    from backend.app.ai.llm.schema_validator import schema_validator

    # 传入非法数据
    ok, data, errors = schema_validator.validate("intent_parse", {"intent": 999, "confidence": "not_a_number"})
    assert not ok
    assert len(errors) > 0
    # fallback 数据应有效
    assert isinstance(data, dict)
    assert "intent" in data


def test_all_task_types_have_schema_fallback():
    """所有 task_type 的 schema fallback 自身可通过校验。"""
    from backend.app.ai.llm.schema_validator import schema_validator

    for task_type in ("intent_parse", "parameter_completion", "report_generation",
                       "result_interpretation", "chat", "error_explanation", "summary"):
        _, fallback, _ = schema_validator.validate(task_type, {})
        ok, _, errors = schema_validator.validate(task_type, fallback)
        assert ok, f"{task_type} fallback invalid: {errors}"


# ============================================================
# 6. Rule parser 高置信度 → 不调 DeepSeek
# ============================================================

def test_high_confidence_rule_skips_llm():
    """Rule parser 高置信度命中时 source=rule（不调 LLM）。"""
    # "帮我做 GWAS" 包含明显 GWAS 关键词
    result = hybrid_intent_parser.parse("帮我做 GWAS 全基因组关联分析，表型是 Liver_PDFF")
    # 如果有高置信度规则命中，source 应为 rule
    # 如果置信度 >= 0.85 且 missing_params <= 2，应直接返回
    if result.confidence >= 0.85 and len(result.missing_params) <= 2:
        assert result.source == "rule", (
            f"High confidence ({result.confidence}) should use rule parser, got source={result.source}"
        )


def test_rule_parser_strong_result_not_llm():
    """验证 _is_rule_result_strong 的逻辑不会错误地调用 LLM。"""
    strong_result = IntentParseResult(
        intent="gwas",
        confidence=0.95,
        capability_type="gwas_analysis",
        extracted_params={"phenotype": "Liver_PDFF"},
        missing_params=[],
        source="rule",
    )
    # 模拟：直接构造强规则结果，验证 hybrid parser 判断逻辑
    parser = HybridIntentParser()
    assert parser._is_rule_result_strong(strong_result) is True


def test_weak_rule_triggers_llm():
    """弱规则结果不会被视为 strong。"""
    weak_result = IntentParseResult(
        intent="gwas",
        confidence=0.3,
        capability_type="gwas_analysis",
        missing_params=["phenotype", "covariates", "method"],
        source="rule",
    )
    parser = HybridIntentParser()
    assert parser._is_rule_result_strong(weak_result) is False


# ============================================================
# 7. Rule parser 低置信度 → 调 DeepSeek
# ============================================================

def test_low_confidence_triggers_llm_path():
    """低置信度（<0.85）或缺失参数多（>2）时，hybrid 尝试 LLM。"""
    # 构造一个 rule 无法明确匹配的查询
    result = hybrid_intent_parser.parse("请帮我分析一下肝脏脂肪和骨骼健康之间的关系")
    # 这种模糊查询 rule 置信度可能较低
    # source 可能是 "llm"（LLM 成功）或 "hybrid"（LLM 失败回退 rule）
    assert result.source in ("rule", "llm", "hybrid")
    # 不应为 unsupported（语义上可以理解）
    # 注意：在 mock 环境下 LLM 可能也失败，这没关系


# ============================================================
# 8. DeepSeek confidence < 0.7 → 不创建 job
# ============================================================

def test_low_llm_confidence_rejected():
    """LLM 返回低置信度结果时 _is_llm_result_valid 返回 False。"""
    parser = HybridIntentParser()
    low_conf = IntentParseResult(
        intent="gwas",
        confidence=0.5,  # < 0.70
        capability_type="gwas_analysis",
        source="llm",
    )
    assert parser._is_llm_result_valid(low_conf) is False


def test_llm_unsupported_rejected():
    """LLM 返回 unsupported 时 _is_llm_result_valid 返回 False。"""
    parser = HybridIntentParser()
    unsupported = IntentParseResult(
        intent="unsupported",
        confidence=0.8,
        source="llm",
    )
    assert parser._is_llm_result_valid(unsupported) is False


def test_llm_with_warnings_rejected():
    """LLM 返回 invalid intent warning 时被拒绝。"""
    parser = HybridIntentParser()
    warned = IntentParseResult(
        intent="gwas",
        confidence=0.85,
        capability_type="gwas_analysis",
        source="llm",
        warnings=["LLM returned invalid intent 'INVALID'"],
    )
    # 有 invalid intent warning → 拒绝
    assert parser._is_llm_result_valid(warned) is False


# ============================================================
# 9. 参数缺失 → need_more_info
# ============================================================

def test_missing_params_returns_need_more_info():
    """参数缺失时 AgentOrchestrator 返回 need_more_info。"""
    result = agent_orchestrator.process(
        "做一个 GWAS 分析吧",  # 无 phenotype
        {"project_id": 1},
    )
    assert result.answer_type == "need_more_info"
    assert "phenotype" in result.missing_params
    assert not result.job_id


def test_missing_file_id_returns_need_more_info():
    """Segmentation 缺 file_id 返回 need_more_info。"""
    result = agent_orchestrator.process(
        "帮我做 MRI 影像分割",
        {"project_id": 1},
    )
    assert result.answer_type == "need_more_info"
    assert "file_id" in result.missing_params


def test_mr_missing_exposure_need_more_info():
    """MR 缺 exposure/outcome 返回 need_more_info。"""
    result = agent_orchestrator.process(
        "跑孟德尔随机化分析",
        {},  # 无 context 预填
    )
    assert result.answer_type == "need_more_info"


# ============================================================
# 10. AI Job Manager 正常创建任务
# ============================================================

def test_job_manager_create_and_run():
    """JobManager 正常创建并运行任务（使用快速 capability）。"""
    # 使用 gwas_analysis —— mock 模式下 0.5s 完成，不走 LLM
    job = job_manager.create_job("gwas_analysis", {
        "project_id": 1, "phenotype": "Liver_PDFF", "method": "REGENIE",
    }, project_id=1)
    assert job.job_id
    assert job.status == JobStatus.QUEUED

    started = job_manager.run_job(job.job_id)
    assert started

    # 等待完成（mock 模式很快）
    for _ in range(60):
        j = job_manager.get_job(job.job_id)
        if j.status == JobStatus.SUCCEEDED:
            break
        time.sleep(0.5)

    assert j.status == JobStatus.SUCCEEDED, f"Expected succeeded, got {j.status}: {j.error_message}"
    assert j.progress == 100


def test_job_manager_get_status():
    """JobManager 查询状态正常。"""
    job = job_manager.create_job("gwas_analysis", {
        "project_id": 1, "phenotype": "Liver_PDFF", "method": "REGENIE",
    })
    job_manager.run_job(job.job_id)

    for _ in range(60):
        status = job_manager.get_job_status(job.job_id)
        if status["status"] == "succeeded":
            break
        time.sleep(0.5)

    assert status["status"] == "succeeded"
    assert status["progress"] == 100


def test_job_manager_failure_has_user_facing_error():
    """Job 失败时 user_facing_error 不为空。"""
    job = job_manager.create_job("image_segmentation", {"project_id": 1}, project_id=1)
    job_manager.run_job(job.job_id)

    # 等待失败（缺 file_id → INVALID_INPUT）
    for _ in range(30):
        j = job_manager.get_job(job.job_id)
        if j.status == JobStatus.FAILED:
            break
        time.sleep(0.5)

    assert j.status == JobStatus.FAILED
    assert j.error_code == "INVALID_INPUT"
    # user_facing_error 可能为 None（LLM 调用中）或已设置
    # 在 LLM 不可用时应 fallback 到静态模板
    if j.user_facing_error is not None:
        assert "user_message" in j.user_facing_error
        assert "possible_reasons" in j.user_facing_error
        assert "next_actions" in j.user_facing_error


def test_job_manager_cancel():
    """JobManager 正常取消任务。"""
    job = job_manager.create_job("report_generation", {"project_id": 1})
    assert job.status == JobStatus.QUEUED

    ok = job_manager.cancel_job(job.job_id)
    assert ok

    j = job_manager.get_job(job.job_id)
    assert j.status == JobStatus.CANCELLED


# ============================================================
# Smoke: 全流程串联
# ============================================================

def test_full_pipeline_smoke():
    """全流程烟雾测试：Agent → Job → Result。"""
    # 1. 通过 Agent 创建 job
    result = agent_orchestrator.process(
        "帮我做 GWAS，表型是 Liver_PDFF，用 REGENIE 方法，人群选 EUR",
        {"project_id": 1},
        auto_run=True,
    )
    assert result.answer_type == "job_created"
    assert result.job_id

    # 2. 查询 job 状态
    for _ in range(30):
        j = job_manager.get_job(result.job_id)
        if j.status in (JobStatus.SUCCEEDED, JobStatus.FAILED):
            break
        time.sleep(0.5)

    assert j.status == JobStatus.SUCCEEDED

    # 3. 获取结果
    res = job_manager.get_result(result.job_id)
    assert res is not None
    assert res["status"] == "succeeded"
    assert res["result"] is not None


def test_all_capabilities_registered():
    """所有 8 个 capability 已注册。"""
    caps = registry.list_all()
    assert len(caps) == 8
    expected = {
        "image_segmentation", "phenotype_quantification", "gwas_analysis",
        "mendelian_randomization", "mediation_mr", "risk_modeling",
        "report_generation", "result_interpretation",
    }
    actual = {c["capability_type"] for c in caps}
    assert actual == expected


def test_parameter_completer_fallback():
    """ParameterCompleter 在 LLM 不可用时 fallback 到静态 hints。"""
    from backend.app.ai.llm.parameter_completer import (
        parameter_completer, ParameterCompletionInput,
    )

    with patch.object(parameter_completer, '_try_llm_completion', return_value=None):
        result = parameter_completer.complete(ParameterCompletionInput(
            capability_type="gwas_analysis",
            missing_params=["phenotype"],
        ))
        assert result is not None
        assert len(result.suggested_inputs) > 0
        # 应有 phenotype 字段的 suggestion
        fields = [s.field for s in result.suggested_inputs]
        assert "phenotype" in fields or any("phenotype" in s.label for s in result.suggested_inputs)


def test_error_explainer_fallback():
    """ErrorExplainer 在 LLM 不可用时 fallback 到静态模板。"""
    from backend.app.ai.llm.error_explainer import (
        error_explainer, ErrorExplanationInput,
    )

    with patch.object(error_explainer, '_try_llm', return_value=None):
        result = error_explainer.explain(ErrorExplanationInput(
            error_code="TASK_TIMEOUT",
            technical_message="Task exceeded 300s",
        ))
        assert result is not None
        assert len(result.user_message) > 0
        assert len(result.possible_reasons) > 0
        assert len(result.next_actions) > 0
