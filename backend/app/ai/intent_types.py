"""
Shared intent type definitions.

Used by rule-based parser, LLM parser, hybrid parser, and Agent Orchestrator.
Extracted to a separate module to avoid circular imports and to ensure
Agent Orchestrator does not depend directly on the rule-based intent_parser module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

# ===== Standard intent enum =====

STANDARD_INTENT = (
    "segmentation", "phenotype", "gwas", "mr", "mediation_mr",
    "risk_modeling", "report", "result_interpretation",
    "job_status", "chat", "unsupported",
)

IntentSource = Literal["rule", "llm", "hybrid"]


@dataclass
class IntentParseResult:
    """
    Standard intent parse result (used uniformly by rule / llm / hybrid parsers).

    The frontend AI Agent uses the `intent` field to decide which status card to display:
    - segmentation/phenotype/gwas/mr/mediation_mr/risk_modeling/report → create job
    - result_interpretation → result interpretation
    - job_status → check job status
    - chat → general chat reply
    - unsupported → not supported
    """
    intent: str                                # standard intent enum value
    confidence: float = 0.0                    # 0.0–1.0
    capability_type: str = ""                  # AI capability type (e.g. "gwas_analysis")
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    missing_params: List[str] = field(default_factory=list)
    next_action: str = ""                      # suggested next action name
    user_message: str = ""                     # human-friendly message for display
    source: str = "rule"                       # rule | llm | hybrid
    warnings: List[str] = field(default_factory=list)
    raw_input: str = ""

    # Backward-compatible aliases
    @property
    def clarification_needed(self) -> bool:
        return self.intent == "unsupported" or len(self.missing_params) > 0

    @property
    def clarification_question(self) -> str:
        return self.user_message


# Backward-compatible alias
IntentResult = IntentParseResult
