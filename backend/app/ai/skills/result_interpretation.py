"""
C8 · AI 分析结果解读 Skill

对已完成的 AI 分析结果进行自然语言解读，支持 5 种分析类型：
segmentation / gwas / mr / mediation_mr / risk_modeling。

Mock 模式使用模板；Real 模式调用 LLM。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry
from backend.app.ai.llm.schema_validator import schema_validator

# ===== 支持的 jobType =====

VALID_JOB_TYPES = {
    "segmentation", "gwas", "mr", "mediation_mr", "risk_modeling",
}

AUDIENCE_LEVELS = {
    "researcher": "生物信息学/医学研究人员",
    "clinician": "临床医生",
    "judge": "竞赛评审专家",
    "general": "一般科研人员",
}


# ===== Mock 模板 =====

def _mock_segmentation(result: dict) -> dict:
    dice = result.get("dice_scores", {})
    qc = result.get("quality_control", {})
    targets = result.get("target_regions", [])
    model = result.get("model_name", "TSSA-UNet")

    dice_text = ", ".join(f"{k}={v:.3f}" for k, v in dice.items()) if dice else "数据缺失"
    qc_status = qc.get("status", "数据缺失")
    qc_score = qc.get("overall_quality_score", "数据缺失")

    key_findings = [
        f"模型 {model} 完成了 {len(targets)} 个解剖结构的分割" if targets else "分割完成",
    ]
    if dice:
        best = max(dice.items(), key=lambda x: x[1])
        worst = min(dice.items(), key=lambda x: x[1])
        key_findings.append(f"{best[0]} 分割精度最高 (DICE={best[1]:.3f})")
        key_findings.append(f"{worst[0]} 分割精度最低 (DICE={worst[1]:.3f})，建议人工复核")

    cautions = []
    if qc_status == "warning":
        cautions.append("质控状态为 warning，定量分析结果需谨慎解读")
    if qc_status == "failed":
        cautions.append("质控未通过 (failed)，建议重新采集或使用更高分辨率序列")
    for region, score in (dice or {}).items():
        if score < 0.85:
            cautions.append(f"{region} 分割 DICE 偏低 ({score:.3f})，可能影响下游分析精度")

    return {
        "summary": f"AI 模型 {model} 对腹部 MRI 进行了多器官自动分割。综合质量评分 {qc_score}，质控状态 {qc_status}。",
        "keyFindings": key_findings,
        "cautions": cautions,
        "recommendedNextSteps": [
            "对 DICE < 0.85 的区域进行人工校正",
            "确认分割 mask 覆盖完整性",
            "将分割结果传递至表型量化 (phenotype_quantification)",
        ],
        "plainLanguageExplanation": (
            f"我们用 AI 模型自动圈出了 MRI 图像中的 {len(targets)} 个解剖结构。"
            f"整体分割质量{'良好' if qc_status == 'passed' else '需要人工复核'}。"
            f"各结构的 AI 分割评分 (DICE) 为：{dice_text}。"
        ),
    }


def _mock_gwas(result: dict) -> dict:
    phenotype = result.get("phenotype", "未知")
    sample_size = result.get("sample_size", "数据缺失")
    n_loci = result.get("significant_loci_count", "数据缺失")
    n_lead = result.get("lead_snps_count", "数据缺失")
    lambda_gc = result.get("lambda_gc", "数据缺失")

    key_findings = [
        f"以 {phenotype} 为表型，在 {sample_size} 例样本中完成 GWAS 扫描",
    ]
    if isinstance(n_loci, int) and n_loci > 0:
        key_findings.append(f"识别 {n_loci} 个显著基因座 (p < 5×10⁻⁸)，{n_lead} 个先导 SNP")

    cautions = []
    if isinstance(lambda_gc, (int, float)):
        if lambda_gc > 1.05:
            cautions.append(f"λ_GC={lambda_gc:.3f} 偏高，可能存在群体分层或隐性关联")
        elif lambda_gc < 0.95:
            cautions.append(f"λ_GC={lambda_gc:.3f} 偏低，需检查统计模型")
    cautions.append("GWAS 为关联分析，不直接证明因果关系——需通过 MR 进一步验证")

    return {
        "summary": f"对表型 {phenotype} 执行了全基因组关联分析 (GWAS)。基因组膨胀系数 λ_GC={lambda_gc}。",
        "keyFindings": key_findings,
        "cautions": cautions,
        "recommendedNextSteps": [
            "对显著 SNP 进行功能注释 (ANNOVAR / FUMA)",
            "以显著 SNP 为工具变量执行孟德尔随机化 (mendelian_randomization)",
            "在独立队列中验证显著位点",
        ],
        "plainLanguageExplanation": (
            f"我们扫描了全基因组，寻找与 {phenotype} 有关的基因位点。"
            f"发现了 {n_loci} 个显著关联区域。"
            f"但关联不等于因果——下一步需要用孟德尔随机化来验证因果关系。"
        ),
    }


def _mock_mr(result: dict) -> dict:
    exposure = result.get("exposure", "未知")
    outcome = result.get("outcome", "未知")
    estimates = result.get("estimates", [])
    pleiotropy = result.get("pleiotropy", {})
    heterogeneity = result.get("heterogeneity", [])

    ivw = next((e for e in estimates if e.get("method") == "IVW"), {})
    ivw_beta = ivw.get("beta", "数据缺失")
    ivw_or = ivw.get("odds_ratio", "数据缺失")
    ivw_p = ivw.get("p_value", "数据缺失")
    egger_p = pleiotropy.get("pval", "数据缺失") if isinstance(pleiotropy, dict) else "数据缺失"

    key_findings = [
        f"IVW 估计：{exposure} → {outcome}，β={ivw_beta}, OR={ivw_or}" if ivw_beta != "数据缺失" else f"MR 分析完成 (暴露={exposure}, 结局={outcome})",
    ]
    for est in estimates:
        if est.get("method") != "IVW":
            key_findings.append(f"{est.get('method')}: β={est.get('beta')}, P={est.get('p_value')}")

    cautions = []
    if isinstance(egger_p, (int, float)):
        if egger_p < 0.05:
            cautions.append(f"MR-Egger intercept p={egger_p:.3f}——存在水平多效性，IVW 估计可能有偏")
        else:
            cautions.append(f"MR-Egger intercept p={egger_p:.3f}——无显著水平多效性证据")
    else:
        cautions.append("缺失多效性检验数据")
    for h in heterogeneity:
        if h.get("q_pval", 1) < 0.05:
            cautions.append(f"{h.get('method')} Cochran's Q p={h.get('q_pval')}——存在显著异质性")
    cautions.append("MR 依赖三大假设（关联性、独立性、排他性）——违反任一假设将导致估计有偏")

    return {
        "summary": f"双样本孟德尔随机化分析评估了 {exposure} 对 {outcome} 的因果效应。IVW 方法为主要分析。",
        "keyFindings": key_findings,
        "cautions": cautions,
        "recommendedNextSteps": [
            "若存在异质性，考虑使用加权中位数或加权众数方法的结果",
            "执行留一法敏感性分析确认无单 SNP 驱动",
            "进行中介 MR 分析探索生物学机制",
        ],
        "plainLanguageExplanation": (
            f"我们利用遗传变异作为工具变量，评估了 {exposure} 是否因果性地影响 {outcome}。"
            f"主要方法的 OR 值为 {ivw_or}。"
            f"{'多效性检验通过，结果较为可靠' if isinstance(egger_p, (int, float)) and egger_p >= 0.05 else '需注意多效性偏倚风险'}。"
        ),
    }


def _mock_mediation_mr(result: dict) -> dict:
    exposure = result.get("exposure", "未知")
    outcome = result.get("outcome", "未知")
    source = result.get("mediator_source", "未知")
    sig_count = result.get("significant_mediators_count", 0)
    proteins = result.get("ranked_proteins", []) or result.get("indirect_effects", [])

    top3 = []
    for p in (proteins or [])[:3]:
        name = p.get("protein", p.get("protein_name", "?"))
        ie = p.get("indirect_effect", "?")
        prop = p.get("proportion_mediated_pct", "?")
        top3.append(f"{name} (间接效应={ie}, 中介比例={prop}%)")

    key_findings = [
        f"从 {source} 中筛选中介血浆蛋白 ({'deCODE 4,907 种蛋白' if 'decode' in str(source) else source})",
        f"识别 {sig_count} 个显著中介蛋白 (FDR<0.05)" if sig_count > 0 else "未发现显著中介蛋白 (FDR<0.05)",
    ]
    if top3:
        key_findings.append(f"前三名中介蛋白: {'; '.join(top3)}")

    cautions = [
        "中介 MR 使用 cis-pQTL，可能遗漏 trans-pQTL 的中介效应",
        "中介比例之和可能 ≠ 100%（不同蛋白间效应可能重叠）",
        "未测量蛋白和代谢物可能也是重要的中介因子",
    ]

    return {
        "summary": f"中介 MR 分析识别了 {exposure}→蛋白→{outcome} 的中介路径。利用 {source} 数据进行两步法 MR。",
        "keyFindings": key_findings,
        "cautions": cautions,
        "recommendedNextSteps": [
            "对显著中介蛋白进行功能注释和通路富集分析",
            "在独立队列中验证 POR/NAAA 等关键中介蛋白",
            "考虑多变量 MR 分析评估蛋白间的独立中介效应",
        ],
        "plainLanguageExplanation": (
            f"我们研究了血浆蛋白在 {exposure} 影响 {outcome} 的过程中扮演的桥梁角色。"
            f"发现了 {sig_count} 个显著的中介蛋白，其中{top3[0] if top3 else '无'}最为关键。"
            f"这些蛋白可能是潜在的药物靶点。"
        ),
    }


def _mock_risk_modeling(result: dict) -> dict:
    exposure = result.get("exposure", "未知")
    outcome = result.get("outcome", "未知")
    grouping = result.get("grouping", "quartile")
    ors = result.get("adjusted_odds_ratios", [])
    ols = result.get("ols_results", [])
    model_types = result.get("model_types", [])

    or_summary = "数据缺失"
    if ors:
        last = ors[-1]
        or_val = last.get("osteoporosis_or", last.get("or", "?"))
        or_summary = f"Q4 vs Q1: OR={or_val}"

    key_findings = [
        f"构建了 {exposure}→{outcome} 的多因素风险预测模型",
        f"建模方法: {', '.join(model_types) if model_types else 'OLS + RCS + 多分类 Logistic'}",
        f"剂量-反应关系: {or_summary}",
    ]
    for m in (ols or [])[:2]:
        key_findings.append(f"{m.get('outcome', '?')}: β={m.get('beta', '?')}, P={m.get('p_value', '?')}")

    cautions = [
        "横断面设计无法确定因果时序——MR 证据可作为因果推断补充",
        "协变量模型中的未测量混杂可能影响估计",
        f"四分位 cutoff 值为人群特异——泛化到其他人群需重新校准",
        "风险模型需在独立队列中进行外部验证",
    ]

    return {
        "summary": f"基于 {exposure} 构建了 {outcome} 风险预测模型。采用 {grouping} 分层策略评估剂量-反应关系。",
        "keyFindings": key_findings,
        "cautions": cautions,
        "recommendedNextSteps": [
            "在独立队列中外部验证风险模型",
            "开发风险评分 (Risk Score) 工具供临床使用",
            "结合 MR 结果构建因果风险模型",
        ],
        "plainLanguageExplanation": (
            f"我们建立了一个模型来预测 {exposure} 对 {outcome} 风险的影响。"
            f"结果显示 {exposure} 最高的四分之一人群，{outcome} 风险显著增加。"
            f"但需要注意，模型不能直接用于临床决策，需要更多验证。"
        ),
    }


_MOCK_GENERATORS = {
    "segmentation": _mock_segmentation,
    "gwas": _mock_gwas,
    "mr": _mock_mr,
    "mediation_mr": _mock_mediation_mr,
    "risk_modeling": _mock_risk_modeling,
}


# ===== Skill 实现 =====

class ResultInterpretationSkill(Skill):
    """C8 · AI 分析结果解读"""

    @property
    def name(self) -> str:
        return "AI Result Interpretation"

    @property
    def capability_type(self) -> str:
        return "result_interpretation"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    # ===== 输入校验 =====

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        if "sourceJobId" not in input_data and "source_job_id" not in input_data:
            return False
        job_type = input_data.get("jobType") or input_data.get("job_type", "")
        if job_type not in VALID_JOB_TYPES:
            return False
        result = input_data.get("jobResult") or input_data.get("job_result")
        if not result or not isinstance(result, dict):
            return False
        audience = input_data.get("audience", "researcher")
        if audience not in AUDIENCE_LEVELS:
            return False
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["sourceJobId", "jobType", "jobResult"],
            "properties": {
                "sourceJobId": {"type": "string", "description": "被解读的源 Job ID"},
                "jobType": {
                    "enum": list(VALID_JOB_TYPES),
                    "description": "源 Job 的分析类型",
                },
                "jobResult": {"type": "object", "description": "源 Job 的输出 summary"},
                "audience": {
                    "enum": list(AUDIENCE_LEVELS.keys()),
                    "default": "researcher",
                    "description": "目标读者",
                },
                "language": {"enum": ["zh", "en"], "default": "zh", "description": "输出语言"},
            },
        }

    # ===== 执行入口 =====

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        source_job_id = input_data.get("sourceJobId") or input_data.get("source_job_id", "")
        job_type = input_data.get("jobType") or input_data.get("job_type", "")
        job_result = input_data.get("jobResult") or input_data.get("job_result", {})
        audience = input_data.get("audience", "researcher")
        language = input_data.get("language", "zh")

        if not isinstance(job_result, dict):
            job_result = {}

        # 1. 尝试 LLM 解读
        llm_output = self._try_llm_interpretation(job_type, job_result, audience, language)

        # 2. LLM 失败 → Mock fallback
        if llm_output is None:
            llm_output = self._mock_interpretation(job_type, job_result)

        # 3. 确保输出结构完整
        output = {
            "summary": llm_output.get("summary", ""),
            "keyFindings": llm_output.get("keyFindings", llm_output.get("key_findings", [])),
            "cautions": llm_output.get("cautions", llm_output.get("limitations", [])),
            "recommendedNextSteps": llm_output.get(
                "recommendedNextSteps",
                llm_output.get("suggested_next_steps", []),
            ),
            "plainLanguageExplanation": llm_output.get("plainLanguageExplanation", ""),
            "evidenceJobId": source_job_id,
        }

        # 写出到 output_dir
        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "interpretation.json"), "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return SkillOutput(
            status="success",
            summary=output,
            output_files=["interpretation.json"],
            metrics={},
        )

    # ===== LLM 路径 =====

    def _try_llm_interpretation(
        self, job_type: str, job_result: dict, audience: str, language: str
    ) -> dict | None:
        """通过 LLM Service 生成解读。失败返回 None。"""
        try:
            from backend.app.ai.llm.service import llm_service
            from backend.app.ai.llm.prompts.result_interpreter import (
                SYSTEM_PROMPT,
                build_user_prompt,
            )
            from backend.app.schemas.llm import LLMRequest, LLMMessage

            user_msg = build_user_prompt(
                capability_type=job_type,
                result_summary=job_result,
                language=language,
            )

            audience_note = f"\n\nTarget audience: {AUDIENCE_LEVELS.get(audience, audience)}."
            user_msg += audience_note

            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=SYSTEM_PROMPT),
                    LLMMessage(role="user", content=user_msg),
                ],
                taskType="result_interpretation",
                temperature=0.3,
            )

            response = llm_service.call_llm_json(request)

            if response.json_data is None:
                return None

            data = response.json_data
            if not isinstance(data, dict):
                return None

            # 确保字段完整
            data.setdefault("cautions", data.get("limitations", []))
            data.setdefault(
                "plainLanguageExplanation",
                "通俗解读暂时不可用，请参见以上专业解读。",
            )
            return data

        except Exception:
            return None

    # ===== Mock 路径 =====

    def _mock_interpretation(self, job_type: str, job_result: dict) -> dict:
        """使用模板生成解读。"""
        generator = _MOCK_GENERATORS.get(job_type)
        if generator is None:
            return {
                "summary": f"暂不支持对 {job_type} 类型的自动解读。请查看原始分析结果。",
                "keyFindings": [],
                "cautions": ["此解读由 Mock 模板生成，不基于实际数据"],
                "recommendedNextSteps": ["查看原始分析数据"],
                "plainLanguageExplanation": "抱歉，此分析类型的通俗解读暂未实现。",
            }

        result = generator(job_result)
        result["cautions"] = result.get("cautions", []) + [
            "[Mock] 此解读由模板生成，不基于 LLM 深度分析。接入 DeepSeek 后将提供更精准的个体化解讀。",
        ]
        return result


# 自动注册
registry.register(ResultInterpretationSkill())
