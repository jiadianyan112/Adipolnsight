import { create } from 'zustand';
import api from '../services/apiClient';
import type { AnalysisTask } from '../types';
import { createPollingController, type PollingController } from '../hooks/pollingController';
import { isActiveRaw } from '../utils/jobStatus';
import { useToastStore } from './toastStore';

interface TaskState {
  tasks: AnalysisTask[];
  loading: boolean;
  polling: boolean;
  fetchTasks: (projectId: number, light?: boolean) => Promise<void>;
  createTask: (projectId: number, taskType: string, params?: any) => Promise<AnalysisTask>;
  rerunTask: (taskId: number) => Promise<void>;
  runFullPipeline: (projectId: number) => Promise<void>;
  startPolling: (projectId: number) => void;
  stopPolling: () => void;
}

/** Merge latest_only polling results into existing task array — preserves old tasks not in response */
function mergeTasks(existing: AnalysisTask[], incoming: AnalysisTask[]): AnalysisTask[] {
  const map = new Map(existing.map((t) => [t.id, t]));
  for (const t of incoming) {
    map.set(t.id, t);
  }
  return Array.from(map.values()).sort((a, b) =>
    new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );
}

export const useTaskStore = create<TaskState>((set, get) => {
  let controller: PollingController | null = null;
  let prevStatusMap: Record<number, string> = {};

  function detectTransitions(tasks: AnalysisTask[]) {
    const toast = useToastStore.getState();
    for (const t of tasks) {
      const prev = prevStatusMap[t.id];
      if (!prev || prev === t.status) continue;
      if (isActiveRaw(prev) && !isActiveRaw(t.status)) {
        if (t.status === 'success') {
          toast.notifyTask(t.id, t.task_type, 'succeeded');
        } else if (t.status === 'failed') {
          toast.notifyTask(t.id, t.task_type, 'failed');
        }
      }
      prevStatusMap[t.id] = t.status;
    }
  }

  function ensureController(projectId: number): PollingController {
    if (controller) return controller;

    controller = createPollingController({
      intervalMs: 2000,
      maxIntervalMs: 10_000,
      backoffFactor: 1.5,
      maxRetries: 300,
      immediate: true,
      visibilityAware: true,
      onTick: async () => {
        // Lightweight poll — only get latest per type
        await get().fetchTasks(projectId, true);
        const tasks = get().tasks;
        detectTransitions(tasks);
        const stillRunning = tasks.some((t) => isActiveRaw(t.status));
        return stillRunning;
      },
      onStop: () => {
        set({ polling: false });
      },
    });

    return controller;
  }

  return {
    tasks: [],
    loading: false,
    polling: false,

    fetchTasks: async (projectId: number, light = false) => {
      try {
        const params = light
          ? '?latest_only=true&page_size=7'
          : '?page_size=0'; // full list, backward compat
        const res = await api.get(`/projects/${projectId}/tasks${params}`);

        // Handle paginated response (items[]) or legacy response (tasks[])
        let taskList: AnalysisTask[];
        if (res.data.items) {
          taskList = res.data.items;
        } else if (res.data.tasks) {
          taskList = res.data.tasks;
        } else {
          return;
        }

        if (light) {
          // Merge into existing — preserves old tasks not returned by latest_only
          set((s) => ({ tasks: mergeTasks(s.tasks, taskList) }));
        } else {
          set({ tasks: taskList });
        }
      } catch (_) {}
    },

    createTask: async (projectId, taskType, params) => {
      const res = await api.post('/tasks', { project_id: projectId, task_type: taskType, parameters: params || {} });
      const toast = useToastStore.getState();
      toast.addToast({
        type: 'info',
        message: '分析任务已启动',
        description: `正在创建 ${taskType} 任务...`,
        duration: 2000,
      });
      get().fetchTasks(projectId);
      return res.data;
    },

    rerunTask: async (taskId) => {
      await api.post(`/tasks/${taskId}/rerun`);
      const toast = useToastStore.getState();
      toast.addToast({ type: 'info', message: '任务已重新提交', duration: 2000 });
    },

    runFullPipeline: async (projectId) => {
      const toast = useToastStore.getState();
      toast.addToast({
        type: 'info',
        message: '完整分析流水线已启动',
        description: '正在依次执行所有分析步骤...',
        duration: 3000,
      });
      await api.post(`/projects/${projectId}/pipeline/run-all`);
      prevStatusMap = {};
      get().startPolling(projectId);
    },

    startPolling: (projectId) => {
      if (controller) {
        controller.cancel();
        controller = null;
      }
      prevStatusMap = {};
      set({ polling: true });
      const ctrl = ensureController(projectId);
      ctrl.reset();
      ctrl.start();
    },

    stopPolling: () => {
      if (controller) {
        controller.cancel();
        controller = null;
      }
      set({ polling: false });
    },
  };
});
