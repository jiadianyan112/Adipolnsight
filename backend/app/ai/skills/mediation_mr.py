"""
C5 · 中介孟德尔随机化分析 Skill

Mock 模式：生成基于 deCODE pQTL 的两步 MR 中介分析结果。
Real 模式：调用 R TwoStepMR / Python mediation pipeline。

输出结构对齐 schemas/ai.py 和前端 types/analysis.ts
"""

import json
import math
import os
import random
import time
import uuid
from typing import Any, Dict, List

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry


# deCODE 血浆蛋白（用户指定的 6 个候选蛋白 + 额外候选）
CANDIDATE_PROTEINS = [
    {"protein": "ACY1", "full_name": "Aminoacylase-1", "uniprot": "Q03154", "cis_pqtl_count": 3, "known_relevance": "脂肪酸代谢酶，在肝脏中高表达"},
    {"protein": "H6PD", "full_name": "Hexose-6-phosphate dehydrogenase", "uniprot": "O95479", "cis_pqtl_count": 5, "known_relevance": "葡萄糖代谢关键酶，与内脏脂肪分布相关"},
    {"protein": "SHBG", "full_name": "Sex hormone-binding globulin", "uniprot": "P04278", "cis_pqtl_count": 12, "known_relevance": "性激素结合球蛋白，与脂肪分布和骨密度独立相关"},
    {"protein": "ADH1A", "full_name": "Alcohol dehydrogenase 1A", "uniprot": "P07327", "cis_pqtl_count": 2, "known_relevance": "乙醇代谢酶，与肝脏脂肪积累相关"},
    {"protein": "POR", "full_name": "NADPH-cytochrome P450 reductase", "uniprot": "P16435", "cis_pqtl_count": 4, "known_relevance": "药物/脂质代谢酶，参与脂肪肝发病"},
    {"protein": "NAAA", "full_name": "N-acylethanolamine acid amidase", "uniprot": "Q02083", "cis_pqtl_count": 1, "known_relevance": "内源性大麻素代谢酶，调控食欲与能量平衡"},
    {"protein": "FGF21", "full_name": "Fibroblast growth factor 21", "uniprot": "Q9NSA1", "cis_pqtl_count": 6, "known_relevance": "肝脏分泌的代谢激素，直接调节脂肪代谢与骨代谢"},
    {"protein": "GDF15", "full_name": "Growth/differentiation factor 15", "uniprot": "Q99988", "cis_pqtl_count": 8, "known_relevance": "应激应答因子，与体重下降和骨质疏松相关"},
    {"protein": "IGFBP1", "full_name": "Insulin-like growth factor-binding protein 1", "uniprot": "P08833", "cis_pqtl_count": 4, "known_relevance": "IGF-1 结合蛋白，调节骨形成与脂肪分布"},
    {"protein": "LEP", "full_name": "Leptin", "uniprot": "P41159", "cis_pqtl_count": 7, "known_relevance": "脂肪细胞分泌激素，直接调控骨代谢"},
    {"protein": "ADIPOQ", "full_name": "Adiponectin", "uniprot": "Q15848", "cis_pqtl_count": 10, "known_relevance": "脂肪因子，与胰岛素敏感性和骨密度关联"},
    {"protein": "CRP", "full_name": "C-reactive protein", "uniprot": "P02741", "cis_pqtl_count": 6, "known_relevance": "炎症标志物，与骨质疏松风险关联"},
]


class MediationMRSkill(Skill):
    """C5 · 中介孟德尔随机化分析"""

    @property
    def name(self) -> str:
        return "Mediation MR Analysis"

    @property
    def capability_type(self) -> str:
        return "mediation_mr"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required = ["project_id", "exposure", "outcome"]
        for key in required:
            if key not in input_data:
                return False
        source = input_data.get("mediator_source", "decode_plasma")
        if source not in {"decode_plasma", "metabolite_gwas", "gwas_catalog", "custom"}:
            return False
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["project_id", "exposure", "outcome", "mediator_source"],
            "properties": {
                "project_id": {"type": "integer"},
                "exposure": {"type": "string", "description": "暴露名称，如 Liver_PDFF"},
                "outcome": {"type": "string", "description": "结局名称，如 Osteoporosis"},
                "mediator_source": {
                    "enum": ["decode_plasma", "metabolite_gwas", "gwas_catalog", "custom"],
                    "description": "中介数据来源",
                },
                "candidate_proteins": {
                    "type": "array", "items": {"type": "string"},
                    "default": ["ACY1", "H6PD", "SHBG", "ADH1A", "POR", "NAAA"],
                    "description": "候选蛋白列表",
                },
                "total_effect": {"type": "number", "description": "暴露→结局总效应 β"},
                "correction_method": {"enum": ["bonferroni", "fdr", "none"], "default": "fdr"},
                "alpha": {"type": "number", "default": 0.05},
            },
        }

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        if self.mode == "mock":
            return self._run_mock(input_data, context)
        else:
            return self._run_real(input_data, context)

    # ==== Mock 实现 ====

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        time.sleep(0.4)
        exposure = input_data.get("exposure", "Liver_PDFF")
        outcome = input_data.get("outcome", "Osteoporosis")
        source = input_data.get("mediator_source", "decode_plasma")
        alpha = input_data.get("alpha", 0.05)
        total_effect = input_data.get("total_effect", round(random.uniform(0.38, 0.48), 3))
        requested = input_data.get("candidate_proteins", ["ACY1", "H6PD", "SHBG", "ADH1A", "POR", "NAAA"])

        # 从候选蛋白库中选择
        selected = [p for p in CANDIDATE_PROTEINS if p["protein"] in requested] or CANDIDATE_PROTEINS[:6]

        # 生成两步 MR 结果
        path_a_results = []   # 暴露 → 中介
        path_b_results = []   # 中介 → 结局
        indirect_effects = []
        ranked_proteins = []

        for protein_info in selected:
            protein = protein_info["protein"]

            # Path A: 暴露 → 中介蛋白 (βᴬ)
            beta_a = round(random.gauss(0.15, 0.08), 4)
            se_a = round(random.uniform(0.02, 0.06), 4)
            p_a = round(10 ** (-random.uniform(2.0, 5.0)), 6)

            # Path B: 中介蛋白 → 结局 (βᴮ)
            beta_b = round(random.gauss(0.25, 0.12), 4)
            se_b = round(random.uniform(0.03, 0.08), 4)
            p_b = round(10 ** (-random.uniform(1.5, 4.0)), 6)

            # 间接效应 = βᴬ × βᴮ (product method)
            indirect = round(beta_a * beta_b, 5)
            # Delta method SE
            se_indirect = round(math.sqrt((beta_a ** 2) * (se_b ** 2) + (beta_b ** 2) * (se_a ** 2)), 5)
            # Sobel test p
            z_indirect = abs(indirect) / max(se_indirect, 0.0001)
            p_indirect = round(2 * (1 - min(0.9999, 0.5 + 0.5 * math.erf(z_indirect / math.sqrt(2)))), 6)

            # 中介比例
            prop_mediated = round(abs(indirect) / max(total_effect, 0.001) * 100, 1)
            significant = p_indirect < alpha

            path_a_results.append({
                "protein": protein,
                "beta_a": beta_a,
                "se_a": se_a,
                "p_value_a": p_a,
                "f_statistic": round(random.uniform(15, 80), 1),
            })

            path_b_results.append({
                "protein": protein,
                "beta_b": beta_b,
                "se_b": se_b,
                "p_value_b": p_b,
            })

            indirect_effects.append({
                "protein": protein,
                "indirect_effect": indirect,
                "se_indirect": se_indirect,
                "ci_lower": round(indirect - 1.96 * se_indirect, 5),
                "ci_upper": round(indirect + 1.96 * se_indirect, 5),
                "p_mediation": p_indirect,
                "proportion_mediated_pct": prop_mediated,
                "significant": significant,
            })

            ranked_proteins.append({
                "rank": 0,  # 稍后排序
                "protein": protein,
                "full_name": protein_info["full_name"],
                "uniprot": protein_info["uniprot"],
                "indirect_effect": indirect,
                "proportion_mediated_pct": prop_mediated,
                "p_mediation": p_indirect,
                "significant": significant,
                "known_relevance": protein_info["known_relevance"],
            })

        # 按间接效应绝对值排序
        ranked_proteins.sort(key=lambda x: abs(x["indirect_effect"]), reverse=True)
        for i, rp in enumerate(ranked_proteins):
            rp["rank"] = i + 1

        # 汇总统计
        sig_count = sum(1 for ie in indirect_effects if ie["significant"])
        total_indirect = sum(ie["indirect_effect"] for ie in indirect_effects if ie["significant"])
        total_direct = round(total_effect - total_indirect, 4)

        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        med_id = f"medmr_{uuid.uuid4().hex[:8]}"

        result = {
            "mediation_id": med_id,
            "exposure": exposure,
            "outcome": outcome,
            "mediator_source": source,
            "tested_proteins": 4907 if source == "decode_plasma" else 500,
            "candidate_proteins": [p["protein"] for p in selected],
            "correction_method": input_data.get("correction_method", "fdr"),
            "alpha": alpha,
            "total_effect": total_effect,
            "total_indirect_effect": round(total_indirect, 4),
            "total_direct_effect": total_direct,
            "total_effect_pvalue": round(random.uniform(1e-6, 1e-4), 6),
            "significant_mediators_count": sig_count,
            "path_a_results": path_a_results,
            "path_b_results": path_b_results,
            "indirect_effects": indirect_effects,
            "ranked_proteins": ranked_proteins,
            "mechanism_diagram_url": f"/api/v1/files/projects/{context.project_id}/outputs/mediation_mr/mechanism.png",
        }

        with open(os.path.join(out_dir, "mediation_summary.json"), "w") as f:
            json.dump(result, f, indent=2)

        return SkillOutput(
            status="success",
            summary=result,
            output_files=[
                "mediation_results.csv",
                "candidate_proteins.csv",
                "mediation_summary.json",
            ],
            metrics={
                "significant_mediators": sig_count,
                "total_indirect_effect": round(total_indirect, 4),
                "proportion_mediated_max": max((ie["proportion_mediated_pct"] for ie in indirect_effects), default=0),
            },
        )

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        return SkillOutput(
            status="failed",
            error_code="NOT_IMPLEMENTED",
            error_message="Real mediation MR pipeline not yet integrated. Switch mode to 'mock'.",
        )


registry.register(MediationMRSkill())
