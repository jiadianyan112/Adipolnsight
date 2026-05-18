"""
C4 · 双样本孟德尔随机化分析 Skill

Mock 模式：生成符合 MR 方法学规范的结构化结果。
Script 模式：真实调用 Python MR 引擎 + OpenGWAS API + harmonization + 可视化。
"""

import json
import logging
import math
import os
import random
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry
from backend.app.ai.mr.engine import (
    mr_ivw,
    mr_egger,
    mr_weighted_median,
    mr_weighted_mode,
    cochran_q,
    mr_egger_intercept_test,
)
from backend.app.ai.mr.harmonization import harmonize, HarmonizationResult
from backend.app.ai.mr.plots import (
    plot_scatter,
    plot_forest,
    plot_leave_one_out,
    plot_funnel,
)
from backend.app.ai.mr.opengwas import find_best_match, fetch_sumstats
from backend.app.config import get_skill_mode, STORAGE_DIR

logger = logging.getLogger("adipoinsight.mr_skill")


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
        return get_skill_mode(self.capability_type)  # type: ignore

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
                "exposure": {"type": "string"},
                "exposure_trait": {"type": "string"},
                "exposure_file": {"type": "string", "description": "上传的暴露 GWAS 文件路径"},
                "outcome": {"type": "string"},
                "outcome_trait": {"type": "string"},
                "outcome_dataset_id": {"type": "string", "description": "结局 OpenGWAS ID"},
                "outcome_file": {"type": "string", "description": "上传的结局 GWAS 文件路径"},
                "exposure_snps": {"type": "array", "items": {"type": "string"}},
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

    # ========================
    #   Mock implementation
    # ========================

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        time.sleep(0.4)
        exposure = input_data.get("exposure_trait") or input_data.get("exposure", "Liver_PDFF")
        outcome = input_data.get("outcome_trait") or input_data.get("outcome", "Osteoporosis")
        methods = input_data.get("methods", ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"])
        n_snps = input_data.get("n_snps") or len(input_data.get("exposure_snps", [])) or random.randint(8, 25)

        ivw_beta = round(random.uniform(0.28, 0.42), 4)
        ivw_se = round(random.uniform(0.06, 0.10), 4)
        ivw_p = round(10 ** (-random.uniform(2.5, 4.5)), 6)
        estimates = self._generate_estimates(methods, ivw_beta, ivw_se)
        heterogeneity = self._generate_heterogeneity(n_snps)
        pleiotropy = self._generate_pleiotropy()
        scatter_points = self._generate_scatter_points(ivw_beta, n_snps)
        loo_data = self._generate_leave_one_out(ivw_beta, ivw_se, n_snps)
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
            output_files=["mr_results.csv", "heterogeneity.csv", "pleiotropy.csv",
                          "mr_summary.json"],
            metrics={
                "IVW_beta": ivw_beta, "IVW_p": ivw_p,
                "OR": round(math.exp(ivw_beta), 3),
                "cochran_q_p": heterogeneity[0].get("q_pval", 0) if heterogeneity else 0,
                "egger_intercept_p": pleiotropy.get("pval", 1.0),
            },
        )

    # Mock data generators (unchanged)
    def _generate_estimates(self, methods, ivw_beta, ivw_se):
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
            p = round(10 ** (-random.uniform(1.5, 4.0)), 6)
            estimates.append({
                "method": method, "beta": beta, "se": se,
                "odds_ratio": round(math.exp(beta), 3),
                "ci_lower": ci_low, "ci_upper": ci_high, "p_value": p,
                "n_snps": random.randint(8, 30),
            })
        return estimates

    def _generate_heterogeneity(self, n_snps):
        q = round(random.uniform(n_snps * 0.8, n_snps * 2.0), 2)
        q_df = n_snps - 1
        q_pval = round(random.uniform(0.05, 0.60), 3)
        return [
            {"method": "IVW", "q_statistic": q, "q_df": q_df, "q_pval": q_pval},
            {"method": "MR-Egger", "q_statistic": round(q * random.uniform(0.8, 1.2), 2),
             "q_df": q_df - 1, "q_pval": round(random.uniform(0.05, 0.60), 3)},
        ]

    def _generate_pleiotropy(self):
        intercept = round(random.gauss(0, 0.003), 5)
        return {
            "egger_intercept": intercept,
            "se": round(random.uniform(0.002, 0.006), 5),
            "pval": round(random.uniform(0.20, 0.85), 3),
            "interpretation": "无显著水平多效性证据",
        }

    def _generate_scatter_points(self, ivw_beta, n_snps):
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

    def _generate_leave_one_out(self, ivw_beta, ivw_se, n_snps):
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

    def _generate_forest_data(self, estimates):
        return [{
            "label": est["method"],
            "beta": est["beta"],
            "ci_lower": est["ci_lower"],
            "ci_upper": est["ci_upper"],
            "or_label": f"{est['odds_ratio']:.2f} ({est['ci_lower']:.2f}–{est['ci_upper']:.2f})",
            "p_value": est["p_value"],
        } for est in estimates]

    # ========================
    #   Real implementation
    # ========================

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """
        Real MR analysis pipeline.

        Steps:
        1. Load exposure data (file or OpenGWAS)
        2. Load outcome data (file or OpenGWAS)
        3. Run validate_and_standardize if files provided
        4. Clumping (p < 5e-8 threshold filter)
        5. Harmonization
        6. MR methods: IVW, MR-Egger, Weighted Median, Weighted Mode
        7. Sensitivity: Cochran's Q, Egger intercept, Leave-one-out
        8. Plots: scatter, forest, funnel, LOO
        9. Return structured result
        """
        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        mr_id = f"mr_{uuid.uuid4().hex[:8]}"
        warnings: List[str] = []
        log_lines: List[str] = []

        exposure_name = input_data.get("exposure_trait") or input_data.get("exposure", "Exposure")
        outcome_name = input_data.get("outcome_trait") or input_data.get("outcome", "Outcome")
        methods = input_data.get("methods", ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"])
        p_threshold = input_data.get("p_threshold", 5e-8)

        log_lines.append(f"MR Analysis: {exposure_name} → {outcome_name}")
        log_lines.append(f"Methods: {', '.join(methods)}")

        # ---- Step 1 & 2: Load data ----
        exp_file = input_data.get("exposure_file", "")
        out_file = input_data.get("outcome_file", "")

        try:
            if exp_file and os.path.isfile(exp_file):
                # User uploaded files
                exp_df = pd.read_csv(exp_file, sep=None, engine="python")
                out_df = pd.read_csv(out_file, sep=None, engine="python") if out_file and os.path.isfile(out_file) else None
                if out_df is None:
                    raise ValueError("Outcome file required when using exposure file")
            else:
                # OpenGWAS workflow: exposure tophits → outcome associations
                from backend.app.ai.mr.opengwas import find_best_match, fetch_tophits, fetch_associations

                exp_match = find_best_match(exposure_name, ancestry="European")
                if exp_match is None:
                    return self._fail("DATA_LOAD_ERROR",
                                      f"Cannot find GWAS dataset for exposure='{exposure_name}'. "
                                      f"Please upload a file or use a more specific trait name.")
                log_lines.append(f"Exposure dataset: {exp_match.id} (n={exp_match.sample_size:,})")

                out_match = find_best_match(outcome_name, ancestry="European")
                if out_match is None:
                    return self._fail("DATA_LOAD_ERROR",
                                      f"Cannot find GWAS dataset for outcome='{outcome_name}'.")

                # Get exposure instruments first
                exp_df = fetch_tophits(exp_match.id, pval_threshold=p_threshold, clump=True, pop="EUR")
                log_lines.append(f"Exposure instruments: {len(exp_df)} SNPs (clumped, P<{p_threshold})")

                if len(exp_df) < 3:
                    return self._fail("INSUFFICIENT_SNPS",
                                      f"Only {len(exp_df)} exposure instruments. Need ≥ 3.")

                # Get outcome associations for same SNPs
                snp_list = exp_df["rsid"].tolist()
                out_df = fetch_associations(out_match.id, snp_list)
                log_lines.append(f"Outcome dataset: {out_match.id} (n={out_match.sample_size:,}), "
                                 f"{len(out_df)}/{len(snp_list)} SNPs matched")

                # Standardize column names
                cmap = {"rsid": "SNP", "ea": "effect_allele", "nea": "other_allele", "p": "pval"}
                exp_df = exp_df.rename(columns=cmap)
                out_df = out_df.rename(columns=cmap)

        except Exception as exc:
            return self._fail("DATA_LOAD_ERROR", str(exc))

        log_lines.append(f"Exposure: {len(exp_df)} SNPs loaded")
        log_lines.append(f"Outcome:  {len(out_df)} SNPs loaded")

        # ---- Step 3: Clumping (p-value filter) ----
        if "pval" in exp_df.columns or "p_value" in exp_df.columns:
            p_col = "pval" if "pval" in exp_df.columns else "p_value"
            n_before = len(exp_df)
            exp_df = exp_df[exp_df[p_col] < p_threshold].copy()
            log_lines.append(f"Clumping: {n_before} → {len(exp_df)} SNPs (P < {p_threshold})")

        if len(exp_df) < 3:
            return self._fail("INSUFFICIENT_SNPS",
                              f"Only {len(exp_df)} SNPs after clumping. Need ≥ 3 for MR.")

        # ---- Step 4: Harmonization ----
        try:
            harm_result = harmonize(exp_df, out_df)
            dat = harm_result.data
            warnings.extend(harm_result.warnings)
            log_lines.append(
                f"Harmonization: {harm_result.n_original} → {harm_result.n_after} SNPs "
                f"({harm_result.n_removed_palindromic} palindromic removed, "
                f"{harm_result.n_flipped} flipped)"
            )
        except Exception as exc:
            return self._fail("HARMONIZATION_ERROR", str(exc))

        if len(dat) < 3:
            return self._fail("INSUFFICIENT_SNPS",
                              f"Only {len(dat)} SNPs after harmonization. Need ≥ 3.")

        # ---- Step 5: Run MR methods ----
        beta_x = dat["beta_exposure"].tolist()
        se_x = dat["se_exposure"].tolist()
        beta_y = dat["beta_outcome"].tolist()
        se_y = dat["se_outcome"].tolist()

        n_snps = len(beta_x)
        estimates = []

        # IVW
        try:
            ivw = mr_ivw(beta_x, se_y, beta_y)
            estimates.append({
                "method": "IVW", "beta": ivw.beta, "se": ivw.se,
                "odds_ratio": round(math.exp(ivw.beta), 3),
                "ci_lower": ivw.ci_lower, "ci_upper": ivw.ci_upper,
                "p_value": ivw.p_value, "n_snps": n_snps,
            })
            log_lines.append(f"IVW: β={ivw.beta:.4f}, SE={ivw.se:.4f}, P={ivw.p_value:.4g}")
        except Exception as exc:
            log_lines.append(f"IVW ERROR: {exc}")

        # MR-Egger
        if n_snps >= 3 and "MR-Egger" in methods:
            try:
                egger = mr_egger(beta_x, se_y, beta_y)
                estimates.append({
                    "method": "MR-Egger", "beta": egger.beta, "se": egger.se,
                    "odds_ratio": round(math.exp(egger.beta), 3),
                    "ci_lower": egger.ci_lower, "ci_upper": egger.ci_upper,
                    "p_value": egger.p_value, "n_snps": n_snps,
                    "intercept": egger.intercept,
                })
            except Exception as exc:
                log_lines.append(f"MR-Egger ERROR: {exc}")

        # Weighted Median
        if "Weighted Median" in methods:
            try:
                wm = mr_weighted_median(beta_x, se_y, beta_y)
                estimates.append({
                    "method": "Weighted Median", "beta": wm.beta, "se": wm.se,
                    "odds_ratio": round(math.exp(wm.beta), 3),
                    "ci_lower": wm.ci_lower, "ci_upper": wm.ci_upper,
                    "p_value": wm.p_value, "n_snps": n_snps,
                })
            except Exception as exc:
                log_lines.append(f"Weighted Median ERROR: {exc}")

        # Weighted Mode
        if "Weighted Mode" in methods:
            try:
                wmode = mr_weighted_mode(beta_x, se_y, beta_y)
                estimates.append({
                    "method": "Weighted Mode", "beta": wmode.beta, "se": wmode.se,
                    "odds_ratio": round(math.exp(wmode.beta), 3),
                    "ci_lower": wmode.ci_lower, "ci_upper": wmode.ci_upper,
                    "p_value": wmode.p_value, "n_snps": n_snps,
                })
            except Exception as exc:
                log_lines.append(f"Weighted Mode ERROR: {exc}")

        if not estimates:
            return self._fail("ALL_METHODS_FAILED", "All MR methods failed to produce estimates.")

        # ---- Step 6: Sensitivity analysis ----
        ivw_est = next((e for e in estimates if e["method"] == "IVW"), estimates[0])

        # Cochran's Q
        q_result = cochran_q(beta_y, se_y, ivw_est["beta"])
        heterogeneity = [{
            "method": "IVW",
            "q_statistic": q_result["q_statistic"],
            "q_df": q_result["q_df"],
            "q_pval": q_result["q_pval"],
        }]

        # Egger intercept test
        if n_snps >= 3:
            try:
                egger_p, egger_int, egger_int_se = mr_egger_intercept_test(beta_x, se_y, beta_y)
                pleiotropy = {
                    "egger_intercept": egger_int,
                    "se": egger_int_se,
                    "pval": egger_p,
                    "interpretation": "无显著水平多效性证据" if egger_p > 0.05 else "存在显著水平多效性",
                }
            except Exception:
                pleiotropy = {"egger_intercept": 0, "se": 0, "pval": 1.0,
                              "interpretation": "无法计算"}
        else:
            pleiotropy = {"egger_intercept": 0, "se": 0, "pval": 1.0,
                          "interpretation": f"SNP不足 (n={n_snps})，无法评估多效性"}

        # Leave-one-out
        loo_data = []
        for i in range(n_snps):
            idx = [j for j in range(n_snps) if j != i]
            try:
                bx_loo = [beta_x[j] for j in idx]
                by_loo = [beta_y[j] for j in idx]
                se_loo = [se_y[j] for j in idx]
                loo_ivw = mr_ivw(bx_loo, se_loo, by_loo)
                snp_name = dat.iloc[i].get("SNP", f"SNP{i}")
                if isinstance(snp_name, float):
                    snp_name = f"SNP{i}"
                loo_data.append({
                    "snp": str(snp_name),
                    "beta": loo_ivw.beta,
                    "se": loo_ivw.se,
                    "ci_lower": loo_ivw.ci_lower,
                    "ci_upper": loo_ivw.ci_upper,
                })
            except Exception:
                pass

        # ---- Step 7: Generate plots ----
        plot_files = []
        for plot_fn, name in [
            (plot_scatter, "scatter_plot.png"),
            (plot_forest, "forest_plot.png"),
            (plot_funnel, "funnel_plot.png"),
            (plot_leave_one_out, "leave_one_out.png"),
        ]:
            try:
                if name == "scatter_plot.png":
                    path = plot_scatter(beta_x, beta_y, se_x, se_y, ivw_est["beta"], out_dir)
                elif name == "forest_plot.png":
                    path = plot_forest(estimates, out_dir)
                elif name == "funnel_plot.png":
                    path = plot_funnel(beta_y, se_y, out_dir)
                elif name == "leave_one_out.png":
                    path = plot_leave_one_out(loo_data, out_dir)
                else:
                    continue
                plot_files.append(path)
            except Exception as exc:
                log_lines.append(f"Plot {name} ERROR: {exc}")

        # ---- Step 8: Build result ----
        result = {
            "mr_id": mr_id,
            "exposure": exposure_name,
            "outcome": outcome_name,
            "primary_method": "IVW",
            "n_snps": n_snps,
            "beta": ivw_est["beta"],
            "se": ivw_est["se"],
            "p_value": ivw_est["p_value"],
            "odds_ratio": ivw_est.get("odds_ratio", round(math.exp(ivw_est["beta"]), 3)),
            "ci_95": [ivw_est["ci_lower"], ivw_est["ci_upper"]],
            "estimates": estimates,
            "heterogeneity": heterogeneity,
            "pleiotropy": pleiotropy,
            "scatter_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/scatter_plot.png",
            "forest_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/forest_plot.png",
            "funnel_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/funnel_plot.png",
            "leave_one_out_url": f"/api/v1/files/projects/{context.project_id}/outputs/mr/leave_one_out.png",
            "scatter_data_points": [
                {"exposure_effect": bx, "outcome_effect": by, "se": sy}
                for bx, by, sy in zip(beta_x[:50], beta_y[:50], se_y[:50])
            ],
            "forest_data": [{
                "label": est["method"], "beta": est["beta"],
                "ci_lower": est["ci_lower"], "ci_upper": est["ci_upper"],
                "or_label": f"{est.get('odds_ratio', math.exp(est['beta'])):.2f} "
                            f"({est['ci_lower']:.2f}–{est['ci_upper']:.2f})",
                "p_value": est["p_value"],
            } for est in estimates],
            "leave_one_out_data": loo_data,
            "log": log_lines,
            "warnings": warnings,
        }

        with open(os.path.join(out_dir, "mr_summary.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        with open(os.path.join(out_dir, "mr_log.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))

        return SkillOutput(
            status="success",
            summary=result,
            output_files=[
                "mr_summary.json", "mr_log.txt",
                "scatter_plot.png", "forest_plot.png",
                "funnel_plot.png", "leave_one_out.png",
            ],
            warnings=warnings,
            metrics={
                "IVW_beta": ivw_est["beta"],
                "IVW_p": ivw_est["p_value"],
                "OR": ivw_est.get("odds_ratio", math.exp(ivw_est["beta"])),
                "cochran_q_p": q_result["q_pval"],
                "egger_intercept_p": pleiotropy.get("pval", 1.0),
                "n_snps": n_snps,
            },
        )

    def _fail(self, error_code: str, error_message: str) -> SkillOutput:
        return SkillOutput(
            status="failed",
            error_code=error_code,
            error_message=error_message,
        )


registry.register(TwoSampleMRSkill())
