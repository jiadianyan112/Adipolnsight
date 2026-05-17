"""
C1 · MRI 影像上传与 AI 分割 Skill

Mock 模式：生成贴合临床 MRI 身体成分分析场景的结构化分割结果。
Real 模式：调用 TSSA-UNet / nnUNet 推理脚本。

输出结构对齐：
- schemas/ai.py: SegmentationResult, DiceScores, VolumeMetrics, QualityControl
- 前端 types/segmentation.ts: 同名 TypeScript 接口
"""

import json
import os
import random
import time
import uuid
from typing import Any, Dict, List

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry
from backend.app.config import STORAGE_DIR


class ImageSegmentationSkill(Skill):
    """C1 · AI 影像分割"""

    @property
    def name(self) -> str:
        return "AI Image Segmentation"

    @property
    def capability_type(self) -> str:
        return "image_segmentation"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    # ===== 输入校验 =====

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        if "project_id" not in input_data:
            return False
        if "file_id" not in input_data:
            return False
        target_structures = input_data.get("target_structures", [])
        valid = {"liver", "pancreas", "visceral_fat", "subcutaneous_fat", "bone_marrow", "kidney", "muscle"}
        if target_structures and not set(target_structures).issubset(valid):
            return False
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["project_id", "file_id"],
            "properties": {
                "project_id": {"type": "integer", "description": "项目 ID"},
                "file_id": {"type": "integer", "description": "已上传 MRI 文件 ID"},
                "target_structures": {
                    "type": "array",
                    "items": {
                        "enum": ["liver", "pancreas", "visceral_fat", "subcutaneous_fat", "bone_marrow", "kidney", "muscle"],
                    },
                    "default": ["liver", "pancreas", "visceral_fat", "subcutaneous_fat", "bone_marrow"],
                    "description": "需要分割的解剖结构列表",
                },
                "modality": {"type": "string", "default": "MRI", "enum": ["MRI", "CT"]},
                "model_name": {"type": "string", "default": "TSSA-UNet"},
                "mode": {"type": "string", "default": "mock", "enum": ["mock", "real"]},
            },
        }

    # ===== 执行入口 =====

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        if self.mode == "mock":
            return self._run_mock(input_data, context)
        else:
            return self._run_real(input_data, context)

    # ---- Mock 实现 ----

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        time.sleep(0.3)
        target = input_data.get("target_regions") or input_data.get("target_structures") or [
            "liver", "pancreas", "visceral_fat", "subcutaneous_fat", "bone_marrow",
        ]
        model_name = input_data.get("model_name", "TSSA-UNet")
        seg_id = f"seg_{uuid.uuid4().hex[:8]}"

        # ---- DICE 评分（贴近 TSSA-UNet 论文报告区间） ----
        dice_scores = self._generate_dice(target)

        # ---- 体积指标（贴合 UK Biobank 腹部 MRI 人群分布） ----
        volume_metrics = self._generate_volumes(target, dice_scores)

        # ---- 质量控制 ----
        quality_control = self._generate_qc(dice_scores)

        # ---- 警告 ----
        warnings = self._generate_warnings(
            dice_scores, quality_control, target, input_data
        )

        # ---- 文件路径 ----
        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)

        mask_url = f"/api/v1/files/projects/{context.project_id}/outputs/segmentation/mask_preview.png"
        overlay_url = f"/api/v1/files/projects/{context.project_id}/outputs/segmentation/overlay_preview.png"

        # ---- 组装输出 ----
        result = {
            "segmentation_id": seg_id,
            "model_name": model_name,
            "model_version": "v2.1",
            "target_regions": target,
            "dice_scores": dice_scores,
            "volume_metrics": volume_metrics,
            "quality_control": quality_control,
            "mask_preview_url": mask_url,
            "overlay_preview_url": overlay_url,
            "warnings": warnings,
        }

        # 写出文件
        metrics_path = os.path.join(out_dir, "segmentation_metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(result, f, indent=2)

        csv_path = os.path.join(out_dir, "fat_quantification.csv")
        with open(csv_path, "w") as f:
            headers = ["subject_id"] + list(volume_metrics.keys())
            f.write(",".join(headers) + "\n")
            f.write(f"DEMO_001," + ",".join(str(v) for v in volume_metrics.values()) + "\n")

        return SkillOutput(
            status="success",
            summary=result,
            output_files=[
                "segmentation_metrics.json",
                "fat_quantification.csv",
                "overlay_preview.png",
            ],
            warnings=warnings,
            metrics={
                "dice_liver": dice_scores["liver"],
                "dice_pancreas": dice_scores["pancreas"],
                "dice_visceral_fat": dice_scores["visceral_fat"],
                "dice_subcutaneous_fat": dice_scores["subcutaneous_fat"],
                "dice_bone_marrow": dice_scores["bone_marrow"],
                "overall_quality": quality_control["overall_quality_score"],
            },
        )

    # ==== Mock 数据生成器 ====

    def _generate_dice(self, target: List[str]) -> Dict[str, float]:
        """生成贴合各解剖结构分割难度的 DICE 评分。

        文献参考区间（TSSA-UNet / nnUNet 腹部 MRI）：
        - 肝脏: 0.92–0.96  （边界清晰，HBP 对比度高）
        - 胰腺: 0.82–0.89  （边界模糊，个体差异大）
        - 内脏脂肪: 0.88–0.94
        - 皮下脂肪: 0.90–0.95  （最易分割）
        - 骨髓: 0.85–0.92  （信号不均匀）
        """
        ranges = {
            "liver": (0.92, 0.96),
            "pancreas": (0.82, 0.89),
            "visceral_fat": (0.88, 0.94),
            "subcutaneous_fat": (0.90, 0.95),
            "bone_marrow": (0.85, 0.92),
            "kidney": (0.90, 0.95),
            "muscle": (0.91, 0.95),
        }
        return {
            region: round(random.uniform(*ranges.get(region, (0.85, 0.92))), 3)
            for region in target
            if region in ranges
        }

    def _generate_volumes(
        self, target: List[str], dice: Dict[str, float]
    ) -> Dict[str, float]:
        """生成贴合 UK Biobank 腹部 MRI 人群分布的体积指标。

        参考值（40,000+ 样本均值 ± SD）：
        - 肝脏体积: 1450 ± 300 cm³
        - 内脏脂肪: 3500 ± 1800 cm³
        - 皮下脂肪: 6800 ± 3200 cm³
        - 肝脏 PDFF: 3–18%（中位~6%）
        - 骨髓脂肪: 55–75%（年龄依赖）
        - 肌肉体积: 22–30 L
        - SAT/VAT: 1.5–3.5
        - 骨密度: 1.1–1.4 g/cm³
        """
        liver_vol = round(random.gauss(1470, 280), 1)
        vat_vol = round(random.gauss(3480, 1600), 1)
        sat_vol = round(random.gauss(6750, 3000), 1)

        return {
            "liver_volume_cm3": max(800, liver_vol),
            "visceral_fat_volume_cm3": max(500, vat_vol),
            "subcutaneous_fat_volume_cm3": max(1000, sat_vol),
            "pancreatic_fat_fraction_pct": round(random.gauss(8.5, 2.5), 1),
            "liver_pdff_pct": max(1.0, round(random.gauss(6.5, 3.5), 1)),
            "bone_marrow_fat_fraction_pct": round(random.gauss(62.0, 8.0), 1),
            "muscle_volume_L": round(random.gauss(26.0, 3.5), 1),
            "sat_vat_ratio": round(sat_vol / max(vat_vol, 1), 2),
            "total_body_fat_pct": round(random.gauss(31.0, 5.0), 1),
            "bone_density_g_cm3": round(random.gauss(1.24, 0.08), 2),
        }

    def _generate_qc(self, dice: Dict[str, float]) -> Dict[str, Any]:
        """生成质量控制指标。

        - overall_quality_score: 各区域 DICE 均值
        - motion_artifact: 10% 概率检测到运动伪影
        - field_inhomogeneity: 0–0.5（越低越好）
        - SNR: 腹部 MRI 典型 20–35 dB
        - coverage_completeness: 0.95–1.0
        """
        avg_dice = sum(dice.values()) / len(dice) if dice else 0.90
        motion = random.random() < 0.10
        if motion:
            # 运动伪影会降低整体质量
            avg_dice = max(0.75, avg_dice - random.uniform(0.03, 0.08))

        qc_status: str = "passed"
        if avg_dice < 0.82:
            qc_status = "failed"
        elif avg_dice < 0.88 or motion:
            qc_status = "warning"

        return {
            "status": qc_status,
            "overall_quality_score": round(avg_dice, 3),
            "motion_artifact_detected": motion,
            "field_inhomogeneity_score": round(random.uniform(0.05, 0.25), 2),
            "snr_estimate_db": round(
                random.gauss(28.0, 3.0) - (5 if motion else 0), 1
            ),
            "coverage_completeness": round(random.uniform(0.95, 1.0), 2),
        }

    def _generate_warnings(
        self,
        dice: Dict[str, float],
        qc: Dict[str, Any],
        target: List[str],
        input_data: Dict[str, Any],
    ) -> List[str]:
        """生成临床可操作的警告信息"""
        warnings: List[str] = []

        for region, score in dice.items():
            if score < 0.83:
                warnings.append(
                    f"{region} 分割 DICE 偏低 ({score:.2f})，"
                    f"建议检查影像质量或手动校正分割边界"
                )
            elif score < 0.88:
                warnings.append(
                    f"{region} 分割 DICE 处于临界值 ({score:.2f})，"
                    f"定量分析结果需谨慎解读"
                )

        if qc["motion_artifact_detected"]:
            warnings.append(
                "检测到运动伪影，可能影响分割精度。"
                "建议在报告中注明此限制"
            )

        if qc["field_inhomogeneity_score"] > 0.20:
            warnings.append(
                f"磁场不均匀性偏高 ({qc['field_inhomogeneity_score']:.2f})，"
                f"可能由患者体位或线圈摆放引起"
            )

        if qc["snr_estimate_db"] < 20:
            warnings.append(
                f"SNR 偏低 ({qc['snr_estimate_db']:.1f} dB)，"
                f"建议检查扫描参数或使用降噪后处理"
            )

        # 检查目标区域是否缺失
        expected = {"liver", "pancreas", "visceral_fat", "subcutaneous_fat", "bone_marrow"}
        requested = set(target)
        missing = expected - requested
        if missing:
            names = {"liver": "肝脏", "pancreas": "胰腺", "visceral_fat": "内脏脂肪",
                     "subcutaneous_fat": "皮下脂肪", "bone_marrow": "骨髓"}
            missing_cn = [names.get(m, m) for m in missing]
            warnings.append(
                f"以下区域未包含在分割目标中：{', '.join(missing_cn)}。"
                f"下游分析（GWAS/MR）的暴露变量选择将受限"
            )

        return warnings

    # ---- Real 实现（预留） ----

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        return SkillOutput(
            status="failed",
            error_code="NOT_IMPLEMENTED",
            error_message="Real segmentation model not yet integrated. Switch mode to 'mock' or deploy TSSA-UNet.",
        )


# 自动注册
registry.register(ImageSegmentationSkill())
