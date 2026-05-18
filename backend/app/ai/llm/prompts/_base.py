"""
Shared medical integrity rules for all AdipoInsight LLM prompts.

Every prompt that produces scientific, clinical, or analytical output
must embed these rules (or a task-specific variant).
"""

# ===== Full medical integrity ruleset =====

MEDICAL_INTEGRITY_RULES = """## MEDICAL INTEGRITY RULES — VIOLATION WILL CAUSE REJECTION

1. **No fabricated data**: DO NOT invent, guess, or hallucinate any numerical results, statistics,
   p-values, effect sizes, odds ratios, DICE scores, sample sizes, or any other quantitative values.
2. **No invented identifiers**: DO NOT create fake job IDs, file IDs, dataset IDs, file paths, URLs,
   or any resource identifiers. If you don't know an ID, omit it or explicitly state "unknown".
3. **Correlation ≠ Causation**: DO NOT present correlational findings as causal unless the evidence
   explicitly comes from Mendelian Randomization (MR) or a randomized controlled trial design.
   For GWAS, observational, or cross-sectional findings, use language like "associated with",
   "correlated with", "linked to" — never "causes", "leads to", or "triggers".
4. **No exaggerated clinical claims**: DO NOT make therapeutic recommendations, clinical practice
   guidelines, or claims of clinical utility beyond what the data supports. Use qualifiers like
   "suggests", "may indicate", "warrants further investigation".
5. **Traceability**: Every numerical statement you make MUST be directly traceable to the input
   data provided to you. If a number does not appear in the input, DO NOT output it.
6. **Missing data must be declared**: If a required data point is missing, explicitly state
   "数据缺失 / Data not available" rather than omitting or making up a value.
7. **No external citations**: DO NOT cite specific papers, DOIs, authors, or journal names
   unless they are EXPLICITLY provided in the input data.
8. **Uncertainty disclosure**: When evidence is weak (small sample, wide confidence intervals,
   borderline significance), explicitly mention the uncertainty and its implications."""

# ===== Abbreviated version for JSON-only prompts =====

MEDICAL_INTEGRITY_RULES_JSON = """## CRITICAL MEDICAL INTEGRITY RULES

1. NO fabricated data — every number must come from the input
2. NO invented IDs (jobId, fileId, datasetId) — use only IDs from the input
3. Correlation ≠ Causation — say "associated with" not "causes" unless MR evidence is present
4. NO exaggerated clinical claims
5. Missing data → explicitly output as "missing" / "数据缺失"
6. NO external citations unless provided in input"""

# ===== Rules for report generation specifically =====

REPORT_INTEGRITY_RULES = """## REPORT INTEGRITY RULES

1. **Data provenance**: Every statistic, table cell, and figure reference must correspond to
   actual analysis results provided in the input. Use "[数据缺失]" for unavailable sections.
2. **Causal language gate**: Only use causal language (causes/increases/decreases risk) when
   citing MR analysis results. For GWAS associations, use "associated with" / "与...相关".
3. **Clinical restraint**: Label all findings as "research-stage". Add a disclaimer that
   the report is AI-generated and not for clinical decision-making.
4. **Limitations mandatory**: Every report must include a limitations section acknowledging
   data sources (mock vs real), population restrictions, and methodological constraints.
5. **Reference discipline**: Only include references that are provided in the input data.
   Do not fabricate DOIs or paper titles."""

# ===== JSON output enforcement =====

JSON_ONLY_INSTRUCTION = (
    "You MUST respond with a single valid JSON object. "
    "No markdown fences, no explanations outside the JSON. "
    "The JSON must conform exactly to the schema described above."
)

JSON_ONLY_SYSTEM_SUFFIX = (
    "\n\nOUTPUT FORMAT: You MUST respond with ONLY a valid JSON object. "
    "No markdown code blocks (```), no leading text, no trailing text. "
    "The entire response must parse as JSON."
)
