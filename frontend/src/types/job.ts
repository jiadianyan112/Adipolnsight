/**
 * AdipoInsight AI 任务/Job 生命周期类型定义
 *
 * 覆盖任务创建 → 运行中 → 成功/失败/取消 的完整状态机，
 * 以及进度上报、错误码、轮询配置等。
 */

import type { AICapabilityType } from './ai';

// ===== 任务状态 =====

/** 任务生命周期状态 */
export type AIJobStatus =
  | 'pending'
  | 'running'
  | 'success'
  | 'failed'
  | 'cancelled';

/** 终态集合 */
export const AI_JOB_TERMINAL_STATUSES: ReadonlySet<AIJobStatus> = new Set([
  'success',
  'failed',
  'cancelled',
]);

/** 状态标签（中文） */
export const AI_JOB_STATUS_LABELS: Record<AIJobStatus, string> = {
  pending: '待开始',
  running: '运行中',
  success: '已完成',
  failed: '失败',
  cancelled: '已取消',
};

// ===== 进度 =====

/** 标准进度里程碑 */
export interface AIJobProgress {
  /** 0–100 */
  percent: number;
  /** 当前阶段描述 */
  stage: string;
  /** 阶段开始时间 */
  stage_started_at: string | null;
}

/** 预定义进度阶段 */
export const PROGRESS_STAGES = {
  INIT: { percent: 0, label: '初始化' },
  VALIDATING: { percent: 10, label: '校验输入' },
  BUILDING: { percent: 20, label: '构建执行命令' },
  SUBMITTED: { percent: 30, label: '已提交执行' },
  PROCESSING: { percent: 50, label: '处理中' },
  COMPLETING: { percent: 70, label: '解析结果' },
  PERSISTING: { percent: 90, label: '持久化结果' },
  DONE: { percent: 100, label: '完成' },
} as const;

// ===== 错误码 =====

/** 任务错误码枚举 */
export type AIJobErrorCode =
  | 'ADAPTER_NOT_FOUND'
  | 'INVALID_INPUT'
  | 'SCRIPT_NOT_FOUND'
  | 'SCRIPT_EXECUTION_FAILED'
  | 'OUTPUT_JSON_INVALID'
  | 'OUTPUT_FILE_MISSING'
  | 'TASK_TIMEOUT'
  | 'FILE_NOT_FOUND'
  | 'DATABASE_ERROR'
  | 'UPSTREAM_DEPENDENCY_FAILED'
  | 'UNKNOWN_ERROR';

/** 错误码 human-readable 描述 */
export const AI_JOB_ERROR_LABELS: Record<AIJobErrorCode, string> = {
  ADAPTER_NOT_FOUND: '未找到对应的 AI 能力适配器',
  INVALID_INPUT: '输入参数不满足最低要求',
  SCRIPT_NOT_FOUND: '分析脚本路径不存在',
  SCRIPT_EXECUTION_FAILED: '脚本执行返回非零退出码',
  OUTPUT_JSON_INVALID: '输出 JSON 解析失败',
  OUTPUT_FILE_MISSING: '预期输出文件不存在',
  TASK_TIMEOUT: '任务执行超时（300 秒）',
  FILE_NOT_FOUND: '上传文件不存在',
  DATABASE_ERROR: '数据库写入失败',
  UPSTREAM_DEPENDENCY_FAILED: '上游依赖任务执行失败',
  UNKNOWN_ERROR: '未知错误',
};

// ===== 核心 Job 类型 =====

/** 完整的 AI 任务对象（前后端共用结构） */
export interface AIJob {
  id: number;
  project_id: number;
  task_type: AICapabilityType;
  task_name: string;
  status: AIJobStatus;
  progress: number;
  /** JSON 字符串 — 创建时的输入参数 */
  input_json: string;
  /** JSON 字符串 — 完成时的输出摘要 */
  output_json: string;
  error_code: AIJobErrorCode | '';
  error_message: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

/** 创建任务的请求 payload */
export interface AIJobCreateRequest {
  project_id: number;
  task_type: AICapabilityType;
  parameters?: Record<string, unknown>;
}

/** 轮询配置 */
export interface AIJobPollingConfig {
  /** 轮询间隔 (ms) */
  intervalMs: number;
  /** 最大轮询次数，超过后停止 */
  maxAttempts: number;
  /** 是否自动开始轮询 */
  autoStart: boolean;
}

export const DEFAULT_POLLING_CONFIG: AIJobPollingConfig = {
  intervalMs: 2000,
  maxAttempts: 600, // 20 分钟 (600 × 2s)
  autoStart: true,
};

/** Job Store 状态 */
export interface AIJobStoreState {
  jobs: AIJob[];
  loading: boolean;
  polling: boolean;
  pollingTimer: ReturnType<typeof setInterval> | null;
  error: string | null;
}
