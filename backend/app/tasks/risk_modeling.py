from backend.app.tasks.base import BaseSkillRunner, register


@register
class RiskModelSkillRunner(BaseSkillRunner):
    task_type = "risk_modeling"
    script_path = "risk_modeling/mock_risk_modeling.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        exposure = params.get("exposure", "Liver_PDFF")
        outcome = params.get("outcome", "Osteoporosis")
        out_dir = f"storage/projects/{project_id}/outputs/risk_modeling"
        return [
            "python", str(self.script_path),
            "--exposure", exposure,
            "--outcome", outcome,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
