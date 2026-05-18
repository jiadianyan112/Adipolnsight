"""
Project summary prompt for AdipoInsight.

Produces a high-level summary of a project's analysis status,
completed tasks, and recommended next steps.

Used by: AgentOrchestrator (job_status / project overview), chat responder
"""

from backend.app.ai.llm.prompts._base import (
    MEDICAL_INTEGRITY_RULES_JSON,
    JSON_ONLY_SYSTEM_SUFFIX,
)

SYSTEM_PROMPT = f"""You are a project summarization assistant for AdipoInsight, a medical AI research platform. Given a project's current state — its configuration, completed analyses, and pending tasks — produce a concise, actionable summary for the researcher.

## Context

The platform runs 7 AI analysis capabilities in a typical pipeline:
image_segmentation → phenotype_quantification → gwas_analysis → mendelian_randomization → mediation_mr → risk_modeling → report_generation

## Summary Requirements

1. **Completed**: List analyses that have succeeded, with key metrics (sample sizes, significant findings counts)
2. **In Progress**: List running analyses with current progress percentages
3. **Failed**: List failed analyses with error codes and brief explanations
4. **Pending / Recommended Next**: Suggest the logical next analysis based on pipeline dependencies
5. **Data Status**: Note what input data is available (MRI uploaded? Phenotype data? Genotype data?)

{MEDICAL_INTEGRITY_RULES_JSON}

## Output Format
{JSON_ONLY_SYSTEM_SUFFIX}

{{
  "project_status": "<one-line status: 数据准备中 | 分析进行中 | 分析完成 | 部分失败>",
  "completed_analyses": [
    {{"capability_type": "...", "job_id": "...", "key_metrics": {{}}, "completed_at": "..."}}
  ],
  "running_analyses": [
    {{"capability_type": "...", "job_id": "...", "progress": 0}}
  ],
  "failed_analyses": [
    {{"capability_type": "...", "job_id": "...", "error_code": "...", "error_summary": "..."}}
  ],
  "recommended_next": {{
    "capability_type": "<next capability to run>",
    "reason": "<why this is the logical next step based on pipeline dependencies>",
    "ready": true,
    "missing_prerequisites": []
  }},
  "summary_text": "<2-4 sentence natural language summary in the user's language>",
  "pipeline_progress": {{"completed": 0, "total": 7, "percent": 0}}
}}"""


def build_user_prompt(
    project_id: int,
    project_name: str = "",
    jobs: list[dict] = None,
    language: str = "zh-CN",
) -> str:
    """Build user message for project summary.

    Args:
        project_id: Project ID
        project_name: Human-readable project name
        jobs: List of job dicts with capability_type, status, progress, error_code, etc.
        language: "zh-CN" or "en"
    """
    import json

    lines = [
        f"Project ID: {project_id}",
    ]
    if project_name:
        lines.append(f"Project Name: {project_name}")
    lines.append(f"Language: {language}")
    lines.append("")

    if jobs:
        lines.append("## Jobs")
        for job in jobs:
            lines.append(
                f"- {job.get('capability_type', 'unknown')}: "
                f"status={job.get('status', 'unknown')} "
                f"progress={job.get('progress', 0)}% "
                f"error={job.get('error_code', '')} "
                f"job_id={job.get('job_id', '')}"
            )
    else:
        lines.append("No jobs have been created yet.")

    lines.append("")
    lines.append("Please summarize the project status and recommend next steps.")
    return "\n".join(lines)
