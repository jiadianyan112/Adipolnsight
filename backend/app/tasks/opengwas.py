from backend.app.tasks.base import BaseSkillRunner, register


@register
class OpenGWASSkillRunner(BaseSkillRunner):
    task_type = "opengwas_fetch"
    script_path = "opengwas/mock_opengwas_fetch.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        params = inputs.get("parameters", {})
        outcome_id = params.get("outcome_id", "ukb-b-12141")
        out_dir = f"storage/projects/{project_id}/outputs/opengwas"
        return [
            "python", str(self.script_path),
            "--outcome-id", outcome_id,
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
