from backend.app.tasks.base import BaseSkillRunner, register
from backend.app.config import ANALYSIS_SCRIPTS_DIR


@register
class MediationMRSkillRunner(BaseSkillRunner):
    task_type = "mediation_mr"
    script_path = "mediation_mr/mock_mediation_mr.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        script = ANALYSIS_SCRIPTS_DIR / self.script_path
        params = inputs.get("parameters", {})
        exposure = params.get("exposure", "Liver_PDFF")
        outcome = params.get("outcome", "Osteoporosis")
        out_dir = f"storage/projects/{project_id}/outputs/mediation_mr"
        return [
            "python", str(script),
            "--exposure", exposure,
            "--outcome", outcome,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
