from backend.app.tasks.base import BaseSkillRunner, register


@register
class MediationMRSkillRunner(BaseSkillRunner):
    task_type = "mediation_mr"
    script_path = "mediation_mr/mock_mediation_mr.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        exposure = params.get("exposure", "Liver_PDFF")
        outcome = params.get("outcome", "Osteoporosis")
        out_dir = f"storage/projects/{project_id}/outputs/mediation_mr"
        return [
            "python", str(self.script_path),
            "--exposure", exposure,
            "--outcome", outcome,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
