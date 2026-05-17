"""
AI Skill Registry

统一注册、查找、调用所有 AI Skill。

用法：
    from backend.app.ai.registry import registry

    # 注册（各 skill 模块 import 时自动完成）
    # registry.register(my_skill)

    # 查找
    skill = registry.get("image_segmentation")

    # 调用
    output = registry.dispatch("image_segmentation", input_data, context)

    # 列出所有已注册能力
    capabilities = registry.list_all()
"""

from typing import Any, Dict, List, Optional

from backend.app.ai.base import CapabilityType, Skill, SkillContext, SkillOutput


class SkillRegistry:
    """
    AI Skill 注册表（单例模式）

    所有 Skill 通过 register() 注册，通过 get() / dispatch() 调用。
    """

    _instance: Optional["SkillRegistry"] = None

    def __new__(cls) -> "SkillRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: Dict[str, Skill] = {}
        return cls._instance

    # ===== 注册 / 注销 =====

    def register(self, skill: Skill) -> None:
        """注册一个 Skill。如果 capability_type 已存在则覆盖。"""
        ct = skill.capability_type
        if ct in self._skills:
            existing = self._skills[ct]
            print(
                f"[SkillRegistry] WARNING: Overwriting '{ct}': "
                f"'{existing.name}' → '{skill.name}'"
            )
        self._skills[ct] = skill
        print(f"[SkillRegistry] Registered '{ct}' → {skill.name} (mode={skill.mode})")

    def unregister(self, capability_type: CapabilityType) -> bool:
        """注销一个 Skill。返回 True 表示成功。"""
        if capability_type in self._skills:
            del self._skills[capability_type]
            return True
        return False

    # ===== 查找 =====

    def get(self, capability_type: str) -> Optional[Skill]:
        """按 capability_type 查找 Skill。未找到返回 None。"""
        return self._skills.get(capability_type)

    def has(self, capability_type: str) -> bool:
        """检查 capability_type 是否已注册。"""
        return capability_type in self._skills

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有已注册 Skill 的元信息"""
        return [skill.describe() for skill in self._skills.values()]

    def count(self) -> int:
        """已注册的 Skill 数量"""
        return len(self._skills)

    # ===== 调用 =====

    def dispatch(
        self,
        capability_type: str,
        input_data: Dict[str, Any],
        context: SkillContext,
    ) -> SkillOutput:
        """
        统一调度入口。

        1. 查找 Skill
        2. 校验输入
        3. 执行 run()
        4. 返回 SkillOutput

        Args:
            capability_type: 能力类型（如 "gwas_analysis"）
            input_data: 能力特定输入参数
            context: 执行上下文

        Returns:
            SkillOutput: 统一输出。如果 Skill 未找到或输入校验失败，
                        返回 status="failed" 的 SkillOutput。
        """
        skill = self.get(capability_type)
        if skill is None:
            return SkillOutput(
                status="failed",
                error_code="ADAPTER_NOT_FOUND",
                error_message=(
                    f"No skill registered for capability '{capability_type}'. "
                    f"Available: {list(self._skills.keys())}"
                ),
            )

        if not skill.validate_input(input_data):
            return SkillOutput(
                status="failed",
                error_code="INVALID_INPUT",
                error_message=(
                    f"Input validation failed for skill '{skill.name}' "
                    f"({skill.capability_type})"
                ),
            )

        try:
            output = skill.run(input_data, context)
            return output
        except Exception as exc:
            return SkillOutput(
                status="failed",
                error_code="SKILL_EXECUTION_ERROR",
                error_message=f"{type(exc).__name__}: {str(exc)}",
            )


# 全局单例
registry = SkillRegistry()
