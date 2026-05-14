from backend.app.tasks.base import BaseSkillRunner, register
from backend.app.config import ANALYSIS_SCRIPTS_DIR


@register
class GWASSkillRunner(BaseSkillRunner):
    task_type = "gwas_analysis"
    script_path = "gwas/mock_gwas.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        script = ANALYSIS_SCRIPTS_DIR / self.script_path
        params = inputs.get("parameters", {})
        phenotype = params.get("phenotype", "Liver_PDFF")
        out_dir = f"storage/projects/{project_id}/outputs/gwas"
        return [
            "python", str(script),
            "--phenotype", phenotype,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
