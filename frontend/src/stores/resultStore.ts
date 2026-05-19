import { create } from 'zustand';
import api, { aiApi } from '../services/apiClient';
import type { AnalysisResult, Report } from '../types';

/** 统一报告生成返回结构 */
export interface ReportGenerationResult {
  report_id?: number;
  project_id: number;
  job_id: string;
  status: string;
  message?: string;
}

interface ResultState {
  currentResult: AnalysisResult | null;
  currentReport: Report | null;
  loading: boolean;
  fetchResult: (taskId: number) => Promise<void>;
  fetchReport: (reportId: number) => Promise<void>;
  /** 统一报告生成入口 — 通过 JobManager 创建 report_generation Job */
  generateReport: (projectId: number) => Promise<ReportGenerationResult>;
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
    // 使用统一的 JobManager 路径
    const res = await aiApi.post('/ai/report/jobs', {
      project_id: projectId,
      parameters: {
        report_type: 'full',
        language: 'zh-CN',
        include_figures: true,
        include_tables: true,
        include_ai_interpretation: true,
      },
    });

    const data = res.data;
    if (!data.success) {
      throw new Error(data.error?.message || '创建报告任务失败');
    }

    return {
      project_id: projectId,
      job_id: data.data.job_id,
      status: data.data.status || 'queued',
      message: data.data.message || '报告生成任务已提交',
    };
  },
}));
