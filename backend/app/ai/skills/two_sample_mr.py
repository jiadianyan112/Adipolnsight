"""
C4 · 双样本孟德尔随机化分析 Skill

Mock 模式：生成符合 MR 方法学规范的结构化结果（IVW/MR-Egger/Weighted Median/Weighted Mode，
含异质性检验、水平多效性检验、leave-one-out 数据）。
Real 模式：调用 R TwoSampleMR 包或 Python MendelianRandomization 包。

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
from backend.app.config import STORAGE_DIR


class TwoSampleMRSkill(Skill):
    """C4 · 双样本孟德尔随机化"""

    @property
    def name(self) -> str:
        return "Two-Sample Mendelian Randomization"

    @property
    def capability_type(self) -> str:
        return "mendelian_randomization"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        for key in ["project_id", "exposure", "outcome"]:
            if key not in input_data:
                return False
        methods = input_data.get("methods", [])
        valid = {"IVW", "MR-Egger", "Weighted Median", "Weighted Mode", "Wald ratio"}
        if methods and not set(methods).issubset(valid):
            return False
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["project_id", "exposure", "outcome"],
            "properties": {
                "project_id": {"type": "integer"},
                "exposure": {"type": "string", "description": "暴露名称，如 Liver_PDFF"},
                "exposure_trait": {"type": "string", "description": "暴露性状 ID"},
                "outcome": {"type": "string", "description": "结局名称，如 Osteoporosis"},
                "outcome_trait": {"type": "string", "description": "结局性状 ID"},
                "exposure_snps": {"type": "array", "items": {"type": "string"}, "description": "暴露工具变量 SNP 列表"},
                "outcome_dataset_id": {"type": "string", "description": "结局 GWAS 数据集 ID（如 ukb-b-12141）"},
                "methods": {
                    "type": "array",
                    "items": {"enum": ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode", "Wald ratio"]},
                    "default": ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"],
                },
                "clump_r2": {"type": "number", "default": 0.001},
                "clump_kb": {"type": "integer", "default": 10000},
                "p_threshold": {"type": "number", "default": 5e-8},
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
        exposure = input_data.get("exposure_trait") or input_data.get("exposure", "Liver_PDFF")
        outcome = input_data.get("outcome_trait") or input_data.get("outcome", "Osteoporosis")
        methods = input_data.get("methods", ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"])
        n_snps = input_data.get("n_snps") or len(input_data.get("exposure_snps", [])) or random.randint(8, 25)

        # Primary 方法为 IVW
        ivw_beta = round(random.uniform(0.28, 0.42), 4)
        ivw_se = round(random.uniform(0.06, 0.10), 4)
        ivw_p = round(10 ** (-random.uniform(2.5, 4.5)), 6)

        # 各方法估计值 — IVW 为核心，其他方法围绕 IVW 有适度偏离
        estimates = self._generate_estimates(methods, ivw_beta, ivw_se)

        # 异质性检验
        heterogeneity = self._generate_heterogeneity(n_snps)

        # 水平多效性检验
        pleiotropy = self._generate_pleiotropy()

        # 散点图数据点（SNP-exposure vs SNP-outcome）
        scatter_points = self._generate_scatter_points(ivw_beta, n_snps)

        # Leave-one-out 数据
        loo_data = self._generate_leave_one_out(ivw_beta, ivw_se, n_snps)

        # 森林图数据
        forest_data = self._generate_forest_data(estimates)

        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        mr_id = f"mr_{uuid.uuid4().hex[:8]}"

        ivw_est = next((e for e in estimates if e["method"] == "IVW"), estimates[0])
        se = ivw_est.get("se", ivw_se)
        ci_lower = ivw_est.get("ci_lower", round(ivw_beta - 1.96 * ivw_se, 4))
        ci_upper = ivw_est.get("ci_upper", round(ivw_beta + 1.96 * ivw_se, 4))

        result = {
            "mr_id": mr_id,
            "exposure": exposure,
            "outcome": outcome,
            "primary_method": "IVW",
            "n_snps": n_snps,
            "beta": ivw_beta,
            "se": se,
            "p_value": ivw_p,
            "odds_ratio": round(math.exp(ivw_beta), 3),
            "ci_95": [ci_lower, ci_upper],
            "estimates": estimates,
            "heterogeneity": heterogeneity,
            "pleiotropy": pleiotropy,
            "scatter_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/scatter_plot.png",
            "forest_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/forest_plot.png",
            "funnel_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/funnel_plot.png",
            "leave_one_out_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/leave_one_out.png",
            "scatter_data_points": scatter_points,
            "forest_data": forest_data,
            "leave_one_out_data": loo_data,
        }

        with open(os.path.join(out_dir, "mr_summary.json"), "w") as f:
            json.dump(result, f, indent=2)

        return SkillOutput(
            status="success",
            summary=result,
            output_files=[
                "mr_results.csv",
                "heterogeneity.csv",
                "pleiotropy.csv",
                "mr_summary.json",
                "scatter_plot.png",
                "forest_plot.png",
                "funnel_plot.png",
                "leave_one_out.png",
            ],
            metrics={
                "IVW_beta": ivw_beta,
                "IVW_p": ivw_p,
                "OR": round(math.exp(ivw_beta), 3),
                "cochran_q_p": heterogeneity[0].get("q_pval", 0) if heterogeneity else 0,
                "egger_intercept_p": pleiotropy.get("pval", 1.0),
            },
        )

    # ==== Mock 数据生成器 ====

    def _generate_estimates(
        self, methods: List[str], ivw_beta: float, ivw_se: float
    ) -> List[Dict[str, Any]]:
        """生成各 MR 方法的估计值"""
        configs = {
            "IVW": {"bias": 0, "se_scale": 1.0},
            "MR-Egger": {"bias": 0.06, "se_scale": 2.0},
            "Weighted Median": {"bias": -0.03, "se_scale": 1.2},
            "Weighted Mode": {"bias": -0.02, "se_scale": 1.3},
            "Wald ratio": {"bias": 0.02, "se_scale": 1.5},
        }
        estimates = []
        for method in methods:
            cfg = configs.get(method, {"bias": 0, "se_scale": 1.0})
            beta = round(ivw_beta + random.uniform(-0.06, 0.06) + cfg["bias"], 4)
            se = round(ivw_se * cfg["se_scale"] + random.uniform(-0.01, 0.03), 4)
            ci_low = round(beta - 1.96 * se, 4)
            ci_high = round(beta + 1.96 * se, 4)
            p = round(10 ** (-random.uniform(1.5, 4.0)), 6) if method == "IVW" else round(10 ** (-random.uniform(0.8, 2.5)), 6)
            estimates.append({
                "method": method,
                "beta": beta,
                "se": se,
                "odds_ratio": round(math.exp(beta), 3),
                "ci_lower": ci_low,
                "ci_upper": ci_high,
                "p_value": p,
                "n_snps": random.randint(8, 30),
            })
        return estimates

    def _generate_heterogeneity(self, n_snps: int) -> List[Dict[str, Any]]:
        """Cochran's Q 异质性检验"""
        q = round(random.uniform(n_snps * 0.8, n_snps * 2.0), 2)
        q_df = n_snps - 1
        q_pval = round(random.uniform(0.05, 0.60), 3)
        return [
            {"method": "IVW", "q_statistic": q, "q_df": q_df, "q_pval": q_pval},
            {"method": "MR-Egger", "q_statistic": round(q * random.uniform(0.8, 1.2), 2), "q_df": q_df - 1, "q_pval": round(random.uniform(0.05, 0.60), 3)},
        ]

    def _generate_pleiotropy(self) -> Dict[str, Any]:
        """MR-Egger intercept 水平多效性检验"""
        intercept = round(random.gauss(0, 0.003), 5)
        return {
            "egger_intercept": intercept,
            "se": round(random.uniform(0.002, 0.006), 5),
            "pval": round(random.uniform(0.20, 0.85), 3),
            "interpretation": "无显著水平多效性证据" if random.random() > 0.1 else "可能存在微弱水平多效性",
        }

    def _generate_scatter_points(
        self, ivw_beta: float, n_snps: int
    ) -> List[Dict[str, float]]:
        """生成 SNP-exposure vs SNP-outcome 散点数据"""
        points = []
        for _ in range(n_snps):
            exposure_eff = random.gauss(0, 0.15)
            outcome_eff = exposure_eff * ivw_beta + random.gauss(0, 0.05)
            points.append({
                "exposure_effect": round(exposure_eff, 4),
                "outcome_effect": round(outcome_eff, 4),
                "se": round(random.uniform(0.01, 0.06), 4),
            })
        return points

    def _generate_leave_one_out(
        self, ivw_beta: float, ivw_se: float, n_snps: int
    ) -> List[Dict[str, Any]]:
        """生成 leave-one-out 分析数据"""
        results = []
        for i in range(min(n_snps, 20)):
            beta_loo = round(random.gauss(ivw_beta, ivw_se * 0.3), 4)
            results.append({
                "snp": f"rs{random.randint(10000, 99999999)}",
                "beta": beta_loo,
                "se": round(ivw_se * random.uniform(0.9, 1.1), 4),
                "ci_lower": round(beta_loo - 1.96 * ivw_se, 4),
                "ci_upper": round(beta_loo + 1.96 * ivw_se, 4),
            })
        return results

    def _generate_forest_data(
        self, estimates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成森林图数据（各方法 + 汇总）"""
        data = []
        for est in estimates:
            data.append({
                "label": est["method"],
                "beta": est["beta"],
                "ci_lower": est["ci_lower"],
                "ci_upper": est["ci_upper"],
                "or_label": f"{est['odds_ratio']:.2f} ({est['ci_lower']:.2f}–{est['ci_upper']:.2f})",
                "p_value": est["p_value"],
            })
        return data

    # ==== Real 实现（预留） ====

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """
        真实模式：调用 R TwoSampleMR 包。

        R 脚本示例：
            library(TwoSampleMR)
            exposure_dat <- read_exposure_data("exposure.csv")
            outcome_dat <- extract_outcome_data(exposure_dat$SNP, "ukb-b-12141")
            dat <- harmonise_data(exposure_dat, outcome_dat)
            mr_results <- mr(dat, method_list=c("mr_ivw", "mr_egger_regression", "mr_weighted_median", "mr_weighted_mode"))
            heterogeneity <- mr_heterogeneity(dat)
            pleiotropy <- mr_pleiotropy_test(dat)
            loo <- mr_leaveoneout(dat)
            write.csv(mr_results, "mr_results.csv")

        替换方式：
        1. 将 self.mode 改为 "script"
        2. subprocess.run(["Rscript", "run_mr.R", ...])
        3. 解析输出 CSV → SkillOutput

        暂未实现。
        """
        return SkillOutput(
            status="failed",
            error_code="NOT_IMPLEMENTED",
            error_message="Real MR analysis (R TwoSampleMR) not yet integrated. Switch mode to 'mock'.",
        )


registry.register(TwoSampleMRSkill())
