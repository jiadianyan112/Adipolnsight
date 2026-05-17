"""
LLM Provider 抽象层 + MockProvider + Registry

所有 LLM Provider 必须实现 LLMProvider 接口。
ProviderRegistry 管理注册和查找。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from backend.app.schemas.llm import (
    LLM_PROVIDER_NAME,
    LLMResponse,
    LLMError as LLMErrorSchema,
    LLMRequest,
    LLMResultInterpretation,
    LLMIntentResult,
    LLMErrorExplanation,
    LLMReportEnhancement,
)


# ===== 抽象接口 =====

class LLMProvider(ABC):
    """LLM Provider 抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称: 'mock' | 'deepseek' | 'openai'"""
        ...

    @abstractmethod
    def chat(self, request: LLMRequest) -> LLMResponse:
        """发送 chat completion 请求，返回文本"""
        ...

    def chat_json(self, request: LLMRequest, output_schema: Type = None) -> LLMResponse:
        """
        发送 chat completion 请求，返回解析后的 JSON。

        子类可重写以实现原生 JSON mode。
        """
        import json

        # 默认实现：强制要求 JSON 格式输出
        json_request = request.model_copy(update={"response_format": "json"})
        if request.response_format != "json":
            # 在 system prompt 末尾追加 JSON 格式要求
            if json_request.messages and json_request.messages[0].role == "system":
                original = json_request.messages[0].content
                json_request.messages[0].content = (
                    f"{original}\n\nYou MUST respond with valid JSON only. No markdown, no explanation."
                )

        response = self.chat(json_request)
        try:
            # 尝试提取 JSON（处理可能的 markdown code block）
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:]) if lines[0].startswith("```") else content
                if content.endswith("```"):
                    content = content[:-3]
            response.json_data = json.loads(content)
        except json.JSONDecodeError:
            response.json_data = None
        return response

    def stream_chat(self, request: LLMRequest):
        """
        流式 chat completion（预留接口）。
        子类实现时应 yield 增量内容。
        """
        raise NotImplementedError(f"{self.name} does not support streaming")


# ===== Mock Provider =====

class MockProvider(LLMProvider):
    """Mock LLM Provider — 本地开发用，不依赖外部 API"""

    @property
    def name(self) -> str:
        return "mock"

    def chat(self, request: LLMRequest) -> LLMResponse:
        time.sleep(0.05)
        text = self._mock_text_response(request)
        return LLMResponse(
            content=text,
            provider="mock",
            model="mock-v1",
            usage={"prompt_tokens": len(str(request.messages)) // 4,
                   "completion_tokens": len(text) // 4,
                   "total_tokens": 0},
        )

    def chat_json(self, request: LLMRequest, output_schema: Type = None) -> LLMResponse:
        time.sleep(0.05)
        json_data = self._mock_json_response(request)
        return LLMResponse(
            content=str(json_data),
            json_data=json_data,
            provider="mock",
            model="mock-v1",
        )

    def stream_chat(self, request: LLMRequest):
        time.sleep(0.05)
        yield self._mock_text_response(request)

    # ---- Mock 响应生成 ----

    def _mock_intent_from_input(self, request: LLMRequest) -> Dict[str, Any]:
        """简单的关键词匹配 mock（只检查 user messages，忽略 system prompt）"""
        text = " ".join(m.content for m in request.messages if m.role == "user").lower()
        # 按优先级匹配关键词
        checks = [
            ("segmentation", "image_segmentation", {"file_id": 0}),
            ("phenotype", "phenotype_quantification", {}),
            ("gwas", "gwas_analysis", {"phenotype": "Liver_PDFF", "method": "REGENIE"}),
            ("mediation_mr", "mediation_mr", {"mediator_source": "decode_plasma"}),
            ("mr", "mendelian_randomization", {"exposure": "Liver_PDFF", "outcome": "Osteoporosis"}),
            ("risk_modeling", "risk_modeling", {"exposure": "Liver_PDFF", "outcome": "Osteoporosis"}),
            ("report", "report_generation", {}),
            ("job_status", "", {}),
        ]
        keywords = {
            "segmentation": ["segmentation", "mri", "影像分割", "分割"],
            "phenotype": ["phenotype", "量化表型", "quantify fat", "表型量化"],
            "gwas": ["gwas", "全基因组", "曼哈顿"],
            "mr": ["mendelian randomization", "mr", "孟德尔"],
            "mediation_mr": ["mediation", "中介", "plasma protein", "pqTL"],
            "risk_modeling": ["risk", "风险", "预测模型", "quartile"],
            "report": ["report", "报告", "generate", "生成"],
            "job_status": ["status", "状态", "进度", "check"],
        }
        for intent, cap, params in checks:
            for kw in keywords.get(intent, []):
                if kw in text:
                    return {
                        "intent": intent,
                        "confidence": 0.85,
                        "capabilityType": cap,
                        "extractedParams": params,
                        "missingParams": [],
                        "nextAction": "create_job",
                        "userMessage": f"Matched intent: {intent} (keyword: {kw})",
                    }
        return {
            "intent": "unsupported",
            "confidence": 0.1,
            "capabilityType": "",
            "extractedParams": {},
            "missingParams": [],
            "nextAction": "clarify",
            "userMessage": "Unable to identify intent from input",
        }

    def _mock_text_response(self, request: LLMRequest) -> str:
        task = request.task_type
        if task == "intent_parse":
            return "已识别意图：GWAS 分析"
        elif task == "result_interpretation":
            return "分析结果显示，肝脏 PDFF 与骨质疏松风险存在显著正相关..."
        elif task == "report_generation":
            return "## 讨论\n\n本研究综合多组学证据..."
        elif task == "error_explanation":
            return "该错误由任务超时引起，建议减少样本量后重试。"
        elif task == "chat":
            return "您好！我是 AdipoInsight AI 助手。请描述您想要执行的分析任务。"
        elif task == "summary":
            return "本项目已完成影像分割、GWAS 和 MR 分析..."
        else:
            return f"Mock response for task: {task}"

    def _mock_json_response(self, request: LLMRequest) -> Dict[str, Any]:
        task = request.task_type
        if task == "intent_parse":
            return self._mock_intent_from_input(request)
        elif task == "result_interpretation":
            return {
                "capability_type": "gwas_analysis",
                "summary": "GWAS 识别 18 个显著基因座，λ_GC=1.003 表明无系统性偏倚",
                "key_findings": [
                    "肝脏 PDFF 与 18 个基因组区域显著关联",
                    "先导 SNP rs1001 位于染色体 3p21",
                    "λ_GC=1.003 表明群体分层控制良好",
                ],
                "clinical_significance": "这些基因座可能作为 NAFLD 相关骨病的生物标志物",
                "limitations": ["样本限于 EUR 人群", "使用 Mock 数据"],
                "suggested_next_steps": ["在独立队列中验证", "进行功能注释和共定位分析"],
            }
        elif task == "error_explanation":
            return {
                "error_code": "TASK_TIMEOUT",
                "friendly_message": "任务执行超时（超过 300 秒）",
                "possible_causes": [
                    "输入数据量过大",
                    "计算资源不足",
                    "脚本陷入死循环",
                ],
                "suggested_actions": [
                    "减少样本量或 SNP 数量",
                    "检查脚本日志排查问题",
                    "联系管理员增加计算资源",
                ],
                "is_retryable": True,
            }
        elif task == "report_generation":
            return {
                "discussion_section": "## 讨论\n\n本研究综合多组学证据...",
                "conclusion_section": "## 结论\n\n肝脏 PDFF 是骨质疏松的独立风险因子...",
                "clinical_implications": "建议将 PDFF=10% 作为临床筛查阈值",
                "future_directions": "在独立队列中验证 POR/NAAA 中介机制",
                "abstract": "背景: NAFLD 与骨质疏松的因果关系不明...",
            }
        elif task == "parameter_completion":
            return {
                "phenotype": "Liver_PDFF",
                "covariates": ["age", "sex", "bmi", "PC1-PC10"],
                "population_filter": "EUR",
            }
        elif task == "chat":
            return {
                "reply": "您好！我可以帮您执行 GWAS、MR、中介分析等任务。请告诉我您想做什么？",
                "suggested_actions": ["run_gwas", "run_mr", "generate_report"],
            }
        elif task == "summary":
            return {
                "summary": "本项目已完成 5 项分析：影像分割、GWAS、MR、中介 MR、风险建模",
                "completed": 5,
                "total": 7,
                "next": "建议运行报告生成",
            }
        return {"mock": True, "task_type": task}


# ===== Provider Registry =====

class ProviderRegistry:
    """LLM Provider 注册表"""

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._default_name: str = "mock"

    def register(self, provider: LLMProvider) -> None:
        name = provider.name
        if name in self._providers:
            print(f"[ProviderRegistry] WARNING: Overwriting provider '{name}'")
        self._providers[name] = provider
        print(f"[ProviderRegistry] Registered provider: {name}")

    def get(self, name: str) -> Optional[LLMProvider]:
        return self._providers.get(name)

    def get_default(self) -> LLMProvider:
        return self._providers.get(self._default_name) or list(self._providers.values())[0]

    def set_default(self, name: str) -> None:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered. Available: {list(self._providers.keys())}")
        self._default_name = name

    def has(self, name: str) -> bool:
        return name in self._providers

    def list_all(self) -> List[str]:
        return list(self._providers.keys())


# 全局单例
provider_registry = ProviderRegistry()
provider_registry.register(MockProvider())
