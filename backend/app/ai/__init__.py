"""
AdipoInsight AI Skill System

统一 AI 能力注册与调用模块。

组件：
- Skill / SkillOutput / SkillContext — AI 能力抽象基类
- SkillRegistry / registry — 注册表（自动发现 7 个 Skill）
- JobManager / job_manager — 异步任务管理（创建/运行/轮询/取消）
- JobStore / InMemoryJobStore — 任务存储（可替换为 SQLAlchemy/Redis）

用法：
    # 直接调用 Skill（同步）
    from backend.app.ai import registry
    output = registry.dispatch("gwas_analysis", input_data, context)

    # 通过 JobManager 异步执行（推荐，支持轮询）
    from backend.app.ai import job_manager
    job = job_manager.create_job("gwas_analysis", {"phenotype": "Liver_PDFF"})
    job_manager.run_job(job.job_id)
"""

from backend.app.ai.base import Skill, SkillMode, SkillOutput, SkillContext
from backend.app.ai.registry import SkillRegistry, registry
from backend.app.ai.job_manager import (
    Job,
    JobStatus,
    JobStore,
    InMemoryJobStore,
    JobManager,
    job_manager,
)

__all__ = [
    # base
    "Skill",
    "SkillMode",
    "SkillOutput",
    "SkillContext",
    # registry
    "SkillRegistry",
    "registry",
    # job_manager
    "Job",
    "JobStatus",
    "JobStore",
    "InMemoryJobStore",
    "JobManager",
    "job_manager",
]
