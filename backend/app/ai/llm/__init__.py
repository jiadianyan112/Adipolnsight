"""
AdipoInsight LLM 模块

统一 LLM Provider 抽象层，支持:
- MockProvider: 本地开发，无 API KEY 时使用
- DeepSeekProvider: DeepSeek API（需 DEEPSEEK_API_KEY）
- HybridIntentParser: rule → LLM → fallback 意图解析

用法:
    from backend.app.ai.llm import llm_service, hybrid_intent_parser

    result = hybrid_intent_parser.parse("做 GWAS 分析")
"""

from backend.app.ai.llm.provider import (
    LLMProvider,
    MockProvider,
    ProviderRegistry,
    provider_registry,
)
from backend.app.ai.llm.deepseek_provider import DeepSeekProvider
from backend.app.ai.llm.service import LLMService, llm_service
from backend.app.ai.llm.deepseek_intent_parser import LLMIntentParser, llm_intent_parser
from backend.app.ai.llm.hybrid_intent_parser import HybridIntentParser, hybrid_intent_parser
from backend.app.ai.llm.schema_validator import LLMSchemaValidator, schema_validator
from backend.app.ai.llm.parameter_completer import (
    ParameterCompletionService,
    ParameterCompletionInput,
    ParameterCompletionOutput,
    SuggestedInput,
    parameter_completer,
)
from backend.app.ai.llm.error_explainer import (
    ErrorExplanationService,
    ErrorExplanationInput,
    ErrorExplanationOutput,
    error_explainer,
)

# 自动注册 DeepSeekProvider（如果 API KEY 未设置则静默跳过）
try:
    provider_registry.register(DeepSeekProvider())
except ValueError:
    pass

__all__ = [
    "LLMProvider",
    "MockProvider",
    "DeepSeekProvider",
    "ProviderRegistry",
    "provider_registry",
    "LLMService",
    "llm_service",
    "LLMIntentParser",
    "llm_intent_parser",
    "HybridIntentParser",
    "hybrid_intent_parser",
    "LLMSchemaValidator",
    "schema_validator",
    "ParameterCompletionService",
    "ParameterCompletionInput",
    "ParameterCompletionOutput",
    "SuggestedInput",
    "parameter_completer",
    "ErrorExplanationService",
    "ErrorExplanationInput",
    "ErrorExplanationOutput",
    "error_explainer",
]
