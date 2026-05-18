"""
AI Skill 实现包

每个子模块定义一个 Skill 子类并通过装饰器/import 自动注册到 SkillRegistry。

import 此包即可完成所有 Skill 的注册：
    import backend.app.ai.skills  # noqa: F401 — 触发各模块的 register() 调用
"""

from backend.app.ai.skills.image_segmentation import ImageSegmentationSkill
from backend.app.ai.skills.phenotype_quantification import PhenotypeQuantificationSkill
from backend.app.ai.skills.gwas_analysis import GWASAnalysisSkill
from backend.app.ai.skills.two_sample_mr import TwoSampleMRSkill
from backend.app.ai.skills.mediation_mr import MediationMRSkill
from backend.app.ai.skills.risk_modeling import RiskModelingSkill
from backend.app.ai.skills.report_generation import ReportGenerationSkill
from backend.app.ai.skills.result_interpretation import ResultInterpretationSkill

__all__ = [
    "ImageSegmentationSkill",
    "PhenotypeQuantificationSkill",
    "GWASAnalysisSkill",
    "TwoSampleMRSkill",
    "MediationMRSkill",
    "RiskModelingSkill",
    "ReportGenerationSkill",
    "ResultInterpretationSkill",
]
