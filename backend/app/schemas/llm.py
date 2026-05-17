"""
AdipoInsight LLM Pydantic Schema 定义

与前端 types/llm.ts 中 TypeScript 类型保持一一对应。
所有 schema 可被 LLM Provider、Agent Orchestrator、Report Skill 等模块复用。
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# ===== Provider =====

LLM_PROVIDER_NAME = Literal["mock", "deepseek", "openai"]

# ===== Task Type =====

LLM_TASK_TYPE = Literal[
    "intent_parse",
    "parameter_completion",
    "report_generation",
    "result_interpretation",
    "chat",
    "error_explanation",
    "summary",
]

# ===== Message =====

LLM_MESSAGE_ROLE = Literal["system", "user", "assistant", "tool"]


class LLMMessage(BaseModel):
    role: LLM_MESSAGE_ROLE
    content: str
    name: Optional[str] = None


# ===== Request =====

LLM_RESPONSE_FORMAT = Literal["text", "json"]


class LLMRequest(BaseModel):
    provider: Optional[str] = None    # 允许任意字符串，未注册 provider 由 service 层 fallback
    model: Optional[str] = None
    messages: List[LLMMessage] = Field(..., min_length=1)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, alias="maxTokens")
    response_format: LLM_RESPONSE_FORMAT = Field(default="text", alias="responseFormat")
    stream: bool = False
    task_type: LLM_TASK_TYPE = Field(..., alias="taskType")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


# ===== Response =====

class LLMUsage(BaseModel):
    prompt_tokens: int = Field(default=0, alias="promptTokens")
    completion_tokens: int = Field(default=0, alias="completionTokens")
    total_tokens: int = Field(default=0, alias="totalTokens")

    model_config = {"populate_by_name": True}


class LLMResponse(BaseModel):
    content: str
    json_data: Optional[Any] = Field(default=None, alias="json")
    usage: Optional[LLMUsage] = None
    provider: LLM_PROVIDER_NAME
    model: str
    raw: Optional[Any] = None

    model_config = {"populate_by_name": True}


# ===== Error =====

class LLMError(BaseModel):
    code: str
    message: str
    provider: LLM_PROVIDER_NAME
    retryable: bool
    raw: Optional[Any] = None


# ===== Intent Parse =====

class LLMIntentResult(BaseModel):
    """LLM 意图解析输出（camelCase，与 DeepSeek JSON 输出对齐）"""
    intent: str
    confidence: float = Field(ge=0, le=1)
    capability_type: str = Field(default="", alias="capabilityType")
    extracted_params: Dict[str, Any] = Field(default_factory=dict, alias="extractedParams")
    missing_params: List[str] = Field(default_factory=list, alias="missingParams")
    next_action: str = Field(default="", alias="nextAction")
    user_message: str = Field(default="", alias="userMessage")

    model_config = {"populate_by_name": True}


# ===== Result Interpretation =====

class LLMResultInterpretation(BaseModel):
    capability_type: str
    summary: str
    key_findings: List[str] = Field(default_factory=list)
    clinical_significance: str = ""
    limitations: List[str] = Field(default_factory=list)
    suggested_next_steps: List[str] = Field(default_factory=list)


# ===== Error Explanation =====

class LLMErrorExplanation(BaseModel):
    error_code: str
    friendly_message: str
    possible_causes: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    is_retryable: bool = False


# ===== Report Enhancement =====

class LLMReportEnhancement(BaseModel):
    discussion_section: str = ""
    conclusion_section: str = ""
    clinical_implications: str = ""
    future_directions: str = ""
    abstract: str = ""


# ===== Chat Context =====

class LLMChatContext(BaseModel):
    project_id: int = 0
    recent_jobs: List[dict] = Field(default_factory=list)
    available_capabilities: List[str] = Field(default_factory=list)
    conversation_history: List[LLMMessage] = Field(default_factory=list)
