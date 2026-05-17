"""
C2 · 多部位脂肪表型量化 Skill

Mock 模式：基于分割结果计算 8 项定量表型指标。
Real 模式：调用标准化后处理 pipeline。
"""

import json
import os
import random
import time
from typing import Any, Dict

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry


class PhenotypeQuantificationSkill(Skill):
    """C2 · 脂肪表型量化"""

    @property
    def name(self) -> str:
        return "Phenotype Quantification"

    @property
    def capability_type(self) -> str:
        return "phenotype_quantification"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "project_id" in input_data

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["project_id"],
            "properties": {
                "project_id": {"type": "integer"},
                "segmentation_job_id": {"type": "integer", "description": "已完成的分割任务 ID"},
            },
        }

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        if self.mode == "mock":
            return self._run_mock(input_data, context)
        else:
            return self._run_real(input_data, context)

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        time.sleep(0.2)

        phenotype = {
            "liver_pdff": round(random.uniform(8.0, 15.0), 2),
            "pancreatic_pdff": round(random.uniform(5.0, 11.0), 2),
            "visceral_fat_volume": round(random.uniform(2.0, 5.0), 2),
            "subcutaneous_fat_volume": round(random.uniform(5.0, 9.0), 2),
            "bone_marrow_fat_fraction": round(random.uniform(55.0, 75.0), 1),
            "total_body_fat_pct": round(random.uniform(28.0, 38.0), 1),
            "muscle_volume": round(random.uniform(20.0, 30.0), 1),
            "sat_vat_ratio": round(random.uniform(2.0, 3.5), 2),
            "bone_density": round(random.uniform(1.1, 1.4), 2),
        }

        os.makedirs(context.output_dir, exist_ok=True)
        summary_path = os.path.join(context.output_dir, "phenotype_summary.json")
        with open(summary_path, "w") as f:
            json.dump(phenotype, f, indent=2)

        csv_path = os.path.join(context.output_dir, "phenotype_detail.csv")
        with open(csv_path, "w") as f:
            f.write("subject_id," + ",".join(phenotype.keys()) + "\n")
            f.write(f"DEMO_001," + ",".join(str(v) for v in phenotype.values()) + "\n")

        return SkillOutput(
            status="success",
            summary=phenotype,
            output_files=["phenotype_summary.json", "phenotype_detail.csv"],
            metrics={
                "total_body_fat_pct": phenotype["total_body_fat_pct"],
                "visceral_fat_volume": phenotype["visceral_fat_volume"],
                "liver_pdff": phenotype["liver_pdff"],
            },
        )

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        return SkillOutput(
            status="failed",
            error_code="NOT_IMPLEMENTED",
            error_message="Real phenotype quantification not yet integrated. Switch mode to 'mock'.",
        )


registry.register(PhenotypeQuantificationSkill())
