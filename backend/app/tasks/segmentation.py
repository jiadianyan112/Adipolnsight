from backend.app.tasks.base import BaseSkillRunner, register


@register
class SegmentationSkillRunner(BaseSkillRunner):
    task_type = "image_segmentation"
    script_path = "segmentation/mock_segmentation.py"

    def build_command(self, inputs: dict) -> list[str]:
        project_id = inputs["project_id"]
        out_dir = f"storage/projects/{project_id}/outputs/segmentation"
        return [
            "python", str(self.script_path),
            "--output-dir", out_dir,
            "--task-id", str(inputs.get("task_id", "")),
        ]
