/**
 * AdipoInsight 统一错误处理
 *
 * 所有 AI API 调用错误通过此模块转换为用户友好的中文提示。
 * 前端组件不应直接展示后端原始错误信息。
 */

// ===== 错误码 → 中文提示 =====

const ERROR_MESSAGES_ZH: Record<string, string> = {
  // 输入校验
  INVALID_INPUT: '输入参数不合法，请检查后重试',
  FILE_TOO_LARGE: '文件大小超过限制（最大 200MB）',
  UNSUPPORTED_FILE_TYPE: '不支持的文件格式，请使用 .nii/.nii.gz/.dcm/.zip/.nrrd',
  MISSING_REQUIRED_PARAM: '缺少必要参数，请补充后重试',
  INVALID_PARAMETER: '参数值不合法，请检查后重试',

  // 资源不存在
  JOB_NOT_FOUND: '任务不存在或已被删除',
  RESULT_NOT_FOUND: '分析结果尚未生成，请等待任务完成',
  FILE_NOT_FOUND: '文件不存在或已被删除',
  PROJECT_NOT_FOUND: '项目不存在',

  // 任务状态
  JOB_FAILED: '任务执行失败',
  JOB_ALREADY_CANCELLED: '任务已被取消',
  JOB_ALREADY_TERMINAL: '任务已结束，无法重复操作',
  UPSTREAM_DEPENDENCY_FAILED: '上游依赖任务未完成，请先执行前置分析',

  // Skill
  SKILL_NOT_AVAILABLE: '该 AI 能力暂不可用，请稍后重试',
  ADAPTER_NOT_FOUND: 'AI 能力适配器未找到，请联系管理员',
  SKILL_EXECUTION_ERROR: 'AI 能力执行异常，请重试',

  // 脚本
  SCRIPT_NOT_FOUND: '分析脚本缺失，请联系管理员',
  SCRIPT_EXECUTION_FAILED: '分析脚本运行失败',
  SCRIPT_EXECUTION_ERROR: '分析脚本运行异常',
  OUTPUT_JSON_INVALID: '分析结果格式异常',
  OUTPUT_FILE_MISSING: '分析输出文件缺失',

  // 外部服务
  MODEL_SERVICE_ERROR: 'AI 模型服务异常，请稍后重试',
  LLM_API_ERROR: '大模型 API 调用失败，请稍后重试',
  EXTERNAL_API_ERROR: '外部数据 API 调用失败，请稍后重试',

  // 系统
  DATABASE_ERROR: '数据库异常，请稍后重试',
  TASK_TIMEOUT: '任务执行超时（超过 5 分钟），请检查数据后重试',
  NOT_IMPLEMENTED: '该功能尚未实现',
  INTERNAL_ERROR: '系统内部错误，请稍后重试',
  UNKNOWN_ERROR: '未知错误',

  // 网络
  NETWORK_ERROR: '网络连接失败，请检查后端服务是否启动',
  EMPTY_RESPONSE: '后端返回空响应，请稍后重试',
};

/** 错误码 → HTTP 状态码提示后缀 */
function statusSuffix(status: number | null): string {
  if (!status) return '';
  if (status === 401 || status === 403) return '（权限不足）';
  if (status >= 500) return '（服务器异常）';
  if (status >= 400) return '（请求异常）';
  return '';
}

// ===== 类型 =====

export interface AppError {
  code: string;
  message: string;
  detail?: string;
  statusCode: number | null;
  isNetworkError: boolean;
  isServerError: boolean;
}

// ===== 错误处理函数 =====

export function handleApiError(
  errorCode: string,
  backendMessage?: string,
  statusCode?: number | null,
): AppError {
  const friendlyMessage = ERROR_MESSAGES_ZH[errorCode] || backendMessage || '未知错误';
  const suffix = statusSuffix(statusCode ?? null);

  return {
    code: errorCode,
    message: suffix ? `${friendlyMessage} ${suffix}` : friendlyMessage,
    detail: backendMessage || undefined,
    statusCode: statusCode ?? null,
    isNetworkError: errorCode === 'NETWORK_ERROR',
    isServerError: (statusCode ?? 0) >= 500 || errorCode === 'EMPTY_RESPONSE',
  };
}

/** 从通用 Error 对象提取 AppError */
export function parseError(err: unknown): AppError {
  if (err instanceof Error) {
    // 检查是否包含错误码（从后端返回的 detail 中提取）
    const msg = err.message;
    // 尝试匹配已知错误码
    for (const code of Object.keys(ERROR_MESSAGES_ZH)) {
      if (msg.includes(code)) {
        return handleApiError(code, msg);
      }
    }
    // 网络错误
    if (msg.includes('Network Error') || msg.includes('ERR_NETWORK')) {
      return handleApiError('NETWORK_ERROR');
    }
    if (msg.includes('timeout') || msg.includes('ECONNABORTED')) {
      return { code: 'TASK_TIMEOUT', message: ERROR_MESSAGES_ZH.TASK_TIMEOUT, statusCode: null, isNetworkError: true, isServerError: false };
    }
    return { code: 'UNKNOWN_ERROR', message: msg, statusCode: null, isNetworkError: false, isServerError: false };
  }
  return { code: 'UNKNOWN_ERROR', message: String(err), statusCode: null, isNetworkError: false, isServerError: false };
}

/** 错误码是否表示需要用户操作 */
export function isRetryable(code: string): boolean {
  const retryable = new Set([
    'NETWORK_ERROR', 'TASK_TIMEOUT', 'EMPTY_RESPONSE',
    'MODEL_SERVICE_ERROR', 'LLM_API_ERROR', 'EXTERNAL_API_ERROR',
    'SCRIPT_EXECUTION_FAILED', 'SCRIPT_EXECUTION_ERROR',
    'SKILL_EXECUTION_ERROR', 'SKILL_NOT_AVAILABLE',
    'DATABASE_ERROR', 'INTERNAL_ERROR',
  ]);
  return retryable.has(code);
}

/** 错误码是否表示需要用户修正输入 */
export function isInputError(code: string): boolean {
  const inputErrors = new Set([
    'INVALID_INPUT', 'INVALID_PARAMETER', 'MISSING_REQUIRED_PARAM',
    'FILE_TOO_LARGE', 'UNSUPPORTED_FILE_TYPE',
  ]);
  return inputErrors.has(code);
}

// ===== 调试用：列出所有错误码 =====

export function listAllErrorCodes(): string[] {
  return Object.keys(ERROR_MESSAGES_ZH);
}
