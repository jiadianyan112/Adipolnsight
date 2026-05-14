import { create } from 'zustand';
import api from '../services/apiClient';
import type { AnalysisResult, Report } from '../types';

interface ResultState {
  currentResult: AnalysisResult | null;
  currentReport: Report | null;
  loading: boolean;
  fetchResult: (taskId: number) => Promise<void>;
  fetchReport: (reportId: number) => Promise<void>;
  generateReport: (projectId: number) => Promise<Report>;
}

export const useResultStore = create<ResultState>((set) => ({
  currentResult: null,
  currentReport: null,
  loading: false,

  fetchResult: async (taskId) => {
    set({ loading: true });
    try {
      const res = await api.get(`/tasks/${taskId}/result`);
      set({ currentResult: res.data, loading: false });
    } catch (_) {
      set({ loading: false });
    }
  },

  fetchReport: async (reportId) => {
    set({ loading: true });
    try {
      const res = await api.get(`/reports/${reportId}`);
      set({ currentReport: res.data, loading: false });
    } catch (_) {
      set({ loading: false });
    }
  },

  generateReport: async (projectId) => {
    const res = await api.post(`/projects/${projectId}/reports/generate`);
    set({ currentReport: res.data });
    return res.data;
  },
}));
