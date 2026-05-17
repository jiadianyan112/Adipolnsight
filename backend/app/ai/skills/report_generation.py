"""
C7 · 科研报告生成 Skill

Mock 模式：基于已完成 job 结果生成符合学术规范的完整报告。
Real 模式：LLM 驱动（Claude API / GPT-4），预留接口。

每个章节包含：
- title, content, summary
- evidence_job_ids（支撑数据来源）
- related_figures, related_tables（关联图表引用）
"""

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry

# ===== 章节定义 =====

SECTION_DEFS: List[Dict[str, Any]] = [
    {"key": "background", "title": "项目背景与研究目标"},
    {"key": "segmentation", "title": "AI 影像分割结果"},
    {"key": "phenotype", "title": "脂肪表型量化"},
    {"key": "gwas", "title": "GWAS 分析结果"},
    {"key": "mr", "title": "MR 因果推断结果"},
    {"key": "mediation_mr", "title": "中介 MR 蛋白筛选结果"},
    {"key": "risk_modeling", "title": "风险建模结果"},
    {"key": "discussion", "title": "综合讨论与结论"},
    {"key": "limitations", "title": "研究局限性与展望"},
]

SECTION_CONTENT_TEMPLATES: Dict[str, str] = {
    "background": (
        "## 研究背景\n\n"
        "肝脏脂肪含量（Liver PDFF）升高与非酒精性脂肪肝病（NAFLD）密切相关，"
        "近年研究提示 NAFLD 可能通过系统性炎症、胰岛素抵抗及脂肪因子分泌异常等途径影响骨代谢。"
        "然而，肝脏脂肪积累与骨质疏松之间的因果关系及其分子机制尚不完全明确。\n\n"
        "## 研究目标\n\n"
        "1. 量化肝脏 PDFF 与骨密度/骨质疏松风险的关联强度\n"
        "2. 利用孟德尔随机化方法评估因果关系\n"
        "3. 识别介导肝脏-骨骼轴的血浆蛋白中介因子\n"
        "4. 构建基于影像和遗传特征的综合风险预测模型\n\n"
        "## 研究设计\n\n"
        "本研究整合腹部 MRI 影像组学（TSSA-UNet 自动分割）、"
        "UK Biobank 基因组学数据（n≈40,000，EUR）、"
        "deCODE 血浆蛋白 pQTL 数据（4,907 种蛋白）及 OpenGWAS 公开数据库，"
        "采用\"影像 → 遗传 → 因果 → 中介 → 临床\"五步分析策略。"
    ),
    "segmentation": (
        "## 方法\n\n"
        "使用 TSSA-UNet v2.1 深度学习模型对腹部 MRI DIXON 序列进行多器官自动分割。\n\n"
        "## 分割性能\n\n"
        "| 解剖结构 | DICE 系数 | 评价 |\n"
        "|---------|----------|------|\n"
        "| 肝脏 | 0.949 | 优秀 |\n"
        "| 胰腺 | 0.843 | 良好 |\n"
        "| 内脏脂肪 | 0.917 | 优秀 |\n"
        "| 皮下脂肪 | 0.901 | 优秀 |\n"
        "| 骨髓 | 0.871 | 良好 |\n\n"
        "## 质控评估\n\n"
        "- 综合质量评分: 0.896 | SNR: 26.7 dB | 运动伪影: 未检测到 | 覆盖完整度: 98%\n\n"
        "胰腺 DICE 处于临界范围（0.843），可能受胰腺边界模糊和个体差异影响。"
    ),
    "phenotype": (
        "## 定量表型提取\n\n"
        "| 指标 | 数值 | 单位 |\n|------|------|------|\n"
        "| 肝脏 PDFF | 9.8 | % |\n"
        "| 内脏脂肪体积 | 3.49 | L |\n"
        "| 皮下脂肪体积 | 7.62 | L |\n"
        "| 胰腺脂肪分数 | 11.1 | % |\n"
        "| 骨髓脂肪分数 | 64.3 | % |\n"
        "| SAT/VAT 比值 | 2.18 | — |\n"
        "| 全身脂肪百分比 | 30.4 | % |\n"
        "| 骨密度 | 1.28 | g/cm³ |\n\n"
        "肝脏 PDFF 9.8% 提示轻度肝脂肪变性（>5% 为异常阈值）。"
    ),
    "gwas": (
        "## GWAS 设计\n\n"
        "以肝脏 PDFF 为定量表型，纳入年龄、性别、BMI 及前 10 个遗传主成分"
        "作为协变量，使用 REGENIE 方法对 40,484 例 EUR 样本进行分析。\n\n"
        "## 结果摘要\n\n"
        "- 显著基因座: 18 个 (p < 5×10⁻⁸) | 先导 SNP: 12 个 | λ_GC: 1.003\n\n"
        "λ_GC 接近 1.0，表明群体分层和隐性关联控制良好，无系统性偏倚。"
    ),
    "mr": (
        "## 双样本孟德尔随机化\n\n"
        "以 GWAS 显著 SNP 为工具变量，从 OpenGWAS 获取骨质疏松结局汇总统计。\n\n"
        "| 方法 | nSNP | β | OR | 95% CI | P |\n"
        "|------|------|---|---|--------|---|\n"
        "| IVW (Primary) | 12 | 0.383 | 1.47 | [1.21, 1.77] | 1.6×10⁻² |\n"
        "| MR-Egger | 12 | 0.433 | 1.54 | [1.17, 2.03] | 3.8×10⁻² |\n"
        "| Weighted Median | 12 | 0.322 | 1.38 | [1.18, 1.62] | 1.5×10⁻¹ |\n"
        "| Weighted Mode | 12 | 0.316 | 1.37 | [1.13, 1.66] | 6.6×10⁻² |\n\n"
        "**敏感性分析**: Cochran's Q p=0.124（无异质性）；MR-Egger intercept p=0.592（无多效性）。"
    ),
    "mediation_mr": (
        "## 中介筛选\n\n"
        "利用 deCODE 4,907 种血浆蛋白 pQTL 数据，两步 MR + Product Method，FDR 校正。\n\n"
        "| Rank | 蛋白 | 全称 | 间接效应 | 中介比例 | P(FDR) |\n"
        "|------|------|------|---------|---------|--------|\n"
        "| 1 | POR | P450 reductase | +0.0605 | 13.7% | 3.5×10⁻⁴ |\n"
        "| 2 | NAAA | Acid amidase | +0.0359 | 8.2% | 2.0×10⁻⁴ |\n"
        "| 3 | SHBG | Hormone-binding globulin | +0.0230 | 5.2% | 0.088 |\n"
        "| 4 | H6PD | Hexose-6-P dehydrogenase | +0.0157 | 3.6% | 0.221 |\n"
        "| 5 | ACY1 | Aminoacylase-1 | +0.0124 | 2.8% | 0.282 |\n"
        "| 6 | ADH1A | Alcohol dehydrogenase | −0.0013 | 0.3% | 0.917 |\n\n"
        "POR 和 NAAA 达到 FDR<0.05 显著性。"
    ),
    "risk_modeling": (
        "## 风险建模\n\n"
        "多因素模型：OLS + RCS + Multinomial Logistic。\n\n"
        "| 四分位 | PDFF 范围 | Osteoporosis OR |\n"
        "|--------|----------|----------------|\n"
        "| Q1 | < 5.2% | 1.00 (ref) |\n"
        "| Q2 | 5.2–8.1% | 1.26 |\n"
        "| Q3 | 8.1–12.8% | 1.50 |\n"
        "| Q4 | 12.8–35.0% | 1.59 |\n\n"
        "Q4 骨质疏松风险是 Q1 的 1.59 倍（95%CI 1.36–1.89, p_trend<0.001）。"
        "RCS 提示 PDFF>10% 后风险趋于平台，建议以此作为临床筛查阈值。"
    ),
    "discussion": (
        "## 主要发现\n\n"
        "1. 肝脏 PDFF 与骨质疏松风险独立正相关（Q4 vs Q1 OR=1.59）\n"
        "2. MR 支持因果推断（IVW β=0.38, p<0.001）\n"
        "3. POR 和 NAAA 为关键分子中介（分别介导 13.7% 和 8.2%）\n"
        "4. PDFF>10% 后骨质疏松风险趋于平台\n\n"
        "## 临床意义\n\n"
        "- 肝脏 PDFF 可作为骨质疏松风险评估的影像生物标志物\n"
        "- PDFF=10% 建议作为骨密度筛查的触发阈值\n"
        "- POR 和 NAAA 可作为 NAFLD 相关骨病的新型治疗靶点"
    ),
    "limitations": (
        "## 研究局限性\n\n"
        "1. **数据来源**: 使用 Mock 模拟数据，不反映真实生物学发现\n"
        "2. **人群限制**: GWAS 限于 EUR 人群，泛化性待验证\n"
        "3. **中介方法**: cis-pQTL 可能遗漏 trans 效应\n"
        "4. **测量偏差**: PDFF 由自动化分割估计，与 MR 波谱金标准有偏差\n"
        "5. **横断面设计**: 无法确定因果时序\n"
        "6. **未测量混杂**: 药物使用和生活方式未纳入\n"
        "7. **报告生成**: 由 Mock Generator 生成，后续接入 LLM\n\n"
        "## 未来方向\n\n"
        "- 独立队列验证（如 China Kadoorie Biobank）\n"
        "- 细胞/动物实验验证 POR/NAAA 机制\n"
        "- 开发 PDFF+PRS 综合骨折风险预测工具"
    ),
}


class ReportGenerationSkill(Skill):
    """C7 · 科研报告生成"""

    @property
    def name(self) -> str:
        return "Report Generation"

    @property
    def capability_type(self) -> str:
        return "report_generation"

    @property
    def mode(self) -> SkillMode:
        return "mock"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "project_id" in input_data

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["project_id"],
            "properties": {
                "project_id": {"type": "integer"},
                "project_title": {"type": "string"},
                "completed_job_results": {
                    "type": "object",
                    "description": "已完成 job 的结果映射 {job_id: result_summary}",
                },
                "report_type": {"enum": ["summary", "full", "competition"], "default": "full"},
                "language": {"enum": ["zh-CN", "en"], "default": "zh-CN"},
                "include_figures": {"type": "boolean", "default": True},
                "include_tables": {"type": "boolean", "default": True},
                "include_ai_interpretation": {"type": "boolean", "default": True},
            },
        }

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        if self.mode == "mock":
            return self._run_mock(input_data, context)
        else:
            return self._run_real(input_data, context)

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        time.sleep(0.3)
        project_id = input_data["project_id"]
        report_type = input_data.get("report_type", "full")
        language = input_data.get("language", "zh-CN")
        completed_results = input_data.get("completed_job_results") or {}
        include_figures = input_data.get("include_figures", True)
        include_tables = input_data.get("include_tables", True)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        report_id = f"rpt_{uuid.uuid4().hex[:8]}"
        project_title = input_data.get("project_title") or "AdipoInsight 科研分析报告"
        subtitle = "肝脏 PDFF 与骨质疏松因果关系 — 多组学整合分析"

        # 已完成 job IDs
        job_ids = list(completed_results.keys()) if completed_results else [
            "mock_seg", "mock_gwas", "mock_mr", "mock_medmr", "mock_risk",
        ]

        sections = self._build_sections(job_ids, report_type, include_figures, include_tables)
        figures = self._build_figures() if include_figures else []
        tables = self._build_tables() if include_tables else []
        references = self._build_references()

        key_findings = [
            "肝脏 PDFF 与骨质疏松风险呈显著正相关（Q4 vs Q1: OR=1.59）",
            "双样本 MR 支持因果推断（IVW β=0.38, 95%CI 0.22–0.55, p<0.001）",
            "POR 和 NAAA 为显著中介血浆蛋白（FDR<0.05），分别介导 13.7% 和 8.2% 的总效应",
            "RCS 曲线提示 PDFF>10% 后骨质疏松风险趋于平台",
            "MR-Egger intercept p=0.59 排除显著水平多效性",
        ]
        limitations = [
            "本研究使用 Mock 模拟数据，结果不反映真实生物学发现，不可用于临床决策",
            "GWAS 样本限于 EUR 人群，跨人群泛化性待独立队列验证",
            "中介分析仅覆盖 cis-pQTL，可能低估总中介效应",
            "PDFF 由自动化分割估计，与 MR 波谱金标准存在偏差",
            "横断面设计无法确定因果时序",
            "未评估药物使用和生活方式对结局的混杂影响",
        ]
        export_formats = [
            {"format": "markdown", "label": "Markdown", "available": True,
             "url": f"/api/v1/files/reports/{report_id}.md", "file_size": 52000},
            {"format": "pdf", "label": "PDF", "available": False, "url": "", "file_size": 0},
            {"format": "docx", "label": "Word", "available": False, "url": "", "file_size": 0},
            {"format": "html", "label": "HTML", "available": True,
             "url": f"/api/v1/files/reports/{report_id}.html", "file_size": 58000},
            {"format": "latex", "label": "LaTeX", "available": False, "url": "", "file_size": 0},
        ]
        metadata = {
            "version": "1.0.0-mock", "generated_at": now, "generation_time_seconds": 1.2,
            "ai_model": "Mock Report Generator (LLM-ready)",
            "data_sources": ["mock_segmentation", "mock_gwas", "mock_mr", "mock_mediation_mr", "mock_risk_modeling"],
            "analysis_methods": ["TSSA-UNet v2.1", "REGENIE", "TwoSampleMR", "Product Method + Sobel", "OLS + RCS + Logistic"],
            "conflict_of_interest": "本研究由 AdipoInsight AI 系统自动生成，仅供演示。",
            "acknowledgments": "感谢 UK Biobank、deCODE genetics、OpenGWAS 及 IEU MR-Base 数据库。",
        }

        content_md = self._build_full_markdown(
            project_title, subtitle, sections, figures, tables,
            references, limitations, key_findings, language,
        )

        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "final_report.md"), "w", encoding="utf-8") as f:
            f.write(content_md)

        summary = {
            "report_id": report_id, "project_id": project_id,
            "title": project_title, "subtitle": subtitle,
            "report_type": report_type, "language": language,
            "sections": sections, "figures": figures, "tables": tables,
            "references": references, "limitations": limitations,
            "key_findings": key_findings, "export_formats": export_formats,
            "metadata": metadata, "content_markdown": content_md[:8000],
            "completed_sections": len([s for s in sections if s["status"] == "complete"]),
            "total_sections": len(sections),
            "ai_interpretation": self._build_ai_interpretation(),
            "output_files": ["final_report.md"],
        }

        return SkillOutput(
            status="success", summary=summary,
            output_files=["final_report.md"],
            metrics={"completed_sections": summary["completed_sections"]},
        )

    # ==== 章节构建 ====

    def _build_sections(
        self, job_ids: List[str], report_type: str,
        include_figures: bool, include_tables: bool,
    ) -> List[Dict[str, Any]]:
        sections = []
        section_defs = SECTION_DEFS
        if report_type == "summary":
            section_defs = [s for s in SECTION_DEFS if s["key"] in (
                "background", "segmentation", "gwas", "mr", "discussion",
            )]

        for i, sec_def in enumerate(section_defs):
            key = sec_def["key"]
            evidence_ids = self._assign_evidence(key, job_ids)
            related_figures = self._build_related_figures(key) if include_figures else []
            related_tables = self._build_related_tables(key) if include_tables else []
            content = SECTION_CONTENT_TEMPLATES.get(key, f"## {sec_def['title']}\n\n待分析完成后补充。\n")
            summary_text = self._section_one_liner(key)

            sections.append({
                "number": i + 1,
                "title": sec_def["title"],
                "content": content,
                "status": "complete",
                "summary": summary_text,
                "evidence_job_ids": evidence_ids,
                "related_figures": related_figures,
                "related_tables": related_tables,
            })
        return sections

    def _assign_evidence(self, section_key: str, job_ids: List[str]) -> List[str]:
        mapping = {
            "background": [],
            "segmentation": [j for j in job_ids if "seg" in j.lower()] or job_ids[:1],
            "phenotype": [j for j in job_ids if "seg" in j.lower() or "pheno" in j.lower()] or job_ids[:1],
            "gwas": [j for j in job_ids if "gwas" in j.lower()] or job_ids[1:2] or job_ids[:1],
            "mr": [j for j in job_ids if "mr" in j.lower() and "med" not in j.lower()] or job_ids[2:3] or job_ids[:1],
            "mediation_mr": [j for j in job_ids if "med" in j.lower()] or job_ids[3:4] or job_ids[:1],
            "risk_modeling": [j for j in job_ids if "risk" in j.lower()] or job_ids[4:5] or job_ids[:1],
            "discussion": job_ids[:5] if len(job_ids) >= 5 else job_ids,
            "limitations": [],
        }
        return mapping.get(section_key, [])

    def _build_related_figures(self, key: str) -> List[Dict[str, str]]:
        fig_map = {
            "segmentation": [{"figure_id": "fig_seg_1", "caption": "Figure 1: 腹部 MRI 多器官分割叠加图", "type": "segmentation_overlay"}],
            "gwas": [
                {"figure_id": "fig_gwas_1", "caption": "Figure 2: Liver PDFF GWAS Manhattan 图", "type": "manhattan"},
                {"figure_id": "fig_gwas_2", "caption": "Figure 3: GWAS Q-Q 图", "type": "qq_plot"},
            ],
            "mr": [{"figure_id": "fig_mr_1", "caption": "Figure 4: MR SNP效应散点图", "type": "scatter"}],
            "mediation_mr": [
                {"figure_id": "fig_medmr_1", "caption": "Figure 5: 中介 MR 森林图", "type": "forest"},
                {"figure_id": "fig_medmr_2", "caption": "Figure 6: 肝脏-蛋白-骨骼机制流程图", "type": "mechanism_diagram"},
            ],
            "risk_modeling": [{"figure_id": "fig_risk_1", "caption": "Figure 7: PDFF-骨质疏松 RCS 曲线", "type": "rcs_curve"}],
        }
        return fig_map.get(key, [])

    def _build_related_tables(self, key: str) -> List[Dict[str, Any]]:
        tbl_map = {
            "segmentation": [{"table_id": "tbl_seg_1", "caption": "Table 1: 多器官分割 DICE 评分", "columns": ["解剖结构", "DICE", "评价"]}],
            "phenotype": [{"table_id": "tbl_pheno_1", "caption": "Table 2: 定量脂肪表型指标", "columns": ["指标", "数值", "单位"]}],
            "gwas": [{"table_id": "tbl_gwas_1", "caption": "Table 3: 先导 SNP 汇总", "columns": ["SNP", "Chr", "BP", "Beta", "P"]}],
            "mr": [
                {"table_id": "tbl_mr_1", "caption": "Table 4: MR 估计值汇总", "columns": ["方法", "nSNP", "β", "OR", "95%CI", "P"]},
                {"table_id": "tbl_mr_2", "caption": "Table 5: 敏感性分析", "columns": ["检验", "统计量", "P"]},
            ],
            "mediation_mr": [{"table_id": "tbl_medmr_1", "caption": "Table 6: 显著中介蛋白排序", "columns": ["Rank", "蛋白", "间接效应", "中介比例", "P(FDR)"]}],
            "risk_modeling": [
                {"table_id": "tbl_risk_1", "caption": "Table 7: 四分位风险分层 OR", "columns": ["四分位", "PDFF范围", "Osteoporosis OR"]},
                {"table_id": "tbl_risk_2", "caption": "Table 8: 模型性能", "columns": ["模型", "AUC", "R²"]},
            ],
            "discussion": [{"table_id": "tbl_disc_1", "caption": "Table 9: 关键发现汇总", "columns": ["发现", "效应量", "证据等级"]}],
        }
        return tbl_map.get(key, [])

    def _section_one_liner(self, key: str) -> str:
        return {
            "background": "阐述肝脏-骨骼轴研究背景及多组学整合研究设计",
            "segmentation": "TSSA-UNet v2.1 成功分割 5 个解剖区域，DICE 0.84–0.95",
            "phenotype": "提取 9 项脂肪表型指标，肝脏 PDFF 9.8%",
            "gwas": "REGENIE 识别 18 个显著基因座，λ_GC=1.003",
            "mr": "IVW 支持因果效应 (OR=1.47, p<0.001)",
            "mediation_mr": "POR 和 NAAA 为显著中介蛋白 (FDR<0.05)",
            "risk_modeling": "Q4 PDFF 骨质疏松风险增加 59%，建议 PDFF=10% 为阈值",
            "discussion": "综合多组学证据支持肝脏-骨骼轴假说",
            "limitations": "Mock 数据、单一人群、横断面设计为主要限制",
        }.get(key, "")

    # ==== 图表清单 ====

    def _build_figures(self) -> List[Dict[str, Any]]:
        return [
            {"figure_id": "fig_seg_1", "number": 1, "caption": "Figure 1: 腹部 MRI 多器官分割叠加图",
             "url": "/api/v1/files/report/fig_seg_overlay.png", "type": "segmentation_overlay",
             "section_number": 2, "alt_text": "TSSA-UNet overlay", "source_job_id": "mock_seg"},
            {"figure_id": "fig_gwas_1", "number": 2, "caption": "Figure 2: GWAS Manhattan 图",
             "url": "/api/v1/files/report/fig_manhattan.png", "type": "manhattan",
             "section_number": 4, "alt_text": "Manhattan plot", "source_job_id": "mock_gwas"},
            {"figure_id": "fig_gwas_2", "number": 3, "caption": "Figure 3: GWAS Q-Q 图",
             "url": "/api/v1/files/report/fig_qq.png", "type": "qq_plot",
             "section_number": 4, "alt_text": "QQ plot", "source_job_id": "mock_gwas"},
            {"figure_id": "fig_mr_1", "number": 4, "caption": "Figure 4: MR 散点图",
             "url": "/api/v1/files/report/fig_mr_scatter.png", "type": "scatter",
             "section_number": 5, "alt_text": "MR scatter", "source_job_id": "mock_mr"},
            {"figure_id": "fig_medmr_1", "number": 5, "caption": "Figure 5: 中介 MR 森林图",
             "url": "/api/v1/files/report/fig_medmr_forest.png", "type": "forest",
             "section_number": 6, "alt_text": "Forest plot", "source_job_id": "mock_medmr"},
            {"figure_id": "fig_medmr_2", "number": 6, "caption": "Figure 6: 机制流程图",
             "url": "/api/v1/files/report/fig_mechanism.png", "type": "mechanism_diagram",
             "section_number": 6, "alt_text": "Mechanism diagram", "source_job_id": "mock_medmr"},
            {"figure_id": "fig_risk_1", "number": 7, "caption": "Figure 7: RCS 剂量反应曲线",
             "url": "/api/v1/files/report/fig_rcs.png", "type": "rcs_curve",
             "section_number": 7, "alt_text": "RCS curve", "source_job_id": "mock_risk"},
        ]

    def _build_tables(self) -> List[Dict[str, Any]]:
        return [
            {"table_id": "tbl_seg_1", "number": 1, "caption": "Table 1: DICE 评分",
             "columns": [{"key":"organ","label":"结构"},{"key":"dice","label":"DICE","format":"number","precision":3}],
             "rows": [], "section_number": 2, "source_job_id": "mock_seg", "footnotes": []},
            {"table_id": "tbl_mr_1", "number": 2, "caption": "Table 2: MR 估计值",
             "columns": [{"key":"method","label":"方法"},{"key":"beta","label":"β","format":"number","precision":3}],
             "rows": [], "section_number": 5, "source_job_id": "mock_mr", "footnotes": ["Primary: IVW"]},
            {"table_id": "tbl_medmr_1", "number": 3, "caption": "Table 3: 中介蛋白排序",
             "columns": [{"key":"protein","label":"蛋白"},{"key":"indirect","label":"间接效应","format":"number","precision":4}],
             "rows": [], "section_number": 6, "source_job_id": "mock_medmr", "footnotes": ["FDR corrected"]},
            {"table_id": "tbl_risk_1", "number": 4, "caption": "Table 4: 风险分层 OR",
             "columns": [{"key":"quartile","label":"四分位"},{"key":"or","label":"OR","format":"number","precision":2}],
             "rows": [], "section_number": 7, "source_job_id": "mock_risk", "footnotes": ["Adjusted for age, sex, BMI"]},
        ]

    def _build_references(self) -> List[Dict[str, Any]]:
        return [
            {"ref_id": "ref_1", "number": 1, "doi": "10.1038/s41586-018-0579-z",
             "text": "Bycroft C, et al. UK Biobank. Nature 2018;562:203–9.", "type": "database", "cited_in_sections": [1,3,4]},
            {"ref_id": "ref_2", "number": 2, "doi": "10.1038/s41588-021-00978-w",
             "text": "Ferkingstad E, et al. Plasma proteome genetics. Nat Genet 2021;53:1712–21.", "type": "database", "cited_in_sections": [6]},
            {"ref_id": "ref_3", "number": 3, "doi": "10.7554/eLife.34408",
             "text": "Hemani G, et al. MR-Base. eLife 2018;7:e34408.", "type": "method", "cited_in_sections": [5]},
            {"ref_id": "ref_4", "number": 4, "doi": "10.12688/wellcomeopenres.15555.2",
             "text": "Burgess S, et al. MR guidelines. Wellcome Open Res 2019;4:186.", "type": "method", "cited_in_sections": [5,6]},
            {"ref_id": "ref_5", "number": 5, "doi": "10.1101/2020.08.10.244293",
             "text": "Elsworth B, et al. OpenGWAS. bioRxiv 2020.", "type": "database", "cited_in_sections": [4,5]},
            {"ref_id": "ref_6", "number": 6, "doi": "10.1038/s41592-020-01008-z",
             "text": "Isensee F, et al. nnU-Net. Nat Methods 2021;18:203–11.", "type": "method", "cited_in_sections": [2]},
        ]

    def _build_ai_interpretation(self) -> str:
        return (
            "## AI 综合分析\n\n"
            "本研究整合影像组学、基因组学和蛋白质组学多维度数据，"
            "系统评估了肝脏 PDFF 与骨质疏松风险的关联。主要结论：\n\n"
            "1. **因果证据链完整**: GWAS → MR → Mediation → Risk Modeling 四级证据一致\n"
            "2. **临床转化潜力**: PDFF=10% 阈值 + Q4 1.59x OR 提供可操作的筛查标准\n"
            "3. **机制可验证性**: POR 和 NAAA 可作为下游实验验证的靶点\n\n"
            "> 本解读由 Mock AI 生成。接入 LLM 后将提供基于实际数据的深度讨论。\n"
            "\n### LLM 接入接口（预留）\n\n"
            "```python\ndef _run_real(self, input_data, context):\n"
            "    import anthropic\n"
            "    client = anthropic.Anthropic()\n"
            "    response = client.messages.create(\n"
            "        model=\"claude-sonnet-4-6\",\n"
            "        system=\"你是医学科研报告撰写专家...\",\n"
            "        messages=[{\"role\":\"user\", \"content\": json.dumps(sections_data)}],\n"
            "    )\n"
            "    return self._parse_llm_response(response)\n"
            "```"
        )

    def _build_full_markdown(
        self, title: str, subtitle: str,
        sections: List[Dict], figures: List[Dict], tables: List[Dict],
        references: List[Dict], limitations: List[str],
        findings: List[str], language: str,
    ) -> str:
        lines = [
            f"# {title}", f"## {subtitle}", "",
            f"**报告类型**: 完整报告 (Mock) | **语言**: {language} | "
            f"**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "", "---", "",
        ]
        for sec in sections:
            lines.append(sec["content"]); lines.append("")
        if findings:
            lines.append("## 关键发现\n")
            for f in findings: lines.append(f"- {f}")
            lines.append("")
        if limitations:
            lines.append("## 研究局限性\n")
            for lim in limitations: lines.append(f"- {lim}")
            lines.append("")
        lines.append(self._build_ai_interpretation()); lines.append("")
        if references:
            lines.append("## 参考文献\n")
            for ref in references: lines.append(f"{ref['number']}. {ref['text']}")
            lines.append("")
        return "\n".join(lines)

    def _run_real(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        return SkillOutput(
            status="failed",
            error_code="NOT_IMPLEMENTED",
            error_message="LLM-based report generation not yet integrated. Switch mode to 'mock'.",
        )


registry.register(ReportGenerationSkill())
