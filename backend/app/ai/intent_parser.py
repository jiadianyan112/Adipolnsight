"""
轻量级 AI Intent Parser — 基于规则和关键词匹配

将用户自然语言输入映射到 AdipoInsight 的 AI capability，
不依赖任何大模型。第一版使用关键词 pattern + 置信度评分。

用法：
    from backend.app.ai.intent_parser import IntentParser

    parser = IntentParser()
    result = parser.parse("帮我做一个 GWAS 分析，表型是 Liver PDFF")
    # IntentResult(intent="run_gwas", confidence=0.85, capability_type="gwas_analysis", ...)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from backend.app.ai.intent_types import (
    IntentParseResult,
    IntentResult,  # noqa: F401 — backward-compatible alias
    STANDARD_INTENT,
)


# ===== Intent Pattern 定义 =====

@dataclass
class IntentPattern:
    intent: str
    capability_type: str
    keywords: List[str]                        # 中英文关键词
    required_params: List[str]                 # 必需参数名
    optional_params: List[str] = field(default_factory=list)
    param_patterns: Dict[str, str] = field(default_factory=dict)  # param_name → regex
    description: str = ""


# 8 个意图 + 1 个查询意图
INTENT_PATTERNS: List[IntentPattern] = [
    IntentPattern(
        intent="run_segmentation",
        capability_type="image_segmentation",
        keywords=[
            "影像分割", "图像分割", "分割", "segmentation",
            "MRI 分割", "mri分割", "上传影像", "上传mri",
            "分割肝脏", "分割脂肪", "身体成分", "body composition",
            "影像上传并分割", "上传并分割",
        ],
        required_params=["project_id"],
        optional_params=["file_id", "modality", "target_structures", "model_name"],
        param_patterns={
            "modality": r"(MRI|CT|DIXON)",
            "target_structures": r"(肝脏|liver|胰腺|pancreas|内脏脂肪|visceral.fat|皮下脂肪|subcutaneous.fat|骨髓|bone.marrow)",
            "model_name": r"(TSSA|UNet|nnUNet|SwinUNETR)",
        },
        description="上传 MRI 影像并执行 AI 分割",
    ),
    IntentPattern(
        intent="run_phenotype_quantification",
        capability_type="phenotype_quantification",
        keywords=[
            "表型量化", "脂肪定量", "表型", "phenotype",
            "量化表型", "计算脂肪", "脂肪分数", "PDFF",
            "脂肪体积", "fat volume", "fat quantification",
            "quantify", "量化", "测量脂肪",
        ],
        required_params=["project_id"],
        optional_params=["segmentation_job_id"],
        param_patterns={},
        description="基于分割结果量化多部位脂肪表型",
    ),
    IntentPattern(
        intent="run_gwas",
        capability_type="gwas_analysis",
        keywords=[
            "gwas", "GWAS", "全基因组关联", "genome-wide",
            "关联分析", "genetic association", "做gwas",
            "跑gwas", "做GWAS", "跑GWAS", "全基因组",
            "曼哈顿图", "manhattan", "基因组关联",
            "snp", "SNP", "单核苷酸", "位点",
        ],
        required_params=["project_id", "phenotype"],
        optional_params=["covariates", "population_filter", "method"],
        param_patterns={
            "phenotype": r"(表型|phenotype|性状)[是为:：]?\s*(\w+)",
            "population_filter": r"(EUR|EAS|AFR|SAS|AMR|欧洲|东亚|非洲)",
            "method": r"(REGENIE|PLINK|SAIGE|BOLT)",
        },
        description="执行全基因组关联分析",
    ),
    IntentPattern(
        intent="run_mr",
        capability_type="mendelian_randomization",
        keywords=[
            "孟德尔随机化", "mr", "MR", "mendelian",
            "mendelian randomization", "两样本", "two-sample",
            "工具变量", "instrumental variable", "做mr",
            "跑mr", "做MR", "跑MR", "因果推断",
            "causal inference", "因果", "causal",
        ],
        required_params=["project_id", "exposure", "outcome"],
        optional_params=["methods", "outcome_dataset_id"],
        param_patterns={
            "exposure": r"(暴露|exposure)[是为:：]?\s*(\w+)",
            "outcome": r"(结局|outcome)[是为:：]?\s*(\w+)",
        },
        description="执行双样本孟德尔随机化因果推断",
    ),
    IntentPattern(
        intent="run_mediation_mr",
        capability_type="mediation_mr",
        keywords=[
            "中介mr", "中介MR", "mediation mr", "中介孟德尔",
            "中介", "mediation", "中介分析", "mediation analysis",
            "两步mr", "two-step", "中介因子", "mediator",
            "血浆蛋白", "plasma protein", "蛋白中介",
            "pQTL", "蛋白组", "蛋白质组", "proteomic",
            "中介机制", "中介 MR", "mediation MR",
            "中介随机化",
        ],
        required_params=["project_id", "exposure", "outcome", "mediator_source"],
        optional_params=["candidate_proteins", "correction_method"],
        param_patterns={
            "exposure": r"(暴露|exposure)[是为:：]?\s*(\w+)",
            "outcome": r"(结局|outcome)[是为:：]?\s*(\w+)",
            "mediator_source": r"(deCODE|decode|冰岛|plasma|代谢物|gwas.catalog)",
        },
        description="执行中介孟德尔随机化分析，识别中介血浆蛋白",
    ),
    IntentPattern(
        intent="run_risk_modeling",
        capability_type="risk_modeling",
        keywords=[
            "风险建模", "风险预测", "risk model", "risk modeling",
            "风险评估", "risk assessment", "临床风险",
            "疾病风险", "disease risk", "分层", "stratification",
            "预测模型", "prediction model", "做风险",
            "ols", "OLS", "logistic", "RCS",
            "四分位", "quartile", "骨质疏松风险",
            "osteoporosis risk", "骨质疏松", "风险模型",
        ],
        required_params=["project_id", "exposure", "outcome"],
        optional_params=["outcomes", "model_types", "grouping"],
        param_patterns={
            "exposure": r"(暴露|exposure)[是为:：]?\s*(\w+)",
            "outcome": r"(结局|outcome)[是为:：]?\s*(\w+)",
            "grouping": r"(四分位|quartile|三分位|tertile|中位|median)",
        },
        description="构建多因素临床风险预测模型",
    ),
    IntentPattern(
        intent="run_report",
        capability_type="report_generation",
        keywords=[
            "生成报告", "报告生成", "report", "generate report",
            "出报告", "写报告", "科研报告", "分析报告",
            "汇总", "总结", "summary", "综合报告",
            "生成文档", "导出报告", "生成分析报告", "生成",
        ],
        required_params=["project_id"],
        optional_params=["title", "language", "sections"],
        param_patterns={
            "language": r"(中文|英文|zh|en|Chinese|English)",
            "title": r"(标题|title)[是为:：]?\s*(.+?)(?:[，。,\.]|$)",
        },
        description="生成结构化科研分析报告",
    ),
    IntentPattern(
        intent="query_status",
        capability_type="",
        keywords=[
            "查询", "状态", "进度", "status", "progress",
            "怎么样了", "好了吗", "完成了吗", "结果",
            "进行到", "进展", "查看任务", "查看结果",
            "check", "query", "job status",
        ],
        required_params=[],
        optional_params=["job_id"],
        param_patterns={
            "job_id": r"(任务|job|task)[\s]*(id|ID)?[\s:：]*(\w+)",
        },
        description="查询任务执行状态和进度",
    ),
]


# ===== Intent Parser =====

class IntentParser:
    """轻量级意图解析器"""

    def __init__(self, patterns: List[IntentPattern] = None, min_confidence: float = 0.15):
        self._patterns = patterns or INTENT_PATTERNS
        self._min_confidence = min_confidence

    # intent 名映射: 旧 "run_*" → 标准名
    _INTENT_MAP = {
        "run_segmentation": "segmentation",
        "run_phenotype_quantification": "phenotype",
        "run_gwas": "gwas",
        "run_mr": "mr",
        "run_mediation_mr": "mediation_mr",
        "run_risk_modeling": "risk_modeling",
        "run_report": "report",
        "query_status": "job_status",
        "unknown": "unsupported",
    }

    def _to_standard_intent(self, old_intent: str) -> str:
        return self._INTENT_MAP.get(old_intent, old_intent)

    def parse(self, text: str) -> IntentParseResult:
        """解析用户输入，返回标准 IntentParseResult"""
        if not text or not text.strip():
            return IntentParseResult(
                intent="unsupported",
                confidence=0.0,
                source="rule",
                user_message="请描述您想要执行的 AI 分析任务",
                raw_input=text,
            )

        text_lower = text.lower().strip()
        scored: List[Tuple[IntentPattern, float, List[str]]] = []

        for pattern in self._patterns:
            score, matched = self._score_pattern(pattern, text_lower)
            if score > 0:
                scored.append((pattern, score, matched))

        if not scored:
            return self._clarify(text, "无法识别您的意图，请使用更具体的分析术语")

        # 按置信度排序
        scored.sort(key=lambda x: x[1], reverse=True)
        best_pattern, confidence, matched_kw = scored[0]

        # 消歧：如果 MR 和 Mediation MR 得分接近，优先 Mediation MR
        if best_pattern.intent == "run_mr" and confidence < 0.5:
            for pat, score, kw in scored[1:]:
                if pat.intent == "run_mediation_mr" and score > confidence * 0.7:
                    best_pattern, confidence, matched_kw = pat, score, kw
                    break

        # 提取参数
        extracted = self._extract_params(best_pattern, text)
        missing = [p for p in best_pattern.required_params if p not in extracted]
        confidence = round(confidence, 3)
        std_intent = self._to_standard_intent(best_pattern.intent)

        # 低置信度 → unsupported
        if confidence < self._min_confidence:
            return self._clarify(
                text,
                f"您是否想要「{best_pattern.description}」？如果是，请补充以下信息：{', '.join(missing) if missing else '确认即可'}",
            )

        # 有缺失必需参数 → need more info
        if missing and confidence < 0.7:
            hints = [f"{p}" for p in missing]
            return IntentParseResult(
                intent=std_intent,
                confidence=confidence,
                capability_type=best_pattern.capability_type,
                extracted_params=extracted,
                missing_params=missing,
                source="rule",
                user_message=f"请提供缺失的信息：{', '.join(missing)}",
                next_action="provide_param",
                raw_input=text,
            )

        # 参数齐全 → 可执行
        return IntentParseResult(
            intent=std_intent,
            confidence=confidence,
            capability_type=best_pattern.capability_type,
            extracted_params=extracted,
            missing_params=missing,
            source="rule",
            user_message=f"已识别意图：{best_pattern.description}（置信度 {confidence:.0%}）",
            next_action="create_job",
            raw_input=text,
        )

    # ===== 内部方法 =====

    def _score_pattern(
        self, pattern: IntentPattern, text: str
    ) -> Tuple[float, List[str]]:
        """计算输入与 pattern 的匹配度 (0–1)"""
        matched = []
        total_weight = len(pattern.keywords)
        if total_weight == 0:
            return 0.0, []

        match_count = 0
        for kw in pattern.keywords:
            kw_lower = kw.lower()
            if kw_lower in text:
                match_count += 1
                matched.append(kw)
            # 部分匹配：关键词中的每个词都在文本中（至少 1 个有效词）
            elif len(kw_lower) > 4:
                words = [w for w in kw_lower.split() if len(w) > 2]
                if words and all(w in text for w in words):
                    match_count += 0.5
                    matched.append(f"{kw}(partial)")

        # 使用 sqrt 避免长关键词列表稀释分数
        base_score = match_count / max(1, total_weight ** 0.6)

        # 加分：参数模式匹配
        param_bonus = 0.0
        for param_name, param_regex in pattern.param_patterns.items():
            if re.search(param_regex, text, re.IGNORECASE):
                param_bonus += 0.10

        # 加分：英文专用词精确匹配
        english_bonus = 0.0
        english_kws = [k for k in pattern.keywords if k.isascii() and len(k) > 3]
        for ek in english_kws:
            if re.search(r'\b' + re.escape(ek.lower()) + r'\b', text):
                english_bonus += 0.08

        score = min(1.0, base_score + param_bonus + english_bonus)
        return score, matched

    def _extract_params(
        self, pattern: IntentPattern, text: str
    ) -> Dict[str, Any]:
        """从文本中提取参数值"""
        params: Dict[str, Any] = {}

        for param_name, param_regex in pattern.param_patterns.items():
            match = re.search(param_regex, text, re.IGNORECASE)
            if match:
                # 取最后一个捕获组作为值
                groups = match.groups()
                if groups:
                    value = groups[-1].strip()
                    # 处理列表值（逗号分隔）
                    if "," in value and param_name in (
                        "target_structures", "covariates", "candidate_proteins",
                        "outcomes", "model_types", "methods",
                    ):
                        params[param_name] = [v.strip() for v in value.split(",")]
                    else:
                        params[param_name] = value

        return params

    def _clarify(self, text: str, question: str) -> IntentParseResult:
        return IntentParseResult(
            intent="unsupported",
            confidence=0.0,
            source="rule",
            user_message=question,
            next_action="clarify",
            raw_input=text,
        )

    # ===== 便捷方法 =====

    def list_intents(self) -> List[Dict[str, Any]]:
        """列出所有可识别意图"""
        return [
            {
                "intent": p.intent,
                "capability_type": p.capability_type,
                "description": p.description,
                "required_params": p.required_params,
            }
            for p in self._patterns
        ]


# ===== 全局单例 =====

intent_parser = IntentParser()
