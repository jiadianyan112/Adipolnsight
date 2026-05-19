/**
 * 统一的异步 Job 状态模型
 *
 * 解决问题：后端新旧 API 返回的状态字符串不统一：
 *   旧 API (AnalysisTask):  pending | running | success  | failed | cancelled
 *   新 API (AIJobFromAPI): queued  | running | succeeded | failed | cancelled
 *   页面组件:              各写各的字符串判断，容易遗漏变体导致 UI 卡死
 *
 * 所有状态归一化为此文件导出的 NormalizedJobStatus。
 * 页面组件禁止直接做字符串比较，应使用导出的 isXxx 函数。
 */

// ===== 归一化状态枚举 =====

export const NORMALIZED_STATUS = {
  QUEUED: 'queued',
  RUNNING: 'running',
  SUCCEEDED: 'succeeded',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  UNKNOWN: 'unknown',
} as const;

export type NormalizedJobStatus = (typeof NORMALIZED_STATUS)[keyof typeof NORMALIZED_STATUS];

// ===== 后端原始字符串 → 归一化状态映射 =====

const RAW_STATUS_MAP: Record<string, NormalizedJobStatus> = {
  // 排队中
  pending: NORMALIZED_STATUS.QUEUED,
  queued: NORMALIZED_STATUS.QUEUED,
  // 运行中
  running: NORMALIZED_STATUS.RUNNING,
  processing: NORMALIZED_STATUS.RUNNING,
  // 成功
  success: NORMALIZED_STATUS.SUCCEEDED,
  succeeded: NORMALIZED_STATUS.SUCCEEDED,
  completed: NORMALIZED_STATUS.SUCCEEDED,
  complete: NORMALIZED_STATUS.SUCCEEDED,
  // 失败
  failed: NORMALIZED_STATUS.FAILED,
  error: NORMALIZED_STATUS.FAILED,
  // 取消
  cancelled: NORMALIZED_STATUS.CANCELLED,
  canceled: NORMALIZED_STATUS.CANCELLED,
};

/**
 * 将后端返回的任意状态字符串归一化为 NormalizedJobStatus。
 * 无法识别的字符串返回 'unknown'。
 */
export function normalizeJobStatus(raw: string | null | undefined): NormalizedJobStatus {
  if (!raw) return NORMALIZED_STATUS.UNKNOWN;
  const key = raw.trim().toLowerCase();
  return RAW_STATUS_MAP[key] ?? NORMALIZED_STATUS.UNKNOWN;
}

// ===== 状态判断（页面组件唯一入口） =====

/** 是否为终态（成功 / 失败 / 取消） */
export function isTerminal(status: NormalizedJobStatus): boolean {
  return status === NORMALIZED_STATUS.SUCCEEDED
    || status === NORMALIZED_STATUS.FAILED
    || status === NORMALIZED_STATUS.CANCELLED;
}

/** 是否为成功终态 */
export function isSuccess(status: NormalizedJobStatus): boolean {
  return status === NORMALIZED_STATUS.SUCCEEDED;
}

/** 是否为失败终态 */
export function isFailed(status: NormalizedJobStatus): boolean {
  return status === NORMALIZED_STATUS.FAILED;
}

/** 是否为取消终态 */
export function isCancelled(status: NormalizedJobStatus): boolean {
  return status === NORMALIZED_STATUS.CANCELLED;
}

/** 是否为进行中 */
export function isRunning(status: NormalizedJobStatus): boolean {
  return status === NORMALIZED_STATUS.RUNNING;
}

/** 是否为排队中 */
export function isQueued(status: NormalizedJobStatus): boolean {
  return status === NORMALIZED_STATUS.QUEUED;
}

/** 是否为活跃状态（排队/运行中） */
export function isActive(status: NormalizedJobStatus): boolean {
  return status === NORMALIZED_STATUS.QUEUED || status === NORMALIZED_STATUS.RUNNING;
}

// ===== 兼容旧 API 的别名 =====

/** @deprecated 使用 isSuccessRaw */
export const isSuccessStatus = isSuccessRaw;
/** @deprecated 使用 isFailedRaw */
export const isFailedStatus = isFailedRaw;
/** @deprecated 使用 isTerminalRaw */
export const isTerminalStatus = isTerminalRaw;

// ===== 从原始字符串直接判断（便捷方法，无需先 normalize） =====

export function isSuccessRaw(raw: string | null | undefined): boolean {
  return isSuccess(normalizeJobStatus(raw));
}

export function isFailedRaw(raw: string | null | undefined): boolean {
  return isFailed(normalizeJobStatus(raw));
}

export function isTerminalRaw(raw: string | null | undefined): boolean {
  return isTerminal(normalizeJobStatus(raw));
}

export function isRunningRaw(raw: string | null | undefined): boolean {
  return isRunning(normalizeJobStatus(raw));
}

export function isActiveRaw(raw: string | null | undefined): boolean {
  return isActive(normalizeJobStatus(raw));
}

// ===== 中文标签 =====

export const STATUS_LABEL: Record<NormalizedJobStatus, string> = {
  [NORMALIZED_STATUS.QUEUED]: '排队中',
  [NORMALIZED_STATUS.RUNNING]: '运行中',
  [NORMALIZED_STATUS.SUCCEEDED]: '已完成',
  [NORMALIZED_STATUS.FAILED]: '失败',
  [NORMALIZED_STATUS.CANCELLED]: '已取消',
  [NORMALIZED_STATUS.UNKNOWN]: '未知',
};

// ===== UI 展示配置 =====

export interface StatusUIConfig {
  dot: string;
  text: string;
  line: string;
}

export const STATUS_UI: Record<NormalizedJobStatus, StatusUIConfig> = {
  [NORMALIZED_STATUS.SUCCEEDED]: {
    dot: 'bg-green-500',
    text: 'text-green-600',
    line: 'bg-green-300',
  },
  [NORMALIZED_STATUS.RUNNING]: {
    dot: 'bg-navy-600 animate-pulse',
    text: 'text-navy-700 font-semibold',
    line: 'bg-navy-300',
  },
  [NORMALIZED_STATUS.FAILED]: {
    dot: 'bg-danger-600',
    text: 'text-danger-600',
    line: 'bg-danger-200',
  },
  [NORMALIZED_STATUS.QUEUED]: {
    dot: 'bg-text-muted',
    text: 'text-text-muted',
    line: 'bg-border',
  },
  [NORMALIZED_STATUS.CANCELLED]: {
    dot: 'bg-gold-400',
    text: 'text-gold-600',
    line: 'bg-gold-200',
  },
  [NORMALIZED_STATUS.UNKNOWN]: {
    dot: 'bg-text-muted',
    text: 'text-text-muted',
    line: 'bg-border',
  },
};
