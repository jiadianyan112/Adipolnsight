"""
C7 · 科研报告生成 Skill

Mock 模式：基于已完成 job 结果生成符合学术规范的完整报告。
Real 模式：LLM 驱动（Claude API / GPT-4），预留接口。

每个章节包含：
- title, content, summary
- evidence_job_ids（支撑数据来源）
- related_figures, related_tables（关联图表引用）
"""

import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry

# ===== 章节定义（旧版，保留向后兼容；新版模板在 report_templates.py） =====

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
        """执行报告生成。优先尝试 LLM，失败回退模板。"""
        # 先尝试 LLM 路径
        llm_output = self._try_llm(input_data, context)
        if llm_output is not None:
            return llm_output

        # Fallback 到模板
        return self._run_mock(input_data, context)

    # ===== LLM 路径 =====

    def _try_llm(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput | None:
        """尝试通过 LLM 生成报告。不可用或失败返回 None。

        使用 text 模式调用（非 JSON mode），自行解析 JSON，
        以避免 DeepSeek 返回 markdown-wrapped JSON 时解析失败。
        """
        try:
            from backend.app.config import LLM_PROVIDER
            from backend.app.ai.llm import provider_registry

            if LLM_PROVIDER != "deepseek":
                return None
            if not provider_registry.has("deepseek"):
                return None

            completed_results = input_data.get("completed_job_results") or {}
            if not isinstance(completed_results, dict):
                completed_results = {}

            project_id = input_data.get("project_id", 0)
            project_title = input_data.get("project_title") or "AdipoInsight 科研分析报告"
            language = input_data.get("language", "zh-CN")

            valid_results = {
                jid: res for jid, res in completed_results.items()
                if isinstance(res, dict) and res
            }

            from backend.app.ai.llm.service import llm_service
            from backend.app.ai.llm.prompts.report_generation import (
                SYSTEM_PROMPT,
                build_user_prompt,
            )
            from backend.app.schemas.llm import LLMRequest, LLMMessage

            user_msg = build_user_prompt(project_title, valid_results, language)

            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=SYSTEM_PROMPT),
                    LLMMessage(role="user", content=user_msg),
                ],
                taskType="report_generation",
                temperature=0.3,
                maxTokens=8192,
            )

            # 使用 text 模式调用，避免 JSON mode 的 markdown fence 问题
            response = llm_service.call_llm(request)

            content = response.content or ""
            if not content.strip():
                return None

            # 手动提取 JSON（健壮的 markdown fence 剥离）
            llm_data = self._extract_json(content)
            if llm_data is None:
                return None

            # Schema 校验
            ok, data, errors = self._validate_report(llm_data)
            if not ok:
                return None

            return self._build_full_output(
                data, project_id, project_title, language, list(valid_results.keys()),
            )

        except Exception:
            return None

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """从 LLM 文本响应中提取 JSON，处理各种 markdown fence 格式。"""
        text = text.strip()

        # 尝试 1：匹配 ```json ... ``` 或 ``` ... ``` 代码块
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass

        # 尝试 2：查找第一个 { 和最后一个 } 之间的内容
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except (json.JSONDecodeError, ValueError):
                pass

        # 尝试 3：直接解析
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    @staticmethod
    def _validate_report(data: dict):
        """校验报告 JSON 结构。返回 (ok, validated_data, errors)。"""
        from backend.app.ai.llm.schema_validator import schema_validator
        return schema_validator.validate("report_generation", data)

    def _build_full_output(
        self,
        llm_data: dict,
        project_id: int,
        project_title: str,
        language: str,
        job_ids: list,
    ) -> SkillOutput:
        """将 LLM JSON 输出转换为前端兼容的完整报告格式。"""
        import uuid as _uuid

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        report_id = f"rpt_{_uuid.uuid4().hex[:8]}"

        llm_sections = llm_data.get("sections", [])
        limitations = llm_data.get("limitations", [])
        next_steps = llm_data.get("nextSteps", llm_data.get("next_steps", []))

        # 转换为前端 ReportSection 格式
        sections = []
        for i, sec in enumerate(llm_sections):
            sections.append({
                "number": i + 1,
                "title": sec.get("title", f"章节 {i+1}"),
                "content": sec.get("content", ""),
                "status": "complete",
                "summary": "",
                "evidence_job_ids": sec.get("evidenceJobIds", sec.get("evidence_job_ids", [])),
                "related_figures": sec.get("relatedFigures", sec.get("related_figures", [])),
                "related_tables": sec.get("relatedTables", sec.get("related_tables", [])),
            })

        # 如果 LLM 返回了 nextSteps，追加到 limitations
        if next_steps:
            limitations = limitations + [f"建议后续步骤: {', '.join(next_steps[:5])}"]

        # 添加 AI 生成声明
        limitations = limitations + [
            "[AI-Generated] 本报告由 DeepSeek LLM 自动生成，数据来源为已完成的分析结果。仅供科研参考，不构成临床决策依据。",
        ]

        export_formats = [
            {"format": "markdown", "label": "Markdown", "available": True,
             "url": f"/api/v1/files/reports/{report_id}.md", "file_size": 52000},
        ]

        metadata = {
            "version": "2.0.0-llm",
            "generated_at": now,
            "generation_time_seconds": 0,
            "ai_model": "DeepSeek (via AdipoInsight LLM Service)",
            "data_sources": job_ids,
            "analysis_methods": [],
            "conflict_of_interest": "本研究由 AdipoInsight AI 系统自动生成。",
            "acknowledgments": "",
        }

        # 构建 markdown
        content_md = self._build_markdown_from_sections(
            llm_data.get("title", project_title), sections, limitations, language,
        )

        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "final_report.md"), "w", encoding="utf-8") as f:
            f.write(content_md)

        completed_count = len([s for s in sections if s["status"] == "complete"])

        return SkillOutput(
            status="success",
            summary={
                "report_id": report_id,
                "project_id": project_id,
                "title": llm_data.get("title", project_title),
                "subtitle": "",
                "report_type": "full",
                "language": language,
                "sections": sections,
                "figures": [],
                "tables": [],
                "references": [],
                "limitations": limitations,
                "key_findings": [],
                "export_formats": export_formats,
                "metadata": metadata,
                "content_markdown": content_md[:8000],
                "completed_sections": completed_count,
                "total_sections": len(sections),
                "ai_interpretation": "[AI-Generated via DeepSeek]",
                "output_files": ["final_report.md"],
            },
            output_files=["final_report.md"],
            metrics={"completed_sections": completed_count},
        )

    def _build_markdown_from_sections(
        self, title: str, sections: list, limitations: list, language: str,
    ) -> str:
        """将 LLM 生成的 sections 拼接为完整 markdown。"""
        lines = [f"# {title}", "", f"**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", "", "---", ""]
        for sec in sections:
            lines.append(f"## {sec['title']}")
            lines.append(sec.get("content", ""))
            lines.append("")
        if limitations:
            lines.append("## 研究局限性")
            for lim in limitations:
                lines.append(f"- {lim}")
            lines.append("")
        return "\n".join(lines)

    # ===== Mock 路径（模板 fallback） =====

    def _run_mock(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """使用新模板系统生成报告（基于 selectedJobs 动态生成章节）。"""
        time.sleep(0.3)
        project_id = input_data.get("project_id", 0)
        report_type = input_data.get("report_type", "full_report")
        language = input_data.get("language", "zh-CN")
        project_title = input_data.get("project_title") or "AdipoInsight 科研分析报告"
        selected_jobs = input_data.get("completed_job_results") or input_data.get("selectedJobs") or {}

        if not isinstance(selected_jobs, dict):
            selected_jobs = {}

        # 调用新模板引擎
        from backend.app.ai.skills.report_templates import build_report

        report = build_report(
            selected_jobs=selected_jobs,
            report_type=report_type,
            project_title=project_title,
            language=language,
            include_figures=input_data.get("include_figures", True),
            include_tables=input_data.get("include_tables", True),
        )
        report["project_id"] = project_id

        # 写出 markdown
        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "final_report.md"), "w", encoding="utf-8") as f:
            f.write(report.get("content_markdown", ""))

        return SkillOutput(
            status="success",
            summary=report,
            output_files=["final_report.md"],
            metrics={"completed_sections": report["completed_sections"]},
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

registry.register(ReportGenerationSkill())
