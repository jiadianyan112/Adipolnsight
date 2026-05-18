"""
AdipoInsight LLM Prompt Templates

Centralized prompt library for all LLM-powered capabilities.
Each module exports a SYSTEM_PROMPT constant and a build_user_prompt() function.

Usage:
    from backend.app.ai.llm.prompts import (
        INTENT_PARSER_PROMPT, build_intent_user_prompt,
        RESULT_INTERPRETER_PROMPT, build_result_interpreter_user_prompt,
        ERROR_EXPLAINER_PROMPT, build_error_explainer_user_prompt,
        REPORT_ENHANCER_PROMPT, build_report_enhancer_user_prompt,
        CHAT_PROMPT, build_chat_user_prompt,
        PARAM_COMPLETION_PROMPT, build_param_completion_user_prompt,
        SUMMARY_PROMPT, build_summary_user_prompt,
        MEDICAL_INTEGRITY_RULES,
        MEDICAL_INTEGRITY_RULES_JSON,
        JSON_ONLY_INSTRUCTION,
        get_prompt,
        list_prompts,
    )

Task type → prompt mapping:

    intent_parse       → INTENT_PARSER_PROMPT
    parameter_completion → PARAM_COMPLETION_PROMPT
    result_interpretation → RESULT_INTERPRETER_PROMPT
    error_explanation  → ERROR_EXPLAINER_PROMPT
    report_generation  → REPORT_ENHANCER_PROMPT
    chat               → CHAT_PROMPT
    summary            → SUMMARY_PROMPT
"""

from typing import Dict, Optional

from backend.app.ai.llm.prompts._base import (
    MEDICAL_INTEGRITY_RULES,
    MEDICAL_INTEGRITY_RULES_JSON,
    REPORT_INTEGRITY_RULES,
    JSON_ONLY_INSTRUCTION,
    JSON_ONLY_SYSTEM_SUFFIX,
)

from backend.app.ai.llm.prompts.intent_parser import (
    SYSTEM_PROMPT as INTENT_PARSER_PROMPT,
    build_user_prompt as build_intent_user_prompt,
)

from backend.app.ai.llm.prompts.parameter_completion import (
    SYSTEM_PROMPT as PARAM_COMPLETION_PROMPT,
    build_user_prompt as build_param_completion_user_prompt,
)

from backend.app.ai.llm.prompts.result_interpreter import (
    SYSTEM_PROMPT as RESULT_INTERPRETER_PROMPT,
    build_user_prompt as build_result_interpreter_user_prompt,
)

from backend.app.ai.llm.prompts.error_explainer import (
    SYSTEM_PROMPT as ERROR_EXPLAINER_PROMPT,
    build_user_prompt as build_error_explainer_user_prompt,
)

from backend.app.ai.llm.prompts.report_enhancer import (
    SYSTEM_PROMPT as REPORT_ENHANCER_PROMPT,
    build_user_prompt as build_report_enhancer_user_prompt,
)

from backend.app.ai.llm.prompts.report_generation import (
    SYSTEM_PROMPT as REPORT_GENERATION_PROMPT,
    build_user_prompt as build_report_generation_user_prompt,
)

from backend.app.ai.llm.prompts.chat import (
    SYSTEM_PROMPT as CHAT_PROMPT,
    build_user_prompt as build_chat_user_prompt,
)

from backend.app.ai.llm.prompts.summary import (
    SYSTEM_PROMPT as SUMMARY_PROMPT,
    build_user_prompt as build_summary_user_prompt,
)

# ===== Prompt registry (task_type → System Prompt) =====

_PROMPT_REGISTRY: Dict[str, str] = {
    "intent_parse": INTENT_PARSER_PROMPT,
    "parameter_completion": PARAM_COMPLETION_PROMPT,
    "result_interpretation": RESULT_INTERPRETER_PROMPT,
    "error_explanation": ERROR_EXPLAINER_PROMPT,
    "report_generation": REPORT_GENERATION_PROMPT,
    "chat": CHAT_PROMPT,
    "summary": SUMMARY_PROMPT,
}

# ===== User prompt builders (task_type → builder function) =====

_BUILDER_REGISTRY: Dict[str, callable] = {
    "intent_parse": build_intent_user_prompt,
    "parameter_completion": build_param_completion_user_prompt,
    "result_interpretation": build_result_interpreter_user_prompt,
    "error_explanation": build_error_explainer_user_prompt,
    "report_generation": build_report_generation_user_prompt,
    "chat": build_chat_user_prompt,
    "summary": build_summary_user_prompt,
}


def get_prompt(task_type: str) -> Optional[str]:
    """Get the system prompt for a given LLM task type."""
    return _PROMPT_REGISTRY.get(task_type)


def get_builder(task_type: str) -> Optional[callable]:
    """Get the user prompt builder for a given LLM task type."""
    return _BUILDER_REGISTRY.get(task_type)


def list_prompts() -> Dict[str, bool]:
    """List all available prompt types and whether they have a builder."""
    return {k: k in _BUILDER_REGISTRY for k in _PROMPT_REGISTRY}


__all__ = [
    # System prompts (by task type)
    "INTENT_PARSER_PROMPT",
    "PARAM_COMPLETION_PROMPT",
    "RESULT_INTERPRETER_PROMPT",
    "ERROR_EXPLAINER_PROMPT",
    "REPORT_ENHANCER_PROMPT",
    "CHAT_PROMPT",
    "SUMMARY_PROMPT",
    # User prompt builders
    "build_intent_user_prompt",
    "build_param_completion_user_prompt",
    "build_result_interpreter_user_prompt",
    "build_error_explainer_user_prompt",
    "build_report_enhancer_user_prompt",
    "build_chat_user_prompt",
    "build_summary_user_prompt",
    # Shared integrity rules
    "MEDICAL_INTEGRITY_RULES",
    "MEDICAL_INTEGRITY_RULES_JSON",
    "REPORT_INTEGRITY_RULES",
    "JSON_ONLY_INSTRUCTION",
    # Registry helpers
    "get_prompt",
    "get_builder",
    "list_prompts",
]
