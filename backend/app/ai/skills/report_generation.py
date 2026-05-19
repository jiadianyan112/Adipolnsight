"""
C7 · 科研报告生成 Skill

职责：报告生成主流程 (Mock / LLM fallback)。
Mock 数据集中在 mock_data.py，模板渲染集中在 report_templates.py。

LLM 扩展点：
- _try_llm() — 已实现 DeepSeek 调用路径
- context_builder — 预制接口 (见 _run_mock)
- renderer — report_templates.build_report() 已实现 markdown 渲染
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.app.ai.base import Skill, SkillContext, SkillMode, SkillOutput
from backend.app.ai.registry import registry
from backend.app.ai.skills.mock_data import (
    SECTION_DEFS,
    SECTION_CONTENT_TEMPLATES,
    SECTION_ONE_LINERS,
    MOCK_FIGURES,
    MOCK_TABLES,
    MOCK_REFERENCES,
    MOCK_AI_INTERPRETATION,
    build_related_figures,
    build_related_tables,
)


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
                "completed_job_results": {"type": "object"},
                "report_type": {"enum": ["summary", "full", "competition"], "default": "full"},
                "language": {"enum": ["zh-CN", "en"], "default": "zh-CN"},
                "include_figures": {"type": "boolean", "default": True},
                "include_tables": {"type": "boolean", "default": True},
                "include_ai_interpretation": {"type": "boolean", "default": True},
            },
        }

    # ===== 主入口 =====

    def run(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """执行报告生成。优先尝试 LLM，失败回退模板。"""
        llm_output = self._try_llm(input_data, context)
        if llm_output is not None:
            return llm_output
        return self._run_template(input_data, context)

    # ===== LLM 路径 =====

    def _try_llm(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput | None:
        """尝试通过 LLM 生成报告。不可用或失败返回 None。"""
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
            from backend.app.ai.llm.prompts.report_generation import SYSTEM_PROMPT, build_user_prompt
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

            response = llm_service.call_llm(request)
            content = response.content or ""
            if not content.strip():
                return None

            llm_data = self._extract_json(content)
            if llm_data is None:
                return None

            ok, data, errors = self._validate_report(llm_data)
            if not ok:
                return None

            return self._build_full_output(data, project_id, project_title, language, list(valid_results.keys()))

        except Exception:
            return None

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """从 LLM 文本响应中提取 JSON。"""
        text = text.strip()
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except (json.JSONDecodeError, ValueError):
                pass
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    @staticmethod
    def _validate_report(data: dict):
        from backend.app.ai.llm.schema_validator import schema_validator
        return schema_validator.validate("report_generation", data)

    def _build_full_output(self, llm_data: dict, project_id: int, project_title: str,
                           language: str, job_ids: list) -> SkillOutput:
        """将 LLM JSON 输出转换为前端兼容格式。"""
        import uuid as _uuid
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        report_id = f"rpt_{_uuid.uuid4().hex[:8]}"

        llm_sections = llm_data.get("sections", [])
        limitations = llm_data.get("limitations", [])
        next_steps = llm_data.get("nextSteps", llm_data.get("next_steps", []))

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

        if next_steps:
            limitations = limitations + [f"建议后续步骤: {', '.join(next_steps[:5])}"]

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

        content_md = self._assemble_markdown(llm_data.get("title", project_title), sections, limitations, language)

        out_dir = context.output_dir
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "final_report.md"), "w", encoding="utf-8") as f:
            f.write(content_md)

        completed_count = len([s for s in sections if s["status"] == "complete"])

        return SkillOutput(
            status="success",
            summary={
                "report_id": report_id, "project_id": project_id,
                "title": llm_data.get("title", project_title), "subtitle": "",
                "report_type": "full", "language": language,
                "sections": sections, "figures": [], "tables": [], "references": [],
                "limitations": limitations, "key_findings": [],
                "export_formats": export_formats, "metadata": metadata,
                "content_markdown": content_md[:8000],
                "completed_sections": completed_count,
                "total_sections": len(sections),
                "ai_interpretation": "[AI-Generated via DeepSeek]",
                "output_files": ["final_report.md"],
            },
            output_files=["final_report.md"],
            metrics={"completed_sections": completed_count},
        )

    @staticmethod
    def _assemble_markdown(title: str, sections: list, limitations: list, language: str) -> str:
        """将章节拼接为完整 markdown。"""
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

    # ===== Template 路径 (Mock fallback) =====

    def _run_template(self, input_data: Dict[str, Any], context: SkillContext) -> SkillOutput:
        """使用模板系统生成报告（基于 selectedJobs 动态生成章节）。

        如果未提供 completed_job_results，则自动从 JobManager + AnalysisTask 收集实际任务数据，
        用于生成报告中的「已完成/未完成」统计，避免硬编码「7 项未完成」。

        未来 LLM 接入路径：
        1. 通过 context_builder 从 project/tasks/results 构建上下文
        2. 调用 LLM 生成结构化 sections
        3. 复用 _build_full_output 输出
        """
        time.sleep(0.3)
        project_id = input_data.get("project_id", 0)
        report_type = input_data.get("report_type", "full_report")
        language = input_data.get("language", "zh-CN")
        project_title = input_data.get("project_title") or "AdipoInsight 科研分析报告"
        selected_jobs = input_data.get("completed_job_results") or input_data.get("selectedJobs") or {}

        if not isinstance(selected_jobs, dict):
            selected_jobs = {}

        # 如果没有提供 completed jobs，尝试从数据库和 JobManager 收集
        if not selected_jobs and project_id:
            selected_jobs = self._collect_project_jobs(project_id)

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

        # 注入项目实际参数到报告
        if project_id:
            self._inject_project_params(report, project_id)

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

    @staticmethod
    def _collect_project_jobs(project_id: int) -> Dict[str, Any]:
        """收集项目下所有已完成的任务作为报告输入。"""
        jobs: Dict[str, Any] = {}

        # From JobManager (new system)
        try:
            from backend.app.ai.job_manager import job_manager as jm
            jm_jobs = jm.list_jobs(project_id=project_id)
            for j in jm_jobs:
                if j.status == "succeeded" and j.result:
                    jobs[j.job_id] = j.result
        except Exception:
            pass

        # From AnalysisTask (old system)
        try:
            from backend.app.database import SessionLocal
            from backend.app.models.analysis_task import AnalysisTask
            db = SessionLocal()
            try:
                tasks = db.query(AnalysisTask).filter(
                    AnalysisTask.project_id == project_id,
                    AnalysisTask.status == "success",
                ).all()
                for t in tasks:
                    result = {}
                    if t.output_json:
                        try:
                            result = json.loads(t.output_json)
                        except (json.JSONDecodeError, TypeError):
                            result = {"summary": t.output_json}
                    jobs[f"task-{t.id}"] = result
            finally:
                db.close()
        except Exception:
            pass

        return jobs

    @staticmethod
    def _inject_project_params(report: Dict[str, Any], project_id: int) -> None:
        """将项目实际参数注入报告，替换模板默认值。"""
        try:
            from backend.app.database import SessionLocal
            from backend.app.models.project import Project
            db = SessionLocal()
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    if project.name and report.get("title") == "AdipoInsight 科研分析报告":
                        report["title"] = f"{project.name} — 科研分析报告"
                    # Update background section with actual project params
                    for sec in report.get("sections", []):
                        if sec.get("title") == "项目背景与研究目标":
                            content = sec.get("content", "")
                            content = content.replace("肝脏脂肪含量（Liver PDFF）", f"本研究关注暴露因素「{project.exposure}」")
                            content = content.replace("肝脏 PDFF 与骨密度/骨质疏松风险的关联强度", f"{project.exposure} 与 {project.outcome} 的关联强度")
                            content = content.replace("肝脏-骨骼轴", f"{project.exposure.replace('_', '-')}-{project.outcome.replace('_', '-')}轴")
                            sec["content"] = content
                            sec["summary"] = f"本项目研究 {project.exposure} → {project.outcome}"
            finally:
                db.close()
        except Exception:
            pass

    # ===== 章节构建 (Legacy mock path — 保留向后兼容) =====

    def _build_sections(self, job_ids: List[str], report_type: str,
                        include_figures: bool, include_tables: bool) -> List[Dict[str, Any]]:
        """构建章节列表。Mock 数据来自 mock_data.py。"""
        sections = []
        section_defs = SECTION_DEFS
        if report_type == "summary":
            section_defs = [s for s in SECTION_DEFS if s["key"] in (
                "background", "segmentation", "gwas", "mr", "discussion")]

        for i, sec_def in enumerate(section_defs):
            key = sec_def["key"]
            evidence_ids = self._assign_evidence(key, job_ids)
            related_figures_list = build_related_figures(key) if include_figures else []
            related_tables_list = build_related_tables(key) if include_tables else []
            content = SECTION_CONTENT_TEMPLATES.get(key, f"## {sec_def['title']}\n\n待分析完成后补充。\n")
            summary_text = SECTION_ONE_LINERS.get(key, "")

            sections.append({
                "number": i + 1,
                "title": sec_def["title"],
                "content": content,
                "status": "complete",
                "summary": summary_text,
                "evidence_job_ids": evidence_ids,
                "related_figures": related_figures_list,
                "related_tables": related_tables_list,
            })
        return sections

    @staticmethod
    def _assign_evidence(section_key: str, job_ids: List[str]) -> List[str]:
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

    # ===== Legacy mock helpers (保留向后兼容) =====

    def _build_related_figures(self, key: str) -> List[Dict[str, str]]:
        return build_related_figures(key)

    def _build_related_tables(self, key: str) -> List[Dict[str, Any]]:
        return build_related_tables(key)

    def _section_one_liner(self, key: str) -> str:
        return SECTION_ONE_LINERS.get(key, "")

    def _build_figures(self) -> List[Dict[str, Any]]:
        return MOCK_FIGURES

    def _build_tables(self) -> List[Dict[str, Any]]:
        return MOCK_TABLES

    def _build_references(self) -> List[Dict[str, Any]]:
        return MOCK_REFERENCES

    def _build_ai_interpretation(self) -> str:
        return MOCK_AI_INTERPRETATION

    def _build_full_markdown(self, title: str, subtitle: str, sections: List[Dict],
                             figures: List[Dict], tables: List[Dict], references: List[Dict],
                             limitations: List[str], findings: List[str], language: str) -> str:
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
        lines.append(MOCK_AI_INTERPRETATION); lines.append("")
        if references:
            lines.append("## 参考文献\n")
            for ref in references: lines.append(f"{ref['number']}. {ref['text']}")
            lines.append("")
        return "\n".join(lines)


# 注册到 SkillRegistry
registry.register(ReportGenerationSkill())
