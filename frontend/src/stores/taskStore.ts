import { create } from 'zustand';
import api from '../services/apiClient';
import type { AnalysisTask } from '../types';

interface TaskState {
  tasks: AnalysisTask[];
  loading: boolean;
  polling: boolean;
  fetchTasks: (projectId: number) => Promise<void>;
  createTask: (projectId: number, taskType: string, params?: any) => Promise<AnalysisTask>;
  rerunTask: (taskId: number) => Promise<void>;
  runFullPipeline: (projectId: number) => Promise<void>;
  startPolling: (projectId: number) => void;
  stopPolling: () => void;
}

export const useTaskStore = create<TaskState>((set, get) => {
  let timer: ReturnType<typeof setInterval> | null = null;

  return {
    tasks: [],
    loading: false,
    polling: false,

    fetchTasks: async (projectId: number) => {
      try {
        const res = await api.get(`/projects/${projectId}/tasks`);
        set({ tasks: res.data.tasks });
      } catch (_) {}
    },

    createTask: async (projectId, taskType, params) => {
      const res = await api.post('/tasks', { project_id: projectId, task_type: taskType, parameters: params || {} });
      get().fetchTasks(projectId);
      return res.data;
    },

    rerunTask: async (taskId) => {
      await api.post(`/tasks/${taskId}/rerun`);
    },

    runFullPipeline: async (projectId) => {
      await api.post(`/projects/${projectId}/pipeline/run-all`);
      get().startPolling(projectId);
    },

    startPolling: (projectId) => {
      if (timer) clearInterval(timer);
      set({ polling: true });
      timer = setInterval(async () => {
        const { tasks } = get();
        const hasRunning = tasks.some((t) => t.status === 'running' || t.status === 'pending');
        await get().fetchTasks(projectId);
        const updated = get().tasks;
        const stillRunning = updated.some((t) => t.status === 'running' || t.status === 'pending');
        if (hasRunning && !stillRunning) {
          get().stopPolling();
        }
      }, 2000);
    },

    stopPolling: () => {
      if (timer) { clearInterval(timer); timer = null; }
      set({ polling: false });
    },
  };
});
