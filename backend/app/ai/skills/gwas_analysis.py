"""
C3 · GWAS 全基因组关联分析 Skill

Mock 模式：生成贴合真实 GWAS 场景的结构化结果（Manhattan/QQ 数据、显著位点、λ_GC）。
Real 模式：调用 REGENIE step1 + step2。

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


CHROMOSOMES = list(range(1, 23))
# 各染色体近似长度 (Mb)，用于生成真实位置
CHR_LENGTHS_MB = {
    1: 249, 2: 237, 3: 198, 4: 190, 5: 182, 6: 171, 7: 159,
    8: 146, 9: 141, 10: 136, 11: 135, 12: 133, 13: 114, 14: 107,
    15: 102, 16: 90, 17: 83, 18: 80, 19: 59, 20: 64, 21: 47, 22: 51,
}


class GWASAnalysisSkill(Skill):
    """C3 · GWAS 全基因组关联分析"""

    @property
    def name(self) -> str:
        return "GWAS Analysis"

    @property
    def capability_type(self) -> str:
        return "gwas_analysis"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        if "project_id" not in input_data:
            return False
        # phenotype is NOT strictly required — fallback reads from project DB
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["project_id"],
            "properties": {
                "project_id": {"type": "integer"},
                "phenotype_id": {"type": "string", "description": "表型 ID（如 Liver_PDFF）"},
                "phenotype_name": {"type": "string", "description": "表型显示名称"},
                "covariates": {
                    "type": "array", "items": {"type": "string"},
                    "default": ["age", "sex", "bmi", "PC1", "PC2", "PC3", "PC4", "PC5", "PC6", "PC7", "PC8", "PC9", "PC10"],
                },
                "population_filter": {"type": "string", "default": "EUR", "enum": ["EUR", "EAS", "AFR", "SAS", "AMR", "ALL"]},
                "method": {"type": "string", "default": "REGENIE", "enum": ["REGENIE", "PLINK2", "SAIGE", "BOLT-LMM"]},
                "maf_threshold": {"type": "number", "minimum": 0, "maximum": 0.5, "default": 0.01},
                "hwe_threshold": {"type": "number", "default": 1e-6},
                "qc_options": {"type": "object", "default": {"impute_missing": True, "remove_outliers": True, "normalize_phenotype": True}},
            },
        }

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        if self.mode == "mock":
            return self._run_mock(input_data, context)
        else:
            return self._run_real(input_data, context)

    # ==== Mock 实现 ====

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        time.sleep(0.5)

        # Resolve project context (tries input_data → database → fallback)
        project_ctx = self._resolve_project_context(input_data, context.project_id)
        phenotype = project_ctx["exposure"]
        method = input_data.get("method", "REGENIE")
        covariates = input_data.get("covariates", ["age", "sex", "bmi"])
        population = input_data.get("population_filter", "EUR")

        from backend.app.ai.mock_result_factory import MockResultFactory
        factory = MockResultFactory(project_ctx)
        result = factory.build_gwas_result(
            method=method,
            significant_loci_count=random.randint(12, 28),
            lead_snps_count=random.randint(8, 18),
            lambda_gc=round(random.uniform(1.00, 1.05), 3),
        )
        # Override with specific input params
        result["population"] = population
        result["covariates"] = covariates
        result["phenotype_id"] = input_data.get("phenotype_id", phenotype)

        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)

        result["manhattan_plot_url"] = f"/api/v1/files/projects/{context.project_id}/outputs/gwas/manhattan.png"
        result["qq_plot_url"] = f"/api/v1/files/projects/{context.project_id}/outputs/gwas/qq_plot.png"

        # 写出文件
        with open(os.path.join(out_dir, "gwas_summary.json"), "w") as f:
            json.dump(result, f, indent=2)

        return SkillOutput(
            status="success",
            summary=result,
            output_files=[
                "gwas_summary_stats.tsv",
                "lead_snps.csv",
                "significant_loci.csv",
                "gwas_summary.json",
                "manhattan.png",
                "qq_plot.png",
            ],
            metrics={
                "significant_loci_count": result["significant_loci_count"],
                "lead_snps_count": result["lead_snps_count"],
                "lambda_gc": result["lambda_gc"],
                "sample_size": result["sample_size"],
            },
        )

    @staticmethod
    def _resolve_project_context(input_data: Dict[str, Any], project_id: int) -> Dict[str, Any]:
        """Resolve project context: input_data → database → fallback."""
        ctx: Dict[str, Any] = {"project_id": project_id, "exposure": "", "outcome": "", "sample_size": 40484}

        # 1. From input_data
        ctx["exposure"] = input_data.get("phenotype_name") or input_data.get("phenotype") or ""
        ctx["outcome"] = input_data.get("outcome") or input_data.get("outcome_name") or ""

        # 2. From project database
        if not ctx["exposure"] or not ctx["outcome"]:
            try:
                from backend.app.database import SessionLocal
                from backend.app.models.project import Project
                db = SessionLocal()
                try:
                    project = db.query(Project).filter(Project.id == project_id).first()
                    if project:
                        if not ctx["exposure"]:
                            ctx["exposure"] = project.exposure or ""
                        if not ctx["outcome"]:
                            ctx["outcome"] = project.outcome or ""
                finally:
                    db.close()
            except Exception:
                pass

        # 3. Fallback (with explicit marker)
        if not ctx["exposure"]:
            ctx["exposure"] = "MOCK_UnknownExposure"
        if not ctx["outcome"]:
            ctx["outcome"] = "MOCK_UnknownOutcome"

        return ctx

    # ==== Mock 数据生成器 ====

    def _generate_lead_snps(self, n: int) -> List[Dict[str, Any]]:
        """生成先导 SNP，贴近真实 GWAS 统计量"""
        snps = []
        used_chrs = set()
        for i in range(n):
            chr_num = random.choice(CHROMOSOMES)
            # 避免同一染色体过多
            if len(used_chrs) < 10 and random.random() < 0.6:
                while chr_num in used_chrs:
                    chr_num = random.choice(CHROMOSOMES)
            used_chrs.add(chr_num)

            bp = random.randint(1, CHR_LENGTHS_MB.get(chr_num, 100) * 1_000_000)
            ea = random.choice(["A", "C", "G", "T"])
            oa = random.choice([b for b in ["A", "C", "G", "T"] if b != ea])
            # 效应量：大部分小效应，少数大效应
            beta = round(random.gauss(0, 0.08), 4)
            se = round(random.uniform(0.005, 0.03), 4)
            pval = 10 ** (-random.uniform(3, 10))

            snp_name = f"rs{random.randint(10000, 99999999)}"
            snps.append({
                "snp": snp_name,
                "chr": chr_num,
                "bp": bp,
                "ea": ea,
                "oa": oa,
                "eaf": round(random.uniform(0.05, 0.95), 3),
                "beta": beta,
                "se": se,
                "p_value": pval,
                "neg_log10_p": round(-math.log10(pval), 2),
            })

        # 按 p 值升序排列
        snps.sort(key=lambda x: x["p_value"])
        return snps

    def _generate_significant_loci(
        self, lead_snps: List[Dict[str, Any]], n_loci: int
    ) -> List[Dict[str, Any]]:
        """生成显著基因座"""
        loci = []
        for i in range(min(n_loci, len(lead_snps))):
            snp = lead_snps[i]
            margin = random.randint(50_000, 200_000)
            loci.append({
                "locus_id": i + 1,
                "chr": snp["chr"],
                "start": max(1, snp["bp"] - margin),
                "end": snp["bp"] + margin,
                "lead_snp": snp["snp"],
                "n_snps": random.randint(20, 200),
                "min_pvalue": snp["p_value"],
            })
        return loci

    def _generate_manhattan_points(
        self, lead_snps: List[Dict[str, Any]], n_background: int
    ) -> List[Dict[str, float]]:
        """生成 Manhattan 图数据点（前端可直接渲染）"""
        points: List[Dict[str, float]] = []

        # 显著位点周围的点
        for snp in lead_snps:
            points.append({
                "chr": float(snp["chr"]),
                "pos": float(snp["bp"]),
                "neg_log10_p": float(snp["neg_log10_p"]),
            })
            # 位点周围加一些连锁点
            for _ in range(random.randint(3, 10)):
                points.append({
                    "chr": float(snp["chr"]),
                    "pos": float(snp["bp"] + random.randint(-500_000, 500_000)),
                    "neg_log10_p": round(snp["neg_log10_p"] - random.uniform(1, 4), 2),
                })

        # 背景噪声点
        for _ in range(n_background):
            chr_num = float(random.choice(CHROMOSOMES))
            pos = float(random.randint(1, CHR_LENGTHS_MB.get(int(chr_num), 100) * 1_000_000))
            p = random.expovariate(1.0 / 1.5)  # 大多低 p 的指数分布
            points.append({"chr": chr_num, "pos": pos, "neg_log10_p": round(p, 2)})

        return points

    def _generate_qq_points(
        self, lambda_gc: float, n_points: int
    ) -> List[Dict[str, float]]:
        """生成 QQ 图数据点"""
        points = []
        for i in range(n_points):
            expected = -math.log10((i + 0.5) / n_points)
            observed = expected * lambda_gc + random.uniform(-0.5, 0.5)
            points.append({
                "expected": round(expected, 3),
                "observed": round(max(0, observed), 3),
            })
        return points

    # ==== Real 实现（预留） ====

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """
        真实模式：调用 REGENIE step1 + step2。

        REGENIE 命令行示例：
            regenie --step 1 --bed data --phenoFile pheno.csv --phenoCol Liver_PDFF --covarFile covar.csv --bsize 1000 --out step1
            regenie --step 2 --bed data --phenoFile pheno.csv --phenoCol Liver_PDFF --covarFile covar.csv --pred step1_pred.list --bsize 400 --out step2

        暂未实现。
        """
        return SkillOutput(
            status="failed",
            error_code="NOT_IMPLEMENTED",
            error_message="Real GWAS pipeline (REGENIE) not yet integrated. Switch mode to 'mock'.",
        )


registry.register(GWASAnalysisSkill())
