import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  description?: string;
  duration?: number;
  createdAt: number;
}

interface ToastState {
  toasts: Toast[];
  notifiedKeys: Set<string>;
  addToast: (t: Omit<Toast, 'id' | 'createdAt'> & { dedupKey?: string }) => void;
  removeToast: (id: string) => void;
  /** 带去重的任务通知 — 同一 taskId 终态只通知一次 */
  notifyTask: (taskId: number | string, taskType: string, status: 'succeeded' | 'failed') => void;
  clearAll: () => void;
}

let seq = 0;
function nextId() { return `toast-${Date.now()}-${++seq}`; }

const TYPE_ICONS: Record<ToastType, string> = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

const TASK_LABELS: Record<string, string> = {
  image_segmentation: '影像分割',
  gwas_analysis: 'GWAS 全基因组关联',
  opengwas_fetch: 'OpenGWAS 数据获取',
  mendelian_randomization: '孟德尔随机化',
  mediation_mr: '中介孟德尔随机化',
  risk_modeling: '风险建模',
  report_generation: '科研报告生成',
};

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  notifiedKeys: new Set<string>(),

  addToast: (input) => {
    const id = nextId();
    const dedupKey = input.dedupKey;

    set((s) => {
      // Replace existing toast with same dedupKey
      let toasts = s.toasts;
      if (dedupKey) {
        toasts = toasts.filter((t) => (t as any).__dedupKey !== dedupKey);
      }
      // Cap at 5 visible
      if (toasts.length >= 5) {
        toasts = toasts.slice(toasts.length - 4);
      }
      return {
        toasts: [...toasts, {
          id,
          type: input.type,
          message: input.message,
          description: input.description,
          duration: input.duration ?? 4000,
          createdAt: Date.now(),
          __dedupKey: dedupKey,
        } as Toast & { __dedupKey?: string }],
      } as any;
    });

    // Auto-dismiss
    const duration = input.duration ?? 4000;
    if (duration > 0) {
      setTimeout(() => get().removeToast(id), duration);
    }
  },

  removeToast: (id) => {
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
  },

  notifyTask: (taskId, taskType, status) => {
    const key = `task:${taskId}:${status}`;
    const { notifiedKeys } = get();
    if (notifiedKeys.has(key)) return;

    const label = TASK_LABELS[taskType] || taskType;
    const isSuccess = status === 'succeeded';

    set((s) => {
      const next = new Set(s.notifiedKeys);
      next.add(key);
      return { notifiedKeys: next };
    });

    get().addToast({
      type: isSuccess ? 'success' : 'error',
      message: isSuccess ? `${label} 分析完成` : `${label} 分析失败`,
      description: isSuccess ? '结果已生成，可查看详细数据' : '请检查错误日志并重试',
      dedupKey: key,
      duration: isSuccess ? 5000 : 0, // errors persist until dismissed
    });
  },

  clearAll: () => set({ toasts: [] }),
}));

export { TYPE_ICONS };
