from backend.app.tasks.base import BaseSkillRunner, register
from backend.app.config import ANALYSIS_SCRIPTS_DIR


@register
class ReportSkillRunner(BaseSkillRunner):
    task_type = "report_generation"
    script_path = "report/mock_report.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        script = ANALYSIS_SCRIPTS_DIR / self.script_path
        out_dir = f"storage/projects/{project_id}/outputs/report"
        return [
            "python", str(script),
            "--project-id", str(project_id),
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
