/**
 * AdipoInsight LLM 类型系统
 *
 * 所有 LLM 相关类型集中定义，可被：
 * - Agent Orchestrator（意图解析）
 * - Report Skill（报告增强）
 * - Result Interpreter（结果解读）
 * - Error Explainer（错误解释）
 * - ChatInput 组件（对话）
 * - aiService（API 调用）
 * 复用。
 */

// ===== Provider =====

export type LLMProviderName = 'mock' | 'deepseek' | 'openai';

export const LLM_PROVIDER_LABELS: Record<LLMProviderName, string> = {
  mock: 'Mock (本地)',
  deepseek: 'DeepSeek',
  openai: 'OpenAI',
};

// ===== Task Type =====

export type LLMTaskType =
  | 'intent_parse'
  | 'parameter_completion'
  | 'report_generation'
  | 'result_interpretation'
  | 'chat'
  | 'error_explanation'
  | 'summary';

export const LLM_TASK_LABELS: Record<LLMTaskType, string> = {
  intent_parse: '意图解析',
  parameter_completion: '参数补全',
  report_generation: '报告生成',
  result_interpretation: '结果解读',
  chat: '对话',
  error_explanation: '错误解释',
  summary: '摘要',
};

// ===== Message =====

export type LLMMessageRole = 'system' | 'user' | 'assistant' | 'tool';

export interface LLMMessage {
  role: LLMMessageRole;
  content: string;
  /** tool 消息的 tool name（可选） */
  name?: string;
}

// ===== Request =====

export type LLMResponseFormat = 'text' | 'json';

export interface LLMRequest {
  /** LLM 提供商（默认从配置读取） */
  provider?: LLMProviderName;
  /** 模型名称（默认从配置读取） */
  model?: string;
  /** 消息列表 */
  messages: LLMMessage[];
  /** 温度 (0–2)，默认 0.1 */
  temperature?: number;
  /** 最大 token 数 */
  maxTokens?: number;
  /** 响应格式 */
  responseFormat?: LLMResponseFormat;
  /** 是否流式输出 */
  stream?: boolean;
  /** 任务类型 */
  taskType: LLMTaskType;
  /** 额外元信息 */
  metadata?: Record<string, unknown>;
}

// ===== Response =====

export interface LLMUsage {
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
}

export interface LLMResponse {
  /** 文本内容 */
  content: string;
  /** 如果 responseFormat='json'，解析后的 JSON */
  json?: unknown;
  /** Token 使用统计 */
  usage?: LLMUsage;
  /** 实际使用的 provider */
  provider: LLMProviderName;
  /** 实际使用的 model */
  model: string;
  /** 原始响应（调试用） */
  raw?: unknown;
}

// ===== Error =====

export interface LLMError {
  /** 错误码 */
  code: string;
  /** 人类可读错误消息 */
  message: string;
  /** 出错的 provider */
  provider: LLMProviderName;
  /** 是否可重试 */
  retryable: boolean;
  /** 原始错误（调试用） */
  raw?: unknown;
}

// ===== Intent Parse 专用 =====

/** 标准 intent 枚举（与后端 STANDARD_INTENT 对齐） */
export type StandardIntent =
  | 'segmentation' | 'phenotype' | 'gwas' | 'mr' | 'mediation_mr'
  | 'risk_modeling' | 'report' | 'result_interpretation'
  | 'job_status' | 'chat' | 'unsupported';

export interface LLMIntentResult {
  intent: StandardIntent;
  confidence: number;
  capability_type: string;
  extracted_params: Record<string, unknown>;
  missing_params: string[];
  next_action: string;
  user_message: string;
  source: 'rule' | 'llm' | 'hybrid';
  warnings: string[];
  reasoning: string;
}

// ===== Result Interpretation 专用 =====

export interface LLMResultInterpretation {
  capability_type: string;
  summary: string;
  key_findings: string[];
  clinical_significance: string;
  limitations: string[];
  suggested_next_steps: string[];
}

// ===== Error Explanation 专用 =====

export interface LLMErrorExplanation {
  error_code: string;
  friendly_message: string;
  possible_causes: string[];
  suggested_actions: string[];
  is_retryable: boolean;
}

// ===== Report Enhancement 专用 =====

export interface LLMReportEnhancement {
  discussion_section: string;
  conclusion_section: string;
  clinical_implications: string;
  future_directions: string;
  abstract: string;
}

// ===== Chat 专用 =====

export interface LLMChatContext {
  project_id?: number;
  recent_jobs?: { job_id: string; capability_type: string; status: string }[];
  available_capabilities?: string[];
  conversation_history?: LLMMessage[];
}
