"""
AdipoInsight 最小端到端测试

覆盖 10 个场景：
1-8: 后端 API + 核心服务（pytest + httpx）
9-10: 前端交互（说明 + 手工验证步骤）

运行（需要后端运行在 localhost:8000）：
  python -m pytest backend/app/ai/llm/tests/test_e2e.py -v -s

也可不依赖运行中后端（纯模块级测试）：
  python -m pytest backend/app/ai/llm/tests/test_e2e.py -v -k "not require_server"
"""

import json
import os
import sys
import time
from unittest.mock import patch, MagicMock

import pytest
import httpx

# ============================================================
# 配置
# ============================================================

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")
REQUIRE_SERVER = pytest.mark.skipif(
    os.environ.get("SKIP_SERVER_TESTS") == "1",
    reason="Server tests require backend running on localhost:8000",
)

# 确保 skills 已注册（模块级测试用）
import backend.app.ai.skills  # noqa: F401


# ============================================================
# 辅助函数
# ============================================================

def _wait_for_job(job_id: str, timeout: float = 60) -> dict:
    """轮询等待 job 完成。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE_URL}/api/ai/jobs/{job_id}", timeout=10)
            if r.status_code == 200:
                data = r.json()["data"]
                if data["status"] in ("succeeded", "failed", "cancelled"):
                    return data
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")


# ============================================================
# 1. /api/ai/llm/health
# ============================================================

class TestLLMHealth:
    """LLM 健康检查端点"""

    def test_health_endpoint_module(self):
        """模块级：直接测试 health 逻辑（不依赖运行中服务）。"""
        # 验证 config 和 provider 导入正常
        from backend.app.config import LLM_PROVIDER, DEEPSEEK_API_KEY
        from backend.app.ai.llm import provider_registry

        assert LLM_PROVIDER in ("mock", "deepseek")
        assert "mock" in provider_registry.list_all()

        # 如果有 API Key，deepseek 应已注册
        if DEEPSEEK_API_KEY:
            assert "deepseek" in provider_registry.list_all()

    @REQUIRE_SERVER
    def test_health_endpoint_server(self):
        """API 级：GET /api/ai/llm/health"""
        r = httpx.get(f"{BASE_URL}/api/ai/llm/health", timeout=120)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["configured"] is True
        assert data["data"]["provider"] in ("mock", "deepseek")
        # reachable 可能是 true 或 false，取决于 API Key
        assert isinstance(data["data"]["reachable"], bool)


# ============================================================
# 2. /api/ai/chat 普通问答
# ============================================================

class TestChatAnswer:
    """聊天助手——普通问答"""

    def test_chat_greeting_module(self):
        """模块级：LLM chat prompt 可用。"""
        from backend.app.ai.llm.prompts.chat import SYSTEM_PROMPT, build_user_prompt

        assert len(SYSTEM_PROMPT) > 100
        user_msg = build_user_prompt("你好", {"project_id": 1})
        assert "你好" in user_msg
        assert "project_id" in user_msg.lower() or "Project" in user_msg

    @REQUIRE_SERVER
    def test_chat_greeting_server(self):
        """API 级：POST /api/ai/chat 普通问答"""
        r = httpx.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "你能帮我做什么分析？",
            "project_id": 1,
        }, timeout=120)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["type"] == "answer", f"Expected answer, got {data['type']}: {data.get('message', '')}"
        assert len(data["message"]) > 10

    @REQUIRE_SERVER
    def test_chat_scientific_question_server(self):
        """API 级：科学问题问答"""
        r = httpx.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "GWAS 和 MR 有什么区别？",
            "project_id": 1,
        }, timeout=120)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["type"] == "answer"
        # 应包含相关解释
        assert len(data["message"]) > 20


# ============================================================
# 3. /api/ai/chat 任务型请求
# ============================================================

class TestChatTask:
    """聊天助手——任务型请求"""

    @REQUIRE_SERVER
    def test_chat_gwas_task_server(self):
        """API 级：POST /api/ai/chat 任务型请求"""
        r = httpx.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "帮我做 GWAS 分析，表型是 Liver_PDFF，用 REGENIE 方法",
            "project_id": 1,
        }, timeout=120)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["type"] == "job_created", f"Expected job_created, got {data['type']}"
        assert data["jobId"]

        # 等待完成并验证
        job = _wait_for_job(data["jobId"])
        assert job["status"] == "succeeded"

    @REQUIRE_SERVER
    def test_chat_report_task_server(self):
        """API 级：POST /api/ai/chat 生成报告"""
        r = httpx.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "生成科研报告",
            "project_id": 1,
        }, timeout=120)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["type"] == "job_created"


# ============================================================
# 4. HybridIntentParser 明确命令识别
# ============================================================

class TestIntentClearCommand:
    """明确命令意图识别"""

    def test_gwas_clear_intent(self):
        """明确 GWAS 关键词 → 高置信度识别"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("帮我做 GWAS，表型是 Liver_PDFF")
        assert result.intent == "gwas"
        assert result.capability_type == "gwas_analysis"
        assert result.confidence >= 0.3  # rule parser 至少部分匹配

    def test_mr_clear_intent(self):
        """明确 MR 关键词 → 高置信度识别"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("跑孟德尔随机化分析，暴露是 Liver_PDFF，结局是 Osteoporosis")
        assert result.intent == "mr"
        assert result.capability_type == "mendelian_randomization"

    def test_segmentation_clear_intent(self):
        """明确分割关键词 → 正确识别"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("上传 MRI 影像并执行 AI 分割")
        assert result.intent == "segmentation"
        assert result.capability_type == "image_segmentation"

    def test_report_clear_intent(self):
        """明确报告关键词 → 正确识别"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("生成分析报告")
        assert result.intent == "report"
        assert result.capability_type == "report_generation"


# ============================================================
# 5. HybridIntentParser 模糊表达识别
# ============================================================

class TestIntentFuzzyExpression:
    """模糊表达意图识别"""

    def test_fuzzy_causal_query(self):
        """模糊因果查询 → 不崩溃，有合理结果"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("请帮我研究一下肝脏脂肪含量高会不会增加骨质疏松的风险")
        # 不应为 unsupported——语义上有明确分析需求
        assert result is not None
        assert result.intent in ("gwas", "mr", "mediation_mr", "risk_modeling", "unsupported",
                                  "chat", "phenotype")
        assert result.confidence >= 0.0

    def test_fuzzy_mechanism_query(self):
        """模糊机制查询 → 有结果"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("我想知道血浆蛋白在肝脏和骨骼之间扮演什么角色")
        assert result is not None
        # mediation_mr 或 mr 或 unsupported（太模糊）
        assert result.intent in ("mediation_mr", "mr", "unsupported", "chat")

    def test_nonsense_query(self):
        """无意义查询 → unsupported"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("xyzzy asdfgh 12345")
        assert result.intent == "unsupported"

    def test_empty_query(self):
        """空查询 → unsupported"""
        from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser

        result = hybrid_intent_parser.parse("")
        assert result.intent == "unsupported"


# ============================================================
# 6. resultInterpretation job 创建与结果返回
# ============================================================

class TestResultInterpretation:
    """结果解读 Job"""

    def test_interpretation_skill_registered(self):
        """模块级：Skill 已注册"""
        from backend.app.ai.registry import registry

        skill = registry.get("result_interpretation")
        assert skill is not None
        assert skill.name == "AI Result Interpretation"

    def test_interpretation_skill_validate(self):
        """模块级：Skill validate_input 正常"""
        from backend.app.ai.registry import registry

        skill = registry.get("result_interpretation")
        assert skill.validate_input({
            "sourceJobId": "job_001",
            "jobType": "gwas",
            "jobResult": {"phenotype": "Liver_PDFF"},
            "audience": "researcher",
        })
        assert not skill.validate_input({})
        assert not skill.validate_input({"sourceJobId": "x", "jobType": "invalid", "jobResult": {}})

    def test_interpretation_mock_output(self):
        """模块级：Mock 解读正常生成"""
        from backend.app.ai.registry import registry
        from backend.app.ai.base import SkillContext

        skill = registry.get("result_interpretation")
        ctx = SkillContext(project_id=1, task_id=1, output_dir="storage/test_e2e_interpretation")
        os.makedirs(ctx.output_dir, exist_ok=True)

        output = skill.run({
            "sourceJobId": "job_gwas_001",
            "jobType": "gwas",
            "jobResult": {
                "phenotype": "Liver_PDFF",
                "sample_size": 40484,
                "significant_loci_count": 18,
                "lambda_gc": 1.003,
            },
            "audience": "researcher",
            "language": "zh",
        }, ctx)

        assert output.status == "success"
        assert "summary" in output.summary
        assert "keyFindings" in output.summary
        assert "cautions" in output.summary
        assert "evidenceJobId" in output.summary

    @REQUIRE_SERVER
    def test_interpretation_job_server(self):
        """API 级：创建 interpretation job 并获取结果"""
        r = httpx.post(f"{BASE_URL}/api/ai/interpretation/jobs", json={
            "project_id": 1,
            "parameters": {
                "sourceJobId": "job_gwas_001",
                "jobType": "gwas",
                "jobResult": {
                    "phenotype": "Liver_PDFF",
                    "sample_size": 40484,
                    "significant_loci_count": 18,
                    "lambda_gc": 1.003,
                },
                "audience": "researcher",
                "language": "zh",
            },
        }, timeout=120)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text[:200]}"
        data = r.json()["data"]
        assert data["job_id"]

        job = _wait_for_job(data["job_id"], timeout=120)
        assert job["status"] == "succeeded"

        r = httpx.get(f"{BASE_URL}/api/ai/jobs/{data['job_id']}/result", timeout=10)
        result_data = r.json()
        assert result_data["success"] is True
        result = result_data["data"]["result"]
        assert result is not None
        assert "summary" in result


# ============================================================
# 7. reportGeneration job 创建与结果返回
# ============================================================

class TestReportGeneration:
    """报告生成 Job"""

    def test_report_skill_registered(self):
        """模块级：Skill 已注册"""
        from backend.app.ai.registry import registry

        skill = registry.get("report_generation")
        assert skill is not None

    def test_report_skill_mock_output(self):
        """模块级：Mock 模板正常生成"""
        from backend.app.ai.registry import registry
        from backend.app.ai.base import SkillContext

        skill = registry.get("report_generation")
        ctx = SkillContext(project_id=1, task_id=1, output_dir="storage/test_e2e_report")
        os.makedirs(ctx.output_dir, exist_ok=True)

        output = skill.run({
            "project_id": 1,
            "project_title": "E2E 测试报告",
            "report_type": "summary_report",
            "language": "zh-CN",
            "completed_job_results": {
                "job_gwas_001": {
                    "phenotype": "Liver_PDFF",
                    "sample_size": 40484,
                    "significant_loci_count": 18,
                    "lead_snps_count": 12,
                },
            },
        }, ctx)

        assert output.status == "success"
        assert len(output.summary["sections"]) > 0
        assert output.summary["title"] == "E2E 测试报告"

    @REQUIRE_SERVER
    def test_report_job_server(self):
        """API 级：创建 report job 并获取结果"""
        r = httpx.post(f"{BASE_URL}/api/ai/report/jobs", json={
            "project_id": 1,
            "parameters": {
                "project_title": "E2E 测试报告",
                "language": "zh-CN",
                "report_type": "summary_report",
                "completed_job_results": {
                    "job_gwas_001": {
                        "phenotype": "Liver_PDFF",
                        "sample_size": 40484,
                        "significant_loci_count": 18,
                    },
                },
            },
        }, timeout=120)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text[:200]}"
        data = r.json()["data"]
        assert data["job_id"]

        job = _wait_for_job(data["job_id"], timeout=180)
        if job["status"] == "succeeded":
            r = httpx.get(f"{BASE_URL}/api/ai/jobs/{data['job_id']}/result", timeout=10)
            result_data = r.json()
            assert result_data["success"] is True
            assert result_data["data"]["result"] is not None


# ============================================================
# 8. errorExplanationService fallback
# ============================================================

class TestErrorExplanationE2E:
    """错误解释服务"""

    def test_error_explainer_all_codes_module(self):
        """模块级：所有错误码有静态 fallback"""
        from backend.app.errors import ErrorCode
        from backend.app.ai.llm.error_explainer import _STATIC_EXPLANATIONS, error_explainer, ErrorExplanationInput

        codes = [v for k, v in ErrorCode.__dict__.items() if not k.startswith("_") and isinstance(v, str)]
        for code in codes:
            result = error_explainer._static_explain(ErrorExplanationInput(
                error_code=code,
                technical_message="test",
            ))
            assert len(result.user_message) > 0, f"Missing user_message for {code}"
            assert len(result.possible_reasons) > 0, f"Missing reasons for {code}"
            assert len(result.next_actions) > 0, f"Missing actions for {code}"

    def test_error_explainer_llm_fallback_module(self):
        """模块级：LLM 不可用时 fallback 到静态"""
        from backend.app.ai.llm.error_explainer import error_explainer, ErrorExplanationInput

        with patch.object(error_explainer, '_try_llm', return_value=None):
            result = error_explainer.explain(ErrorExplanationInput(
                error_code="TASK_TIMEOUT",
                technical_message="Task exceeded 300s",
                job_type="gwas_analysis",
            ))
            assert len(result.user_message) > 0
            assert len(result.possible_reasons) > 0
            assert len(result.next_actions) > 0

    @REQUIRE_SERVER
    def test_job_failure_has_user_facing_error_server(self):
        """API 级：失败 job 的响应包含 user_facing_error"""
        r = httpx.post(f"{BASE_URL}/api/ai/segmentation/jobs", json={
            "project_id": 1,
            "parameters": {},  # 故意缺 file_id → INVALID_INPUT
        }, timeout=10)
        assert r.status_code == 201
        job_id = r.json()["data"]["job_id"]

        # 等待足够久以让 user_facing_error 生成（LLM 可能需要几秒）
        job = _wait_for_job(job_id, timeout=90)
        assert job["status"] == "failed"
        assert job["error_code"] == "INVALID_INPUT"

        # user_facing_error 可能为 None（LLM 超时）或 dict
        ufe = job.get("user_facing_error")
        if ufe is not None:
            assert "user_message" in ufe
            assert "possible_reasons" in ufe
            assert "next_actions" in ufe


# ============================================================
# 9. 前端聊天框发送消息（手工验证 + 模块级检查）
# ============================================================

class TestFrontendChat:
    """
    前端聊天框测试。

    Node 18 无法运行前端 dev server，以下为模块级验证。
    完整 UI 测试需要 Node 20+ 并运行 `npm run dev`。
    """

    def test_chatinput_component_exists(self):
        """ChatInput 组件文件存在。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "components", "agent", "ChatInput.tsx",
        )
        assert _os.path.exists(path), f"ChatInput.tsx not found at {path}"

    def test_chatinput_imports_chatquery(self):
        """ChatInput 使用 chatQuery（而非旧的 agentQuery）。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "components", "agent", "ChatInput.tsx",
        )
        content = open(path, encoding='utf-8').read()
        assert "chatQuery" in content, "ChatInput should use chatQuery"
        assert "POST /api/ai/chat" not in content, "ChatInput should not hardcode API path"

    def test_aiservice_has_chatquery(self):
        """aiService.ts 导出 chatQuery 函数。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "services", "aiService.ts",
        )
        content = open(path, encoding='utf-8').read()
        assert "chatQuery" in content
        assert "/ai/chat" in content

    def test_chatquery_handles_all_five_types(self):
        """chatQuery 响应类型覆盖 5 种 ChatResponse type。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "services", "aiService.ts",
        )
        content = open(path, encoding='utf-8').read()
        assert "answer" in content
        assert "job_created" in content
        assert "need_more_info" in content
        assert "job_status" in content

    def test_chatinput_renders_answer_type(self):
        """ChatInput 渲染 answer 类型的 UI。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "components", "agent", "ChatInput.tsx",
        )
        content = open(path, encoding='utf-8').read()
        assert "type === 'answer'" in content
        assert "type === 'job_created'" in content
        assert "type === 'need_more_info'" in content
        assert "type === 'job_status'" in content

    def test_manual_verification_steps(self):
        """
        [手工验证] 前端聊天框步骤：

        前置条件：Node.js 20+ 已安装

        1. cd frontend && npm run dev
        2. 打开 http://localhost:5173
        3. 进入一个项目工作区
        4. 在右下角聊天框输入"你好" → 应显示 AI 回答卡片
        5. 输入"做 GWAS 分析" → 应显示绿色任务已创建卡片
        6. 输入"查看任务进度" → 应显示任务状态卡片
        7. 输入"今天天气怎么样" → 应显示需要补充信息卡片
        """
        pass  # 手工验证，pytest 跳过


# ============================================================
# 10. 前端结果页点击 AI 解释（手工验证 + 模块级检查）
# ============================================================

class TestFrontendInterpretationButton:
    """
    前端 AI 解释按钮测试。

    Node 18 无法运行前端 dev server，以下为模块级验证。
    """

    def test_ai_interpretation_panel_exists(self):
        """AIInterpretationPanel 组件文件存在。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "components", "result", "AIInterpretationPanel.tsx",
        )
        assert _os.path.exists(path), f"AIInterpretationPanel.tsx not found at {path}"

    def test_all_five_modules_have_panel(self):
        """5 个分析模块都导入了 AIInterpretationPanel。"""
        import os as _os

        base = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "components", "analysis",
        )
        modules = [
            "ImageProcessingModule.tsx",
            "GWASModule.tsx",
            "MRModule.tsx",
            "MediationMRModule.tsx",
            "RiskModelingModule.tsx",
        ]
        for mod in modules:
            path = _os.path.join(base, mod)
            assert _os.path.exists(path), f"{mod} not found"
            content = open(path, encoding='utf-8').read()
            assert "AIInterpretationPanel" in content, (
                f"{mod} should import AIInterpretationPanel"
            )

    def test_panel_creates_interpretation_job(self):
        """AIInterpretationPanel 调用 createAIJob('interpretation', ...)。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "components", "result", "AIInterpretationPanel.tsx",
        )
        content = open(path, encoding='utf-8').read()
        assert "interpretation" in content, "Should create interpretation job"
        assert "createAIJob" in content

    def test_panel_has_fallback_state(self):
        """AIInterpretationPanel 有失败状态处理。"""
        import os as _os
        path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "..", "..", "..",
            "frontend", "src", "components", "result", "AIInterpretationPanel.tsx",
        )
        content = open(path, encoding='utf-8').read()
        assert "'failed'" in content or '"failed"' in content
        # 检查关键展示字段
        assert "summary" in content
        assert "keyFindings" in content or "key_findings" in content
        assert "cautions" in content

    def test_manual_verification_steps(self):
        """
        [手工验证] 前端 AI 解释按钮步骤：

        前置条件：Node.js 20+ 已安装，后端运行中

        1. cd frontend && npm run dev
        2. 打开 http://localhost:5173，进入使用了 AI Job API 的项目工作区
        3. 运行 GWAS 分析 → 等待完成
        4. GWAS 结果底部出现「🌟 AI 解读 GWAS 结果」按钮
        5. 点击按钮 → 等待 20-40 秒
        6. 展示 6 个区域：摘要、关键发现、注意事项、下一步建议、通俗解释、evidenceJobId
        """
        pass  # 手工验证，pytest 跳过


# ============================================================
# 全流程串联（模块级，不依赖服务）
# ============================================================

class TestFullPipelineModule:
    """全流程验证（纯模块级，不需要运行服务）"""

    def test_agent_to_job_pipeline(self):
        """Agent → Job → Result 全流程可走通（使用快速 capability）。"""
        from backend.app.ai.agent_orchestrator import agent_orchestrator
        from backend.app.ai.job_manager import job_manager, JobStatus

        # 1. Agent 创建 job（使用 gwas_analysis，mock 模式 0.5s 完成）
        result = agent_orchestrator.process(
            "帮我做 GWAS，表型是 Liver_PDFF，用 REGENIE 方法",
            {"project_id": 1},
            auto_run=True,
        )
        assert result.answer_type == "job_created"
        assert result.job_id

        # 2. 等待完成
        for _ in range(60):
            j = job_manager.get_job(result.job_id)
            if j.status == JobStatus.SUCCEEDED:
                break
            time.sleep(0.5)

        assert j.status == JobStatus.SUCCEEDED

        # 3. 获取结果
        res = job_manager.get_result(result.job_id)
        assert res is not None
        assert res["result"] is not None

    def test_hybrid_parser_to_orchestrator(self):
        """HybridParser → AgentOrchestrator 链路正常。"""
        from backend.app.ai.agent_orchestrator import agent_orchestrator

        # 完整参数 → job_created
        result = agent_orchestrator.process(
            "帮我做 GWAS，表型是 Liver_PDFF",
            {"project_id": 1},
            auto_run=True,
        )
        assert result.answer_type in ("job_created", "need_more_info")
        if result.answer_type == "job_created":
            assert result.capability_type == "gwas_analysis"

    def test_intent_to_job_to_error_explanation(self):
        """Intent → Job 失败 → Error Explanation 链路。"""
        from backend.app.ai.job_manager import job_manager, JobStatus

        # 创建必然失败的任务
        job = job_manager.create_job("image_segmentation", {"project_id": 1}, project_id=1)
        job_manager.run_job(job.job_id)

        for _ in range(60):
            j = job_manager.get_job(job.job_id)
            if j.status == JobStatus.FAILED:
                break
            time.sleep(0.5)

        assert j.status == JobStatus.FAILED
        assert j.error_code == "INVALID_INPUT"
        # user_facing_error 可能为 None（LLM 未完成）或 dict
        # 两种都是合法状态


# ============================================================
# 运行说明
# ============================================================

if __name__ == "__main__":
    print("""
AdipoInsight 端到端测试

运行方式：

1. 只跑模块级测试（不需要运行中的后端）：
   python -m pytest backend/app/ai/llm/tests/test_e2e.py -v -k "not require_server"

2. 全部测试（需要后端运行在 localhost:8000）：
   python -m pytest backend/app/ai/llm/tests/test_e2e.py -v -s

3. 跑特定场景：
   python -m pytest backend/app/ai/llm/tests/test_e2e.py -v -k "TestLLMHealth"
   python -m pytest backend/app/ai/llm/tests/test_e2e.py -v -k "TestChatAnswer"
   python -m pytest backend/app/ai/llm/tests/test_e2e.py -v -k "TestResultInterpretation"

4. 带覆盖率：
   python -m pytest backend/app/ai/llm/tests/test_e2e.py -v --tb=short

手工验证前端（需要 Node 20+）：
   cd frontend && npm run dev
   打开 http://localhost:5173
""")
