/**
 * 流水线进度计算 — 纯函数
 *
 * 解决问题：同一 pipeline step 存在多个任务（如单独跑过一次 GWAS，
 * 又跑完整流水线创建第二个 GWAS）时，进度统计去重，避免出现 8/7、114% 等溢出。
 *
 * 去重策略（按 task_type 分组，每组只计一次）：
 *   1. 该组有 success  → 该步骤计为 completed（取最新完成的任务）
 *   2. 该组有 running   → 该步骤计为 running
 *   3. 该组有 failed    → 该步骤计为 failed
 *   4. 均无             → 该步骤计为 pending
 *
 * 不属于 PIPELINE_ORDER 的 task_type 不计入主流水线，但保留在 extraTasks 中供调试。
 */

import type { AnalysisTask } from '../types';
import {
  normalizeJobStatus,
  isSuccess,
  isFailed,
  isRunning,
  type NormalizedJobStatus,
} from './jobStatus';

export type StepStatus = NormalizedJobStatus;

export interface PipelineStepInfo {
  step: string;
  status: StepStatus;
  /** 该 step 的任务总数（含重复） */
  taskCount: number;
  /** 代表任务的 ID（用于查看结果），无任务时为 null */
  representativeTaskId: number | null;
}

export interface PipelineProgress {
  completed: number;
  running: number;
  failed: number;
  pending: number;
  total: number;
  /** 0–100，安全上限 */
  percent: number;
  /** PIPELINE_ORDER 中每一步的详细信息 */
  steps: PipelineStepInfo[];
  /** 不属于 PIPELINE_ORDER 的任务数 */
  extraTaskCount: number;
}

/** 任务终态优先级：succeeded > running > failed > cancelled > queued > unknown */
const STATUS_PRIORITY: Record<NormalizedJobStatus, number> = {
  succeeded: 5,
  running: 4,
  failed: 3,
  cancelled: 2,
  queued: 1,
  unknown: 0,
};

/**
 * 将 task_type 映射到 PIPELINE_ORDER 中的标准步骤名。
 * 覆盖新旧 API 可能产生的字段差异。
 */
export function normalizeTaskStep(task: AnalysisTask): string {
  // AnalysisTask.task_type 与 PIPELINE_ORDER 对齐
  // 两者均使用 snake_case，如 'gwas_analysis'、'mediation_mr'
  if (task.task_type && typeof task.task_type === 'string') {
    return task.task_type.trim();
  }
  // 兜底：不可识别的任务类型
  return '_unknown_';
}

/**
 * 核心函数：从原始任务列表计算去重后的流水线进度。
 *
 * @param tasks        项目下的全部 AnalysisTask 列表
 * @param pipelineOrder 标准流水线步骤数组（如 PIPELINE_ORDER）
 * @returns PipelineProgress — 去重且安全的进度对象
 */
export function computePipelineProgress(
  tasks: AnalysisTask[],
  pipelineOrder: string[],
): PipelineProgress {
  const total = pipelineOrder.length;

  // 1. 按 normalizeTaskStep 分组
  const groups = new Map<string, AnalysisTask[]>();
  for (const t of tasks) {
    const step = normalizeTaskStep(t);
    const bucket = groups.get(step);
    if (bucket) {
      bucket.push(t);
    } else {
      groups.set(step, [t]);
    }
  }

  // 2. 每组选出代表任务
  const bestPerStep = new Map<string, { status: StepStatus; taskId: number }>();
  for (const [step, group] of groups) {
    // 排序：状态优先级 → finished_at 倒序
    const sorted = [...group].sort((a, b) => {
      const pa = STATUS_PRIORITY[normalizeJobStatus(a.status)] ?? 0;
      const pb = STATUS_PRIORITY[normalizeJobStatus(b.status)] ?? 0;
      if (pa !== pb) return pb - pa;
      // 同状态按完成时间倒序（最新的在前）
      const af = a.finished_at ?? '';
      const bf = b.finished_at ?? '';
      return bf.localeCompare(af);
    });
    const best = sorted[0];
    const bestStatus = normalizeJobStatus(best.status);
    bestPerStep.set(step, {
      status: bestStatus,
      taskId: best.id,
    });
  }

  // 3. 遍历 PIPELINE_ORDER 统计
  let completed = 0;
  let running = 0;
  let failed = 0;
  let pending = 0;
  const steps: PipelineStepInfo[] = [];

  for (const step of pipelineOrder) {
    const group = groups.get(step);
    const taskCount = group ? group.length : 0;
    const best = bestPerStep.get(step);

    let status: NormalizedJobStatus = 'queued';
    if (best) {
      const s = best.status;
      if (isSuccess(s)) {
        completed++;
        status = 'succeeded';
      } else if (isRunning(s)) {
        running++;
        status = 'running';
      } else if (isFailed(s)) {
        failed++;
        status = 'failed';
      } else {
        pending++;
        status = s;
      }
    } else {
      pending++;
    }

    steps.push({
      step,
      status,
      taskCount,
      representativeTaskId: best?.taskId ?? null,
    });
  }

  // 4. 外部任务计数（不在 PIPELINE_ORDER 中的 task_type）
  let extraTaskCount = 0;
  for (const [step, group] of groups) {
    if (!pipelineOrder.includes(step) && step !== '_unknown_') {
      extraTaskCount += group.length;
    }
  }
  // 也计入 _unknown_ 类型
  const unknownGroup = groups.get('_unknown_');
  if (unknownGroup) extraTaskCount += unknownGroup.length;

  // 5. 安全约束
  const safeCompleted = Math.min(completed, total);
  const percent = total > 0 ? Math.min(100, Math.round((safeCompleted / total) * 100)) : 0;

  return {
    completed: safeCompleted,
    running,
    failed,
    pending,
    total,
    percent,
    steps,
    extraTaskCount,
  };
}
