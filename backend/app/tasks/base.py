import json
import subprocess
import uuid
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.config import ANALYSIS_SCRIPTS_DIR, STORAGE_DIR
from backend.app.models.analysis_task import AnalysisTask
from backend.app.services.task_orchestrator import TaskOrchestrator


class BaseSkillRunner:
    task_type: str
    script_path: str

    def prepare_inputs(self, task: AnalysisTask) -> dict:
        return json.loads(task.input_json)

    def build_command(self, inputs: dict) -> list[str]:
        return ["python", str(ANALYSIS_SCRIPTS_DIR / self.script_path)]

    def run(self, cmd: list[str], cwd: str = None) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=cwd)

    def parse_outputs(self, stdout: str) -> dict:
        lines = stdout.strip().split("\n")
        last_line = lines[-1] if lines else "{}"
        return json.loads(last_line)

    def execute(self, task: AnalysisTask, orch: TaskOrchestrator, db: Session):
        orch.update_progress(task.id, 10)
        inputs = self.prepare_inputs(task)
        orch.update_progress(task.id, 20)
        cmd = self.build_command(inputs)
        out_dir = STORAGE_DIR / "projects" / str(task.project_id) / "outputs" / task.task_type
        out_dir.mkdir(parents=True, exist_ok=True)
        orch.update_progress(task.id, 30)

        try:
            result = self.run(cmd, cwd=str(out_dir))
        except subprocess.TimeoutExpired:
            orch.mark_failed(task.id, "TASK_TIMEOUT", "Task exceeded 300s limit")
            return
        except FileNotFoundError:
            orch.mark_failed(task.id, "SCRIPT_NOT_FOUND", f"Script not found: {self.script_path}")
            return

        log_dir = out_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "run.log").write_text(result.stdout + "\n" + result.stderr)
        (log_dir / "command.txt").write_text(" ".join(cmd))

        orch.update_progress(task.id, 70)

        if result.returncode != 0:
            orch.mark_failed(task.id, "SCRIPT_EXECUTION_FAILED", result.stderr[:500])
            return

        try:
            output = self.parse_outputs(result.stdout)
        except (json.JSONDecodeError, IndexError):
            orch.mark_failed(task.id, "OUTPUT_JSON_INVALID", "Failed to parse stdout JSON")
            return

        orch.update_progress(task.id, 90)
        orch.mark_success(task.id, output)


RUNNER_REGISTRY = {}


def register(runner_cls):
    inst = runner_cls()
    RUNNER_REGISTRY[inst.task_type] = inst
    return runner_cls


def dispatch_skill(task: AnalysisTask, db: Session):
    orch = TaskOrchestrator(db)
    runner = RUNNER_REGISTRY.get(task.task_type)
    if not runner:
        orch.mark_failed(task.id, "SCRIPT_NOT_FOUND", f"No runner for {task.task_type}")
        return
    runner.execute(task, orch, db)
