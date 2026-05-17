"""
AI Skill 基类定义

所有 AI 能力（Mock / Script / API / Model）必须实现 Skill 接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


# ===== 运行模式 =====

SkillMode = Literal["mock", "script", "api", "model"]


class SkillModeMeta:
    """各模式的语义说明"""
    mock = "本地 mock 数据，不依赖外部资源"
    script = "调用本地 Python/Shell 分析脚本（subprocess）"
    api = "调用外部 HTTP API（如 OpenGWAS、LLM API）"
    model = "调用本地 AI 模型推理（如 TSSA-UNet）"


# ===== 能力类型 =====

CapabilityType = Literal[
    "image_segmentation",
    "phenotype_quantification",
    "gwas_analysis",
    "opengwas_fetch",
    "mendelian_randomization",
    "mediation_mr",
    "risk_modeling",
    "report_generation",
]


# ===== Skill 输出 =====

@dataclass
class SkillOutput:
    """统一的 Skill 执行结果"""
    status: Literal["success", "failed", "partial"]
    summary: Dict[str, Any] = field(default_factory=dict)
    output_files: List[str] = field(default_factory=list)
    error_code: str = ""
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "output_files": self.output_files,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


# ===== 执行上下文 =====

@dataclass
class SkillContext:
    """Skill 执行上下文，由 Orchestrator 注入"""
    project_id: int
    task_id: int
    output_dir: str = ""
    db_session: Any = None
    extra: Dict[str, Any] = field(default_factory=dict)


# ===== Skill 接口 =====

class Skill(ABC):
    """
    AI Skill 抽象基类

    每个 AI 能力实现为一个 Skill 子类，通过 SkillRegistry 注册。
    子类只需关心输入校验和业务逻辑，执行环境和持久化由 Orchestrator 负责。
    """

    # --- 子类必须覆盖的属性 ---

    @property
    @abstractmethod
    def name(self) -> str:
        """Skill 人类可读名称，如 "AI Image Segmentation" """
        ...

    @property
    @abstractmethod
    def capability_type(self) -> CapabilityType:
        """能力类型枚举值，如 "image_segmentation" """
        ...

    @property
    @abstractmethod
    def mode(self) -> SkillMode:
        """当前运行模式：mock | script | api | model"""
        ...

    # --- 子类必须实现的方法 ---

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        校验输入参数是否满足此 Skill 的最低要求。
        返回 True 表示校验通过，False 表示不通过。

        实现时应检查必填字段、类型、取值范围。
        """
        ...

    @abstractmethod
    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """
        执行 AI 能力。

        Args:
            input_data: 能力特定输入参数（由 API request body 传入）
            context: 执行上下文（project_id, task_id, output_dir 等）

        Returns:
            SkillOutput: 统一输出结构
        """
        ...

    # --- 可选覆盖的方法 ---

    def get_input_schema(self) -> Optional[Dict[str, Any]]:
        """返回 JSON Schema 描述，供前端动态表单使用。默认无。"""
        return None

    def get_output_schema(self) -> Optional[Dict[str, Any]]:
        """返回输出 JSON Schema 描述。默认无。"""
        return None

    def cleanup(self, context: SkillContext) -> None:
        """执行后的清理工作。默认不执行任何操作。"""
        pass

    # --- 序列化 ---

    def describe(self) -> Dict[str, Any]:
        """返回 Skill 元信息（供前端能力发现）"""
        return {
            "name": self.name,
            "capability_type": self.capability_type,
            "mode": self.mode,
            "input_schema": self.get_input_schema(),
            "output_schema": self.get_output_schema(),
        }
