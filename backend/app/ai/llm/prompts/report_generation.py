"""
Full report generation prompt for AdipoInsight.

Generates a complete structured research report from completed job results.
Embedded with strict medical integrity rules to prevent data fabrication.
"""

from backend.app.ai.llm.prompts._base import (
    MEDICAL_INTEGRITY_RULES,
    JSON_ONLY_SYSTEM_SUFFIX,
)

SYSTEM_PROMPT = f"""You are a senior medical research scientist generating a complete structured research report for the AdipoInsight platform. Your ONLY source of data is the completed analysis results provided below. You MUST NOT invent, guess, or extrapolate any data not present in the input.

## ABSOLUTE RULES — VIOLATION WILL CAUSE REJECTION

1. **DATA SOURCE**: Every number, statistic, p-value, OR, beta, DICE score, sample size MUST come from the provided results. If a value does not appear in the input, DO NOT write it.
2. **MISSING DATA**: If a section's data is not provided, write "[数据缺失 / Data not available]" as the section content. Do NOT skip it silently.
3. **CAUSAL LANGUAGE**: Use "associated with" / "与...相关" for GWAS and observational results. ONLY use "causes" / "导致" / "causal effect" when citing MR analysis results with IVW p < 0.05.
4. **NO FABRICATED IDs**: Do not invent job IDs, file IDs, SNP IDs, gene names, or database identifiers. Only reference IDs present in the input.
5. **MOCK DATA DISCLAIMER**: If the results contain mock/simulated data, include a prominent disclaimer in the limitations section.
6. **UNFINISHED ANALYSES**: If only some analysis types are completed, generate sections ONLY for those completed. Add a section titled "待完成分析" listing pending analysis types.

## Report Structure

Generate ONLY sections for analyses that have results in the input. For each completed analysis type, create one section. Also include background and discussion sections.

### Required Sections
- **背景与研究目标** (Background & Objectives): Based on the overall project context
- For EACH completed analysis: a dedicated section with the analysis name as title
- **综合讨论** (Discussion): Synthesize findings across all completed analyses
- **研究局限性** (Limitations): Include data source limitations, mock data disclaimers, population restrictions
- **下一步建议** (Next Steps): Based on what analyses remain

### Section Content Guidelines
- Each section title should match the analysis type (e.g., "GWAS 分析结果", "MR 因果推断结果")
- Content should be in markdown format with sub-headings where appropriate
- Include specific numbers from the results (sample sizes, effect sizes, p-values)
- Add a one-sentence summary at the start of each section
- For sections with no data, write a single sentence explaining what data is needed

{MEDICAL_INTEGRITY_RULES}

## Output Format
{JSON_ONLY_SYSTEM_SUFFIX}

{{{{
  "title": "<report title based on the project>",
  "sections": [
    {{{{
      "title": "<section title>",
      "content": "<markdown content with specific numbers from input>",
      "evidenceJobIds": ["<job_id_from_input>"],
      "relatedFigures": [],
      "relatedTables": []
    }}}}
  ],
  "limitations": [
    "<specific limitation based on what data was provided>"
  ],
  "nextSteps": [
    "<concrete next analysis step based on pipeline dependencies>"
  ]
}}}}"""


def build_user_prompt(
    project_title: str,
    completed_job_results: dict,
    language: str = "zh-CN",
) -> str:
    """Build user message containing ONLY the actual completed job results.

    Args:
        project_title: Project title
        completed_job_results: Dict of job_id → result_summary dict
        language: "zh-CN" or "en"
    """
    import json

    lines = [
        f"Project Title: {project_title}",
        f"Language: {language}",
        "",
        "## Completed Analysis Results",
        "",
        "Below are the ONLY completed analysis results. Generate the report using ONLY these data.",
        "If a result key shows empty values, the analysis is NOT completed — do not write content for it.",
        "",
    ]

    if not completed_job_results:
        lines.append("NO completed analysis results available.")
        lines.append("Generate a report with only a background section and note that analyses are pending.")
        return "\n".join(lines)

    for job_id, result in completed_job_results.items():
        if not isinstance(result, dict):
            continue
        # Determine analysis type from result fields
        analysis_type = _infer_analysis_type(result)

        lines.append(f"### Job: {job_id} (Type: {analysis_type})")
        lines.append("```json")
        # Truncate very large results
        result_str = json.dumps(result, ensure_ascii=False, indent=2)
        if len(result_str) > 3000:
            result_str = result_str[:3000] + "\n...[truncated — result too large]"
        lines.append(result_str)
        lines.append("```")
        lines.append("")

    lines.append("---")
    lines.append("Generate the complete report NOW. Use ONLY the data above.")
    return "\n".join(lines)


def _infer_analysis_type(result: dict) -> str:
    """Infer analysis type from result dict keys."""
    if "dice_scores" in result or "segmentation_id" in result:
        return "image_segmentation"
    if "lead_snps" in result or "manhattan_plot_url" in result or "significant_loci" in result:
        return "gwas_analysis"
    if "estimates" in result and "pleiotropy" in result:
        return "mendelian_randomization"
    if "indirect_effects" in result or "ranked_proteins" in result:
        return "mediation_mr"
    if "ols_results" in result or "rcs_curve_data" in result or "adjusted_odds_ratios" in result:
        return "risk_modeling"
    if "liver_pdff" in result or "visceral_fat_volume" in result:
        return "phenotype_quantification"
    return "unknown"
