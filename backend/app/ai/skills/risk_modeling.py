"""
C6 · 疾病风险建模 Skill

Mock 模式：生成 OLS 线性回归 + RCS 限制性立方样条 + 多分类 Logistic 回归结果。
Real 模式：调用 Python statsmodels / scikit-learn 或 R rms/nnet 包。

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


QUARTILE_CUTOFFS = [5.2, 8.1, 12.8, 35.0]  # 肝脏 PDFF 四分位 cutoff (%)
RCS_KNOTS_DEFAULT = [10, 50, 90]  # PDFF 分位数百分位


class RiskModelingSkill(Skill):
    """C6 · 疾病风险建模"""

    @property
    def name(self) -> str:
        return "Risk Modeling"

    @property
    def capability_type(self) -> str:
        return "risk_modeling"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        for key in ["project_id", "exposure", "outcome"]:
            if key not in input_data:
                return False
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["project_id", "exposure", "outcome"],
            "properties": {
                "project_id": {"type": "integer"},
                "exposure": {"type": "string", "description": "暴露名称，如 Liver_PDFF"},
                "outcome": {"type": "string", "description": "结局名称"},
                "outcomes": {
                    "type": "array", "items": {"type": "string"},
                    "default": ["BMD", "TBS", "Osteopenia", "Osteoporosis"],
                    "description": "结局变量列表",
                },
                "model_types": {
                    "type": "array", "items": {"enum": ["OLS", "RCS", "MultinomialLogistic"]},
                    "default": ["OLS", "RCS", "MultinomialLogistic"],
                },
                "grouping": {"enum": ["quartile", "tertile", "median"], "default": "quartile"},
                "covariate_model": {
                    "type": "array", "items": {"type": "string"},
                    "default": ["age", "sex", "bmi", "smoking", "alcohol", "physical_activity"],
                },
                "quartile_groups": {
                    "type": "array", "items": {"type": "number"},
                    "default": [5.2, 8.1, 12.8, 35.0],
                },
            },
        }

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        if self.mode == "mock":
            return self._run_mock(input_data, context)
        else:
            return self._run_real(input_data, context)

    # ==== Mock 实现 ====

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        time.sleep(0.3)
        exposure = input_data.get("exposure", "Liver_PDFF")
        outcomes = input_data.get("outcomes", ["BMD", "TBS", "Osteopenia", "Osteoporosis"])
        model_types = input_data.get("model_types", ["OLS", "RCS", "MultinomialLogistic"])
        grouping = input_data.get("grouping", "quartile")
        covariates = input_data.get("covariate_model", ["age", "sex", "bmi", "smoking", "alcohol", "physical_activity"])
        quartiles = input_data.get("quartile_groups", QUARTILE_CUTOFFS)

        # 1. OLS 结果
        ols_results = self._generate_ols(outcomes)

        # 2. RCS 曲线数据
        rcs_curve_data = self._generate_rcs_curve()

        # 3. 多分类 Logistic (Osteopenia / Osteoporosis vs Normal)
        logistic_results = self._generate_logistic()

        # 4. 调整后 OR（四分位分层）
        adjusted_ors = self._generate_adjusted_or(quartiles)

        # 5. 汇总解读
        interpretation = self._generate_interpretation(exposure, adjusted_ors, ols_results)

        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        risk_id = f"risk_{uuid.uuid4().hex[:8]}"

        result = {
            "risk_id": risk_id,
            "exposure": exposure,
            "outcome": ", ".join(outcomes),
            "outcomes": outcomes,
            "model_types": model_types,
            "grouping": grouping,
            "covariate_model": covariates,
            "quartile_groups": quartiles,
            "ols_results": ols_results,
            "rcs_curve_data": rcs_curve_data,
            "multinomial_logistic_results": logistic_results,
            "adjusted_odds_ratios": adjusted_ors,
            "interpretation_summary": interpretation,
            "rcs_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/risk_modeling/rcs_curve.png",
            "or_forest_plot_url": f"/api/v1/files/projects/{context.project_id}/outputs/risk_modeling/or_forest.png",
        }

        with open(os.path.join(out_dir, "risk_summary.json"), "w") as f:
            json.dump(result, f, indent=2)

        return SkillOutput(
            status="success",
            summary=result,
            output_files=["ols_results.csv", "rcs_results.csv", "risk_summary.json"],
            metrics={
                "osteoporosis_aor_q4": adjusted_ors[-1]["osteoporosis_or"] if adjusted_ors else 1.0,
                "bmd_beta_per_sd": ols_results[0]["beta"] if ols_results else 0,
                "auc": logistic_results[0]["auc"] if logistic_results else 0,
            },
        )

    # ==== Mock 数据生成器 ====

    def _generate_ols(self, outcomes: List[str]) -> List[Dict[str, Any]]:
        """OLS 线性回归：PDFF 每增加 1 SD，各结局的 β 变化"""
        results = []
        configs = {
            "BMD": {"beta": -0.12, "se": 0.03, "p": 5e-5, "r2": 0.18},
            "TBS": {"beta": -0.09, "se": 0.02, "p": 2e-4, "r2": 0.14},
            "Osteopenia": {"beta": 0.18, "se": 0.04, "p": 8e-6, "r2": 0.22},
            "Osteoporosis": {"beta": 0.25, "se": 0.05, "p": 1e-6, "r2": 0.28},
        }
        for outcome in outcomes:
            cfg = configs.get(outcome, {"beta": 0.1, "se": 0.04, "p": 0.01, "r2": 0.10})
            results.append({
                "outcome": outcome,
                "model": "OLS",
                "beta": round(random.gauss(cfg["beta"], abs(cfg["beta"]) * 0.2), 4),
                "se": round(random.gauss(cfg["se"], cfg["se"] * 0.1), 4),
                "p_value": round(10 ** (-random.uniform(3, 6)), 6),
                "r_squared": round(random.gauss(cfg["r2"], 0.02), 3),
                "n_observations": random.randint(35000, 42000),
                "interpretation": self._ols_interpretation(outcome),
            })
        return results

    def _ols_interpretation(self, outcome: str) -> str:
        maps = {
            "BMD": "肝脏 PDFF 每增加 1 SD，骨密度显著降低，提示肝脂积累对骨骼健康有独立负面影响",
            "TBS": "肝脏 PDFF 每升高 1 SD，骨小梁评分显著下降，反映骨微结构受损",
            "Osteopenia": "肝脏 PDFF 每增加 1 SD，骨量减少风险显著增加",
            "Osteoporosis": "肝脏 PDFF 每增加 1 SD，骨质疏松风险显著增加，呈剂量-反应关系",
        }
        return maps.get(outcome, f"肝脏 PDFF 与 {outcome} 存在显著关联")

    def _generate_rcs_curve(self) -> List[Dict[str, Any]]:
        """RCS 限制性立方样条：PDFF 连续值与结局的非线性关系"""
        points = []
        for pdf_pct in range(2, 36, 1):
            # 线性部分 + 非线性偏离
            linear = pdf_pct * 0.008
            nonlinear = 0.002 * (pdf_pct - 10) ** 2 / 50 if pdf_pct > 10 else 0
            log_or = linear + nonlinear + random.gauss(0, 0.02)
            or_val = math.exp(log_or)
            points.append({
                "pdf_pct": pdf_pct,
                "log_odds_ratio": round(log_or, 4),
                "odds_ratio": round(or_val, 3),
                "ci_lower": round(or_val * 0.85, 3),
                "ci_upper": round(or_val * 1.18, 3),
            })
        return points

    def _generate_logistic(self) -> List[Dict[str, Any]]:
        """多分类 Logistic 回归结果"""
        return [
            {
                "outcome": "Osteopenia",
                "reference": "Normal BMD",
                "beta": round(random.gauss(0.35, 0.08), 4),
                "se": round(random.uniform(0.06, 0.10), 4),
                "odds_ratio": round(random.gauss(1.42, 0.10), 2),
                "ci_lower": round(random.uniform(1.15, 1.30), 2),
                "ci_upper": round(random.uniform(1.55, 1.75), 2),
                "p_value": round(10 ** (-random.uniform(2.5, 4.5)), 6),
                "auc": round(random.gauss(0.72, 0.03), 3),
            },
            {
                "outcome": "Osteoporosis",
                "reference": "Normal BMD",
                "beta": round(random.gauss(0.52, 0.10), 4),
                "se": round(random.uniform(0.08, 0.12), 4),
                "odds_ratio": round(random.gauss(1.68, 0.15), 2),
                "ci_lower": round(random.uniform(1.35, 1.55), 2),
                "ci_upper": round(random.uniform(1.85, 2.15), 2),
                "p_value": round(10 ** (-random.uniform(3.5, 6.0)), 6),
                "auc": round(random.gauss(0.78, 0.03), 3),
            },
        ]

    def _generate_adjusted_or(self, quartiles: List[float]) -> List[Dict[str, Any]]:
        """调整后 OR（PDFF 四分位分层）"""
        labels = ["Q1 (最低)", "Q2", "Q3", "Q4 (最高)"]
        results = []
        for i, q in enumerate(quartiles):
            ref = 1.0 if i == 0 else random.gauss(1.0 + i * 0.15, 0.05)
            results.append({
                "quartile": f"Q{i + 1}",
                "label": labels[i] if i < len(labels) else f"Q{i+1}",
                "pdf_range": f"< {q}%" if i == 0 else f"{quartiles[i-1]:.1f}–{q:.1f}%",
                "osteopenia_or": round(ref, 2) if ref > 1 else 1.0,
                "osteopenia_ci_lower": round(max(0.8, ref - 0.15), 2),
                "osteopenia_ci_upper": round(ref + 0.20, 2),
                "osteoporosis_or": round(ref * 1.12, 2) if ref > 1 else 1.0,
                "osteoporosis_ci_lower": round(max(0.8, ref * 1.12 - 0.20), 2),
                "osteoporosis_ci_upper": round(ref * 1.12 + 0.25, 2),
                "p_trend": round(10 ** (-random.uniform(2, 5)), 6),
            })
        return results

    def _generate_interpretation(self, exposure: str, ors: List[Dict[str, Any]], ols: List[Dict[str, Any]]) -> str:
        q4_or = ors[-1]["osteoporosis_or"] if ors else 1.5
        bmd_beta = ols[0]["beta"] if ols else -0.12
        risk_level = "高" if q4_or > 1.5 else "中"

        return (
            f"基于 UK Biobank 队列 {40000}+ 样本的多变量回归分析，"
            f"肝脏 {exposure} 与骨质疏松风险呈显著正相关。"
            f"Q4（最高四分位）人群的骨质疏松风险是 Q1（最低四分位）的 {q4_or:.1f} 倍"
            f"（95% CI: {ors[-1]['osteoporosis_ci_lower']:.1f}–{ors[-1]['osteoporosis_ci_upper']:.1f}）。"
            f"OLS 回归显示 PDFF 每增加 1 SD，骨密度下降 {abs(bmd_beta):.2f} g/cm³。"
            f"RCS 分析提示剂量-反应关系在 PDFF > 10% 时趋于平台，"
            f"建议以 PDFF = 10% 作为临床风险分层阈值。"
            f"综合评估：该队列的骨质疏松风险等级为 **{risk_level}风险**。"
            f"MR 分析支持该关联的因果推断（IVW β = 0.38, p < 0.001），"
            f"中介分析表明部分效应通过血浆蛋白（POR、NAAA 等）介导。"
        )

    # ==== Real 实现（预留） ====

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """
        真实模式：调用 Python statsmodels / sklearn 或 R rms/nnet 包。

        Python 实现示例：
            import statsmodels.api as sm
            model = sm.OLS(y, X).fit()
            # RCS via patsy: cr(pdf, df=3)

        替换方式：
        1. 将 self.mode 改为 "script" 或 "model"
        2. 读取 storage/projects/{id}/outputs/ 下的表型+协变量数据
        3. 运行 OLS + RCS + Multinomial Logistic
        4. 返回 SkillOutput

        暂未实现。
        """
        return SkillOutput(
            status="failed",
            error_code="NOT_IMPLEMENTED",
            error_message="Real risk modeling (statsmodels/sklearn) not yet integrated. Switch mode to 'mock'.",
        )


registry.register(RiskModelingSkill())
