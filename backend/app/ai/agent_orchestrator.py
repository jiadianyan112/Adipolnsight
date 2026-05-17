"""
Agent Orchestrator — 自然语言 → AI Job 编排

连接 Intent Parser + AI Skill Registry + Job Manager，
实现从用户自然语言 query 到 AI 分析任务创建的全链路。

约束：
- 不直接生成分析结果（结果由 Skill Adapter 产生）
- 不替换 Intent Parser 的意图识别
- 参数不足时返回补全指引，不猜测参数

用法：
    from backend.app.ai.agent_orchestrator import agent_orchestrator

    result = agent_orchestrator.process(
        query="帮我做 GWAS，表型是 Liver PDFF",
        context={"project_id": 1, "exposure": "Liver_PDFF"},
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

import backend.app.ai.skills  # noqa: F401 — 确保所有 Skill 已注册
from backend.app.ai.llm.hybrid_intent_parser import hybrid_intent_parser
from backend.app.ai.intent_parser import IntentParseResult as IntentResult
from backend.app.ai.registry import registry as skill_registry
from backend.app.ai.job_manager import job_manager

logger = logging.getLogger("adipoinsight.agent_orchestrator")

# ===== 输出结构 =====

AnswerType = Literal[
    "job_created",       # 参数齐全，任务已创建并启动
    "need_more_info",    # 参数不足，需要用户补充
    "unsupported",       # 意图无法识别或能力未注册
    "error",             # 执行异常
]


@dataclass
class NextAction:
    """建议的下一步操作"""
    label: str                               # 按钮/链接文字
    action: str                              # "create_job" | "provide_param" | "view_result" | "retry"
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorResult:
    """Agent Orchestrator 输出"""
    answer_type: AnswerType
    message: str                             # 人类可读响应
    capability_type: str = ""                # 匹配到的能力类型
    job_id: str = ""                         # 创建成功后的 job ID
    job_status: str = ""                     # queued / running
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    missing_params: List[str] = field(default_factory=list)
    clarification_question: str = ""         # need_more_info 时的追问
    next_actions: List[NextAction] = field(default_factory=list)
    intent_confidence: float = 0.0
    raw_query: str = ""


# ===== 参数补全策略 =====

# 各 capability 的推荐默认值和提示
PARAM_HINTS: Dict[str, Dict[str, Any]] = {
    "image_segmentation": {
        "required": ["project_id", "file_id"],
        "hints": {
            "file_id": "请先上传 MRI 影像文件",
            "modality": "MRI（默认）或 CT",
            "target_structures": "肝脏(liver)、胰腺(pancreas)、内脏脂肪(visceral_fat)、皮下脂肪(subcutaneous_fat)、骨髓(bone_marrow)",
            "model_name": "TSSA-UNet（默认）",
        },
    },
    "phenotype_quantification": {
        "required": ["project_id"],
        "hints": {
            "segmentation_job_id": "可指定已有分割任务 ID，留空则自动查找",
        },
    },
    "gwas_analysis": {
        "required": ["project_id", "phenotype"],
        "hints": {
            "phenotype": "表型名称，如 Liver_PDFF",
            "covariates": "协变量列表，如 age, sex, bmi, PC1-PC10",
            "population_filter": "EUR / EAS / AFR / SAS / AMR",
            "method": "REGENIE（默认）/ PLINK2 / SAIGE",
        },
    },
    "mendelian_randomization": {
        "required": ["project_id", "exposure", "outcome"],
        "hints": {
            "exposure": "暴露因素名称",
            "outcome": "结局变量名称",
            "outcome_dataset_id": "OpenGWAS ID，如 ukb-b-12141",
            "methods": "IVW, MR-Egger, Weighted Median, Weighted Mode",
        },
    },
    "mediation_mr": {
        "required": ["project_id", "exposure", "outcome", "mediator_source"],
        "hints": {
            "exposure": "暴露因素名称",
            "outcome": "结局变量名称",
            "mediator_source": "decode_plasma / metabolite_gwas / gwas_catalog / custom",
            "candidate_proteins": "候选蛋白列表，默认 ACY1, H6PD, SHBG, ADH1A, POR, NAAA",
        },
    },
    "risk_modeling": {
        "required": ["project_id", "exposure", "outcome"],
        "hints": {
            "exposure": "暴露因素名称",
            "outcome": "结局变量名称",
            "outcomes": "BMD, TBS, Osteopenia, Osteoporosis",
            "model_types": "OLS, RCS, MultinomialLogistic",
            "grouping": "quartile / tertile / median",
        },
    },
    "report_generation": {
        "required": ["project_id"],
        "hints": {
            "title": "报告标题（可选）",
            "language": "zh-CN（默认）/ en",
            "sections": "指定包含的章节（可选）",
        },
    },
}


# ===== Agent Orchestrator =====

class AgentOrchestrator:
    """
    自然语言 → AI Job 编排器

    不生成分析结果。分析结果由 Skill Adapter → JobManager → SkillRegistry 产生。
    编排器只负责：意图识别 → 参数校验 → 任务创建。
    """

    def __init__(self):
        self._intent_parser = hybrid_intent_parser
        self._registry = skill_registry
        self._job_manager = job_manager

    # ===== 主入口 =====

    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        auto_run: bool = True,
    ) -> OrchestratorResult:
        """
        处理用户自然语言 query。

        Args:
            query: 用户输入的自然语言文本
            context: 当前上下文，可包含 project_id, exposure, outcome 等预填参数
            auto_run: True 时参数齐全自动创建并运行 Job

        Returns:
            OrchestratorResult
        """
        ctx = context or {}
        project_id = ctx.get("project_id", 0)

        # 1. 意图识别
        intent_result = self._intent_parser.parse(query)

        # 2. 不可识别 → unsupported
        if intent_result.intent == "unsupported":
            return self._make_unsupported(intent_result)

        cap_type = intent_result.capability_type

        # 3. Skill 未注册 → unsupported
        if cap_type and not self._registry.has(cap_type):
            return OrchestratorResult(
                answer_type="unsupported",
                message=f"能力 '{cap_type}' 尚未注册，请联系管理员",
                capability_type=cap_type,
                next_actions=[
                    NextAction("查看可用能力", "view_capabilities"),
                ],
                raw_query=query,
            )

        # 4. job_status / chat 意图 → 返回查询/对话指引
        if intent_result.intent in ("job_status", "chat"):
            return self._handle_query_status(ctx, intent_result, query)

        # 5. 参数补全：合并 extracted + context 预填
        enriched = self._enrich_params(intent_result.extracted_params, ctx, cap_type)
        hints = PARAM_HINTS.get(cap_type, {})
        required = hints.get("required", [])
        missing = [p for p in required if p not in enriched or not enriched[p]]

        # 6. 参数不足 → need_more_info
        if missing:
            return self._make_need_more_info(
                cap_type, intent_result, enriched, missing, query
            )

        # 7. 参数齐全 → 创建 Job
        if not auto_run:
            return OrchestratorResult(
                answer_type="need_more_info",
                message=f"已准备好创建「{cap_type}」任务，请确认后执行",
                capability_type=cap_type,
                extracted_params=enriched,
                next_actions=[
                    NextAction("确认创建", "create_job", {"capability": cap_type, "params": enriched}),
                    NextAction("取消", "cancel"),
                ],
                intent_confidence=intent_result.confidence,
                raw_query=query,
            )

        try:
            return self._create_and_run_job(cap_type, enriched, intent_result, query)
        except Exception as exc:
            logger.exception("Failed to create job for %s", cap_type)
            return OrchestratorResult(
                answer_type="error",
                message=f"任务创建失败：{exc}",
                capability_type=cap_type,
                extracted_params=enriched,
                next_actions=[
                    NextAction("重试", "retry", {"capability": cap_type, "params": enriched}),
                ],
                intent_confidence=intent_result.confidence,
                raw_query=query,
            )

    # ===== 内部方法 =====

    def _enrich_params(
        self,
        extracted: Dict[str, Any],
        context: Dict[str, Any],
        cap_type: str,
    ) -> Dict[str, Any]:
        """合并 context 预填参数到 extracted params"""
        merged = dict(extracted)

        # 从 context 预填
        for key in ("project_id", "exposure", "outcome", "file_id", "mediator_source"):
            if key not in merged and key in context and context[key]:
                merged[key] = context[key]

        # project_id 优先从 context 取
        if "project_id" in context and context["project_id"]:
            merged["project_id"] = context["project_id"]

        # 为不同能力补全默认值
        defaults_by_cap: Dict[str, Dict[str, Any]] = {
            "gwas_analysis": {
                "covariates": context.get("covariates", ["age", "sex", "bmi"]),
                "method": context.get("method", "REGENIE"),
                "population_filter": context.get("population_filter", "EUR"),
            },
            "mendelian_randomization": {
                "methods": context.get("methods", ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"]),
            },
            "mediation_mr": {
                "mediator_source": context.get("mediator_source", "decode_plasma"),
                "correction_method": "fdr",
            },
            "risk_modeling": {
                "model_types": context.get("model_types", ["OLS", "RCS", "MultinomialLogistic"]),
                "grouping": context.get("grouping", "quartile"),
            },
        }

        defaults = defaults_by_cap.get(cap_type, {})
        for k, v in defaults.items():
            if k not in merged or not merged[k]:
                merged[k] = v

        return merged

    def _create_and_run_job(
        self,
        cap_type: str,
        params: Dict[str, Any],
        intent_result: IntentResult,
        query: str,
    ) -> OrchestratorResult:
        """创建并启动 Job"""
        job = self._job_manager.create_job(
            capability_type=cap_type,
            input_data=params,
            project_id=params.get("project_id", 0),
        )
        self._job_manager.run_job(job.job_id)

        logger.info(
            "Agent created job: %s cap=%s project=%s params=%s",
            job.job_id, cap_type, params.get("project_id"), list(params.keys()),
        )

        # 建议下一步
        next_actions = [
            NextAction("查看任务状态", "view_result", {"job_id": job.job_id}),
            NextAction("查看所有任务", "list_jobs", {"project_id": params.get("project_id", 0)}),
        ]

        # 状态查询的特殊下一步
        if cap_type == "report_generation":
            next_actions.insert(0, NextAction("查看报告", "view_report", {"job_id": job.job_id}))

        return OrchestratorResult(
            answer_type="job_created",
            message=(
                f"已创建「{cap_type}」分析任务 (job: {job.job_id})，"
                f"正在后台执行。您可以通过「查看任务状态」跟踪进度。"
            ),
            capability_type=cap_type,
            job_id=job.job_id,
            job_status=job.status,
            extracted_params=params,
            next_actions=next_actions,
            intent_confidence=intent_result.confidence,
            raw_query=query,
        )

    def _make_need_more_info(
        self,
        cap_type: str,
        intent_result: IntentResult,
        enriched: Dict[str, Any],
        missing: List[str],
        query: str,
    ) -> OrchestratorResult:
        """构建「需要补充信息」响应"""
        hints = PARAM_HINTS.get(cap_type, {}).get("hints", {})
        hint_texts = [f"• {p}: {hints.get(p, '请提供此参数')}" for p in missing]

        return OrchestratorResult(
            answer_type="need_more_info",
            message=(
                f"已识别您想要执行「{cap_type}」分析，"
                f"但缺少以下信息：\n" + "\n".join(hint_texts)
            ),
            capability_type=cap_type,
            extracted_params=enriched,
            missing_params=missing,
            clarification_question=f"请补充：{', '.join(missing)}",
            next_actions=[
                NextAction(f"提供 {p}", "provide_param", {"param": p})
                for p in missing
            ],
            intent_confidence=intent_result.confidence,
            raw_query=query,
        )

    def _make_unsupported(self, intent_result: IntentResult) -> OrchestratorResult:
        """构建「无法识别」响应"""
        return OrchestratorResult(
            answer_type="unsupported",
            message=intent_result.clarification_question or "抱歉，没有理解您的意图",
            clarification_question=intent_result.clarification_question,
            next_actions=[
                NextAction("查看可用能力", "view_capabilities"),
                NextAction("上传 MRI 并分割", "run_segmentation"),
                NextAction("做 GWAS", "run_gwas"),
                NextAction("做 MR", "run_mr"),
                NextAction("查看任务状态", "query_status"),
            ],
            intent_confidence=intent_result.confidence,
            raw_query=intent_result.raw_input,
        )

    def _handle_query_status(
        self,
        ctx: Dict[str, Any],
        intent_result: IntentResult,
        query: str,
    ) -> OrchestratorResult:
        """处理查询状态意图"""
        job_id = intent_result.extracted_params.get("job_id", "")
        project_id = ctx.get("project_id", 0)

        actions = []
        if job_id:
            actions.append(NextAction("查看任务", "view_result", {"job_id": job_id}))
        if project_id:
            actions.append(NextAction("查看项目所有任务", "list_jobs", {"project_id": project_id}))

        return OrchestratorResult(
            answer_type="job_created",
            message=(
                f"查询任务状态。"
                + (f"任务 ID: {job_id}" if job_id else f"项目 {project_id} 的任务列表如下")
            ),
            capability_type="",
            extracted_params=intent_result.extracted_params,
            next_actions=actions or [NextAction("查看项目列表", "list_projects")],
            intent_confidence=intent_result.confidence,
            raw_query=query,
        )

    # ===== 便捷方法 =====

    def list_capabilities(self) -> List[Dict[str, Any]]:
        """列出所有可用能力及其参数要求"""
        caps = []
        for s in self._registry.list_all():
            ct = s["capability_type"]
            hints = PARAM_HINTS.get(ct, {})
            caps.append({
                "capability_type": ct,
                "name": s["name"],
                "mode": s["mode"],
                "required_params": hints.get("required", []),
                "param_hints": hints.get("hints", {}),
            })
        return caps


# ===== 全局单例 =====

agent_orchestrator = AgentOrchestrator()
