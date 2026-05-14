from backend.app.tasks.base import BaseSkillRunner, register
from backend.app.config import ANALYSIS_SCRIPTS_DIR


@register
class SegmentationSkillRunner(BaseSkillRunner):
    task_type = "image_segmentation"
    script_path = "segmentation/mock_segmentation.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        script = ANALYSIS_SCRIPTS_DIR / self.script_path
        out_dir = f"storage/projects/{project_id}/outputs/segmentation"
        return [
            "python", str(script),
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
