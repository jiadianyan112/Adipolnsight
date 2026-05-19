"""
Mock 结果工厂 — 集中生成与项目参数一致的 Mock 分析结果。

所有 Mock 数据从此模块产出，确保：
1. phenotype 与项目 exposure 一致（不再固定 Liver_PDFF）
2. outcome 与项目 outcome 一致
3. 不同项目之间数据不串
4. 任务统计基于实际传入的 completed_jobs 计数

用法：
    from backend.app.ai.mock_result_factory import MockResultFactory
    factory = MockResultFactory(project_context)
    gwas_result = factory.build_gwas_result()
"""

import math
import random
import uuid
from typing import Any, Dict, List, Optional


class MockResultFactory:
    """根据项目上下文生成一致的 Mock 分析结果。"""

    def __init__(self, project_context: Dict[str, Any]):
        self._project_id = project_context.get("project_id", 0)
        self._exposure = project_context.get("exposure") or project_context.get("phenotype_name") or project_context.get("phenotype") or "Unknown"
        self._outcome = project_context.get("outcome") or project_context.get("outcome_name") or "Unknown"
        self._mediator_source = project_context.get("mediator_source", "decode_plasma")
        self._population = project_context.get("population", "EUR")
        self._sample_size = project_context.get("sample_size", 40484)
        self._completed_job_count = project_context.get("completed_job_count", 0)
        self._total_pipeline_steps = project_context.get("total_pipeline_steps", 7)
        # Deterministic seed per project — ensures reproducibility
        self._seed = self._project_id * 37 + hash(self._exposure) % 10000
        self._rng = random.Random(self._seed)

    @property
    def exposure(self) -> str:
        return self._exposure

    @property
    def outcome(self) -> str:
        return self._outcome

    # ===== GWAS =====

    def build_gwas_result(
        self,
        method: str = "REGENIE",
        significant_loci_count: int = 18,
        lead_snps_count: int = 12,
        lambda_gc: float = 1.03,
    ) -> Dict[str, Any]:
        """构建 GWAS 分析结果。phenotype 自动使用项目 exposure。"""
        return {
            "gwas_id": f"gwas_{uuid.uuid4().hex[:8]}",
            "phenotype": self._exposure,
            "phenotype_id": self._exposure,
            "method": method,
            "population": self._population,
            "sample_size": self._sample_size,
            "lambda_gc": lambda_gc,
            "significant_loci_count": significant_loci_count,
            "lead_snps_count": lead_snps_count,
            "significant_loci": self._build_significant_loci(significant_loci_count),
            "lead_snps": self._build_lead_snps(lead_snps_count),
            "manhattan_plot_url": "",
            "qq_plot_url": "",
            "manhattan_data_points": self._build_manhattan_points(),
            "qq_data_points": self._build_qq_points(),
        }

    # ===== MR =====

    def build_mr_result(
        self,
        primary_method: str = "IVW",
        n_snps: int = 14,
        beta: float = 0.284,
        se: float = 0.067,
        p_value: float = 2.3e-5,
    ) -> Dict[str, Any]:
        """构建双样本 MR 结果。exposure/outcome 自动使用项目参数。"""
        return {
            "mr_id": f"mr_{uuid.uuid4().hex[:8]}",
            "exposure": self._exposure,
            "outcome": self._outcome,
            "primary_method": primary_method,
            "n_snps": n_snps,
            "beta": beta,
            "se": se,
            "p_value": p_value,
            "odds_ratio": math.exp(beta),
            "ci_95": [math.exp(beta - 1.96 * se), math.exp(beta + 1.96 * se)],
            "estimates": [
                {"method": "IVW", "beta": beta, "se": se, "odds_ratio": math.exp(beta),
                 "ci_lower": math.exp(beta - 1.96 * se), "ci_upper": math.exp(beta + 1.96 * se),
                 "p_value": p_value, "n_snps": n_snps},
                {"method": "MR-Egger", "beta": beta * 0.85, "se": se * 1.3, "odds_ratio": math.exp(beta * 0.85),
                 "ci_lower": math.exp(beta * 0.85 - 1.96 * se * 1.3), "ci_upper": math.exp(beta * 0.85 + 1.96 * se * 1.3),
                 "p_value": p_value * 3, "n_snps": n_snps},
                {"method": "Weighted Median", "beta": beta * 0.93, "se": se * 1.1, "odds_ratio": math.exp(beta * 0.93),
                 "ci_lower": math.exp(beta * 0.93 - 1.96 * se * 1.1), "ci_upper": math.exp(beta * 0.93 + 1.96 * se * 1.1),
                 "p_value": p_value * 1.5, "n_snps": n_snps},
                {"method": "Weighted Mode", "beta": beta * 0.78, "se": se * 1.5, "odds_ratio": math.exp(beta * 0.78),
                 "ci_lower": math.exp(beta * 0.78 - 1.96 * se * 1.5), "ci_upper": math.exp(beta * 0.78 + 1.96 * se * 1.5),
                 "p_value": p_value * 5, "n_snps": n_snps},
            ],
            "heterogeneity": [
                {"method": "IVW", "q_statistic": 18.4, "q_df": n_snps - 1, "q_pval": 0.14},
                {"method": "MR-Egger", "q_statistic": 17.2, "q_df": n_snps - 2, "q_pval": 0.19},
            ],
            "pleiotropy": {
                "egger_intercept": -0.0021, "se": 0.008, "pval": 0.79,
                "interpretation": "无显著水平多效性证据 (p > 0.05)",
            },
            "scatter_plot_url": "",
            "forest_plot_url": "",
            "funnel_plot_url": "",
            "leave_one_out_url": "",
            "scatter_data_points": self._build_scatter_points(beta, n_snps),
            "forest_data": self._build_forest_data(beta),
            "leave_one_out_data": self._build_loo_data(beta, n_snps),
        }

    # ===== Mediation MR =====

    def build_mediation_mr_result(self) -> Dict[str, Any]:
        """构建中介 MR 结果。exposure/outcome/mediator 自动使用项目参数。"""
        return {
            "mediation_id": f"medmr_{uuid.uuid4().hex[:8]}",
            "exposure": self._exposure,
            "outcome": self._outcome,
            "mediator_source": self._mediator_source,
            "significant_mediators_count": 2,
            "correction_method": "fdr",
            "alpha": 0.05,
            "ranked_proteins": [
                {"protein": "POR", "uniprot": "P16435", "indirect_effect": 0.145, "proportion_mediated_pct": 33.0,
                 "path_a_beta": 0.284, "path_b_beta": 0.512, "p_mediation": 0.003, "p_fdr": 0.018, "significant": True},
                {"protein": "NAAA", "uniprot": "Q02083", "indirect_effect": 0.067, "proportion_mediated_pct": 15.3,
                 "path_a_beta": 0.131, "path_b_beta": 0.512, "p_mediation": 0.021, "p_fdr": 0.063, "significant": False},
            ],
            "indirect_effects": [
                {"protein": "POR", "indirect_effect": 0.145, "proportion_mediated_pct": 33.0,
                 "p_mediation": 0.003, "p_fdr": 0.018, "significant": True},
                {"protein": "NAAA", "indirect_effect": 0.067, "proportion_mediated_pct": 15.3,
                 "p_mediation": 0.021, "p_fdr": 0.063, "significant": False},
            ],
            "total_effect": 0.44,
            "direct_effect": 0.295,
        }

    # ===== Risk Modeling =====

    def build_risk_modeling_result(self) -> Dict[str, Any]:
        """构建风险建模结果。"""
        return {
            "risk_id": f"risk_{uuid.uuid4().hex[:8]}",
            "exposure": self._exposure,
            "outcome": self._outcome,
            "grouping": "quartile",
            "model_types": ["OLS", "RCS", "MultinomialLogistic"],
            "adjusted_odds_ratios": [
                {"quartile": "Q1", "label": "Q1 (最低)", "pdf_range": f"≤ 5.2%",
                 "osteoporosis_or": 1.00, "or": 1.00, "ci_lower": None, "ci_upper": None},
                {"quartile": "Q2", "label": "Q2", "pdf_range": "5.3–8.1%",
                 "osteoporosis_or": 1.12, "or": 1.12, "ci_lower": 0.94, "ci_upper": 1.33},
                {"quartile": "Q3", "label": "Q3", "pdf_range": "8.2–12.8%",
                 "osteoporosis_or": 1.31, "or": 1.31, "ci_lower": 1.08, "ci_upper": 1.59},
                {"quartile": "Q4", "label": "Q4 (最高)", "pdf_range": "> 12.8%",
                 "osteoporosis_or": 1.59, "or": 1.59, "ci_lower": 1.28, "ci_upper": 1.98},
            ],
            "rcs_curve_data": [],
            "ols_results": [
                {"outcome": self._outcome, "beta": 0.032, "se": 0.008, "p_value": "<0.001", "r_squared": 0.18},
            ],
        }

    # ===== Report context =====

    def build_report_context(self) -> Dict[str, Any]:
        """构建报告生成所需的项目上下文。"""
        pending = max(0, self._total_pipeline_steps - self._completed_job_count)
        return {
            "project_id": self._project_id,
            "exposure": self._exposure,
            "outcome": self._outcome,
            "completed_count": self._completed_job_count,
            "total_steps": self._total_pipeline_steps,
            "pending_count": pending,
            "is_complete": pending == 0,
            "sample_size": self._sample_size,
            "population": self._population,
        }

    # ===== Private helpers =====

    def _build_significant_loci(self, count: int) -> List[Dict[str, Any]]:
        loci = []
        for i in range(count):
            chr_num = (i % 22) + 1
            pos = self._rng.randint(1_000_000, 200_000_000)
            loci.append({
                "locus_id": i + 1,
                "chr": chr_num,
                "start": max(1, pos - self._rng.randint(50_000, 500_000)),
                "end": pos + self._rng.randint(50_000, 500_000),
                "lead_snp": f"rs{self._rng.randint(100000, 999999)}",
                "n_snps": self._rng.randint(5, 200),
                "min_pvalue": 10 ** -self._rng.uniform(5, 15),
            })
        return loci

    def _build_lead_snps(self, count: int) -> List[Dict[str, Any]]:
        snps = []
        for i in range(count):
            chr_num = (i % 22) + 1
            snps.append({
                "snp": f"rs{self._rng.randint(100000, 999999)}",
                "chr": chr_num,
                "bp": self._rng.randint(1_000_000, 200_000_000),
                "ea": self._rng.choice(["A", "C", "G", "T"]),
                "oa": self._rng.choice(["A", "C", "G", "T"]),
                "eaf": round(self._rng.uniform(0.05, 0.95), 3),
                "beta": round(self._rng.uniform(-0.5, 0.5), 4),
                "se": round(self._rng.uniform(0.01, 0.1), 4),
                "p_value": 10 ** -self._rng.uniform(5, 15),
                "neg_log10_p": round(self._rng.uniform(5, 15), 2),
            })
        return snps

    def _build_manhattan_points(self, n: int = 500) -> List[Dict[str, Any]]:
        points = []
        for _ in range(n):
            chr_num = self._rng.randint(1, 22)
            points.append({
                "chr": chr_num,
                "pos": self._rng.randint(1_000_000, 200_000_000),
                "neg_log10_p": max(0, self._rng.gauss(1.5, 1.2)),
            })
        # 模拟显著点
        for _ in range(20):
            points.append({
                "chr": self._rng.randint(1, 22),
                "pos": self._rng.randint(1_000_000, 200_000_000),
                "neg_log10_p": self._rng.uniform(8, 15),
            })
        return points

    def _build_qq_points(self, n: int = 200) -> List[Dict[str, Any]]:
        points = []
        for i in range(n):
            expected = -math.log10((i + 0.5) / n)
            observed = expected * (1 + self._rng.gauss(0, 0.05))
            points.append({"expected": expected, "observed": observed})
        return points

    def _build_scatter_points(self, beta: float, n: int = 40) -> List[Dict[str, Any]]:
        return [{
            "exposure_effect": round(self._rng.gauss(0, 0.3), 3),
            "outcome_effect": round(self._rng.gauss(0, 0.3) + beta * self._rng.gauss(0, 0.3), 3),
            "se": round(self._rng.uniform(0.02, 0.1), 3),
        } for _ in range(n)]

    def _build_forest_data(self, beta: float) -> List[Dict[str, Any]]:
        items = []
        methods = [("IVW", beta), ("MR-Egger", beta * 0.85), ("Weighted Median", beta * 0.93), ("Weighted Mode", beta * 0.78)]
        for label, b in methods:
            items.append({
                "label": label,
                "beta": b,
                "ci_lower": b - 1.96 * 0.07,
                "ci_upper": b + 1.96 * 0.07,
                "or_label": f"{math.exp(b):.2f}",
                "p_value": 0.01,
            })
        return items

    def _build_loo_data(self, beta: float, n: int = 14) -> List[Dict[str, Any]]:
        return [{
            "snp": f"rs{self._rng.randint(100000, 999999)}",
            "beta": round(beta + self._rng.gauss(0, 0.02), 3),
            "se": round(self._rng.uniform(0.05, 0.1), 3),
            "ci_lower": round(beta + self._rng.gauss(0, 0.02) - 1.96 * 0.07, 3),
            "ci_upper": round(beta + self._rng.gauss(0, 0.02) + 1.96 * 0.07, 3),
        } for _ in range(n)]
