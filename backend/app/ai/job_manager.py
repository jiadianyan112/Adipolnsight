"""
AI Job Manager — 统一异步任务管理

所有 AI 能力通过 JobManager 以异步任务方式运行。
当前使用内存存储 + 后台线程执行，预留 JobStore 抽象接口用于后续
替换为 SQLAlchemy / Redis / Celery / BullMQ。

用法：
    from backend.app.ai.job_manager import job_manager

    # 创建并运行
    job = job_manager.create_job("gwas_analysis", {"phenotype": "Liver_PDFF"})
    job_manager.run_job(job.job_id)

    # 前端轮询
    job = job_manager.get_job(job_id)
    print(job.status, job.progress)  # "running", 45

    # 获取结果
    result = job_manager.get_result(job_id)
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from backend.app.ai.base import CapabilityType, SkillContext, SkillOutput
from backend.app.ai.registry import registry as skill_registry


# ===== 状态枚举 =====

class JobStatus:
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    ALL = {QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED}
    TERMINAL = {SUCCEEDED, FAILED, CANCELLED}
    ACTIVE = {QUEUED, RUNNING}


# ===== Job 数据结构 =====

@dataclass
class Job:
    """统一的 AI Job 数据结构"""

    job_id: str
    capability_type: CapabilityType
    status: str = JobStatus.QUEUED
    progress: int = 0
    progress_stage: str = "初始化"

    # 输入
    input: Dict[str, Any] = field(default_factory=dict)

    # 输出
    result: Optional[Dict[str, Any]] = None
    output_files: List[str] = field(default_factory=list)

    # 错误
    error_code: str = ""
    error_message: str = ""
    user_facing_error: Optional[Dict[str, Any]] = None   # error_explainer 生成

    # 时间戳
    created_at: str = ""
    started_at: str = ""
    finished_at: str = ""
    updated_at: str = ""

    # 元信息
    project_id: int = 0

    def __post_init__(self):
        now = self._now()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def touch(self):
        self.updated_at = self._now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "capability_type": self.capability_type,
            "status": self.status,
            "progress": self.progress,
            "progress_stage": self.progress_stage,
            "input": self.input,
            "result": self.result,
            "output_files": self.output_files,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "user_facing_error": self.user_facing_error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "updated_at": self.updated_at,
            "project_id": self.project_id,
        }

    @classmethod
    def create(
        cls,
        capability_type: CapabilityType,
        input_data: Dict[str, Any],
        project_id: int = 0,
    ) -> "Job":
        return cls(
            job_id=str(uuid.uuid4())[:8],
            capability_type=capability_type,
            input=input_data,
            project_id=project_id,
        )


# ===== JobStore 抽象接口 =====

class JobStore(ABC):
    """
    Job 存储抽象接口。

    当前实现：InMemoryJobStore (dict)
    预留替换：SQLAlchemyJobStore, RedisJobStore
    """

    @abstractmethod
    def save(self, job: Job) -> None:
        """保存 Job（新增或更新）"""
        ...

    @abstractmethod
    def get(self, job_id: str) -> Optional[Job]:
        """按 ID 获取 Job"""
        ...

    @abstractmethod
    def list_all(self) -> List[Job]:
        """列出全部 Job"""
        ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> List[Job]:
        """按项目列出 Job"""
        ...

    @abstractmethod
    def delete(self, job_id: str) -> bool:
        """删除 Job"""
        ...


# ===== 内存存储实现 =====

class InMemoryJobStore(JobStore):
    """基于 dict 的内存 Job 存储"""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def save(self, job: Job) -> None:
        job.touch()
        with self._lock:
            self._jobs[job.job_id] = job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_all(self) -> List[Job]:
        with self._lock:
            return sorted(
                self._jobs.values(),
                key=lambda j: j.created_at,
                reverse=True,
            )

    def list_by_project(self, project_id: int) -> List[Job]:
        with self._lock:
            return sorted(
                [j for j in self._jobs.values() if j.project_id == project_id],
                key=lambda j: j.created_at,
                reverse=True,
            )

    def delete(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False


# ===== JobManager =====

class JobManager:
    """
    AI Job 管理器

    职责：
    - 创建 Job
    - 后台异步执行（线程池）
    - 进度更新
    - 结果/错误存取
    - 取消支持

    不负责：
    - HTTP 路由（由 api 层处理）
    - 数据持久化（委托给 JobStore）
    - AI 逻辑（委托给 SkillRegistry）
    """

    def __init__(
        self,
        store: Optional[JobStore] = None,
        on_progress: Optional[Callable[[Job], None]] = None,
        on_complete: Optional[Callable[[Job], None]] = None,
    ):
        self._store = store or InMemoryJobStore()
        self._running: Dict[str, threading.Thread] = {}
        self._cancel_flags: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

        # 可选回调（用于外部监听，如 WebSocket 推送）
        self.on_progress = on_progress
        self.on_complete = on_complete

    @property
    def store(self) -> JobStore:
        return self._store

    # ===== 创建 =====

    def create_job(
        self,
        capability_type: str,
        input_data: Dict[str, Any],
        project_id: int = 0,
    ) -> Job:
        """创建一个新 Job（status=queued），不自动运行。"""
        # 校验 capability 是否已注册
        if not skill_registry.has(capability_type):
            raise ValueError(
                f"Unknown capability '{capability_type}'. "
                f"Available: {[s['capability_type'] for s in skill_registry.list_all()]}"
            )

        job = Job.create(capability_type, input_data, project_id)
        self._store.save(job)
        return job

    # ===== 运行 =====

    def run_job(self, job_id: str) -> bool:
        """
        在后台线程中启动 Job。

        返回 True 表示已启动，False 表示 Job 不存在或状态不允许。
        """
        job = self._store.get(job_id)
        if job is None:
            return False
        if job.status not in JobStatus.ACTIVE:
            return False

        cancel_flag = threading.Event()
        with self._lock:
            self._cancel_flags[job_id] = cancel_flag

        thread = threading.Thread(
            target=self._execute_job,
            args=(job_id, cancel_flag),
            daemon=True,
        )
        with self._lock:
            self._running[job_id] = thread
        thread.start()
        return True

    def _execute_job(self, job_id: str, cancel_flag: threading.Event):
        """后台执行线程"""
        job = self._store.get(job_id)
        if job is None:
            return

        # 标记 running
        job.status = JobStatus.RUNNING
        job.started_at = Job._now()
        self._update_progress(job, 5, "开始执行")

        try:
            skill = skill_registry.get(job.capability_type)
            if skill is None:
                self._fail_job(job, "ADAPTER_NOT_FOUND",
                               f"No skill for '{job.capability_type}'")
                return

            # 校验
            self._update_progress(job, 10, "校验输入")
            if cancel_flag.is_set():
                self._cancel_job_internal(job)
                return
            time.sleep(0.1)  # mock 延迟

            if not skill.validate_input(job.input):
                self._fail_job(job, "INVALID_INPUT", "Input validation failed")
                return

            # 构建
            self._update_progress(job, 20, "构建执行命令")
            if cancel_flag.is_set():
                self._cancel_job_internal(job)
                return
            time.sleep(0.1)

            # 提交
            self._update_progress(job, 30, "已提交执行")
            if cancel_flag.is_set():
                self._cancel_job_internal(job)
                return
            time.sleep(0.1)

            # 处理中（skill run）
            self._update_progress(job, 40, "处理中")
            output_dir = os.path.join(
                "storage", "projects", str(job.project_id),
                "outputs", job.capability_type,
            )
            os.makedirs(output_dir, exist_ok=True)

            context = SkillContext(
                project_id=job.project_id,
                task_id=0,
                output_dir=output_dir,
            )

            # 在 skill.run 期间模拟多次进度更新
            def _simulate_progress():
                stages = [(50, "处理中 (25%)"), (60, "处理中 (50%)"), (70, "解析结果")]
                for pct, stage in stages:
                    if cancel_flag.is_set():
                        return
                    time.sleep(0.15)
                    self._update_progress(job, pct, stage)

            # 并行：进度模拟 + skill 执行
            progress_thread = threading.Thread(target=_simulate_progress)
            progress_thread.start()

            output = skill.run(job.input, context)
            progress_thread.join(timeout=5)

            if cancel_flag.is_set():
                self._cancel_job_internal(job)
                return

            if output.status == "success":
                self._update_progress(job, 90, "持久化结果")
                time.sleep(0.1)
                job.status = JobStatus.SUCCEEDED
                job.progress = 100
                job.progress_stage = "完成"
                job.result = output.summary
                job.output_files = output.output_files
                job.finished_at = Job._now()
                job.touch()
                self._store.save(job)
                self._notify_complete(job)
            else:
                self._fail_job(job, output.error_code or "SKILL_EXECUTION_ERROR",
                               output.error_message)

        except Exception as exc:
            self._fail_job(job, "SKILL_EXECUTION_ERROR",
                           f"{type(exc).__name__}: {str(exc)}")
        finally:
            with self._lock:
                self._running.pop(job_id, None)
                self._cancel_flags.pop(job_id, None)

    def _update_progress(self, job: Job, progress: int, stage: str):
        job.progress = min(100, progress)
        job.progress_stage = stage
        job.touch()
        self._store.save(job)
        if self.on_progress:
            try:
                self.on_progress(job)
            except Exception:
                pass

    def _fail_job(self, job: Job, error_code: str, error_message: str):
        job.status = JobStatus.FAILED
        job.progress = 0
        job.progress_stage = "失败"
        job.error_code = error_code
        job.error_message = error_message

        # 生成用户友好错误解释
        try:
            from backend.app.ai.llm.error_explainer import (
                error_explainer,
                ErrorExplanationInput,
            )
            explanation = error_explainer.explain(ErrorExplanationInput(
                error_code=error_code,
                technical_message=error_message,
                job_type=job.capability_type,
                stage=job.progress_stage,
                user_action="",
                context={"job_id": job.job_id, "project_id": job.project_id},
            ))
            job.user_facing_error = {
                "user_message": explanation.user_message,
                "possible_reasons": explanation.possible_reasons,
                "next_actions": explanation.next_actions,
                "technical_summary": explanation.technical_summary,
            }
        except Exception:
            job.user_facing_error = None

        job.finished_at = Job._now()
        job.touch()
        self._store.save(job)
        self._notify_complete(job)

    def _cancel_job_internal(self, job: Job):
        job.status = JobStatus.CANCELLED
        job.progress = 0
        job.progress_stage = "已取消"
        job.error_message = "用户手动取消"
        job.finished_at = Job._now()
        job.touch()
        self._store.save(job)
        self._notify_complete(job)

    def _notify_complete(self, job: Job):
        if self.on_complete:
            try:
                self.on_complete(job)
            except Exception:
                pass

    # ===== 查询 =====

    def get_job(self, job_id: str) -> Optional[Job]:
        """查询 Job 当前状态（供前端轮询）"""
        return self._store.get(job_id)

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Job 执行结果。

        仅在 status=succeeded 时返回 result dict。
        非终态返回 None。
        """
        job = self._store.get(job_id)
        if job is None:
            return None
        if job.status != JobStatus.SUCCEEDED:
            return None
        return {
            "job_id": job.job_id,
            "capability_type": job.capability_type,
            "status": job.status,
            "result": job.result,
            "output_files": job.output_files,
            "created_at": job.created_at,
            "finished_at": job.finished_at,
        }

    def list_jobs(self, project_id: Optional[int] = None) -> List[Job]:
        """列出 Job（可按项目过滤）"""
        if project_id:
            return self._store.list_by_project(project_id)
        return self._store.list_all()

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Job 状态摘要（供前端轮询）。

        返回结构比 get_result() 轻量，包含 progress 用于展示进度条。
        """
        job = self._store.get(job_id)
        if job is None:
            return None
        return {
            "job_id": job.job_id,
            "capability_type": job.capability_type,
            "status": job.status,
            "progress": job.progress,
            "progress_stage": job.progress_stage,
            "error_code": job.error_code,
            "error_message": job.error_message,
            "user_facing_error": job.user_facing_error,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "updated_at": job.updated_at,
        }

    # ===== 取消 =====

    def cancel_job(self, job_id: str) -> bool:
        """
        取消一个 queued 或 running 的 Job。

        返回 True 表示取消信号已发送。
        对于 running 任务，取消在下一个检查点生效。
        """
        job = self._store.get(job_id)
        if job is None:
            return False
        if job.status in JobStatus.TERMINAL:
            return False

        with self._lock:
            flag = self._cancel_flags.get(job_id)
        if flag is not None:
            flag.set()
            return True

        # 如果还没有 cancel flag（job 是 queued 还没 run），直接标记
        job.status = JobStatus.CANCELLED
        job.progress_stage = "已取消"
        job.error_message = "用户手动取消"
        job.finished_at = Job._now()
        job.touch()
        self._store.save(job)
        return True

    # ===== 管理 =====

    def is_running(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._running

    def active_count(self) -> int:
        with self._lock:
            return len(self._running)

    def clean_terminal_jobs(self) -> int:
        """清理所有终态 Job。返回清理数量。"""
        all_jobs = self._store.list_all()
        count = 0
        for job in all_jobs:
            if job.status in JobStatus.TERMINAL:
                self._store.delete(job.job_id)
                count += 1
        return count


# ===== 全局单例 =====

# 替换 JobStore 为 SQLAlchemy / Redis 时只需改这一行：
# job_manager = JobManager(store=SQLAlchemyJobStore(db_session_factory))
job_manager = JobManager(store=InMemoryJobStore())
