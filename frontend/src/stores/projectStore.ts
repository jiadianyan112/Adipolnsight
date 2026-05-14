import { create } from 'zustand';
import api from '../services/apiClient';
import type { Project } from '../types';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  fetchProject: (id: number) => Promise<void>;
  createProject: (data: any) => Promise<Project>;
  deleteProject: (id: number) => Promise<void>;
  createDemo: () => Promise<Project>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const res = await api.get('/projects');
      set({ projects: res.data.projects, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  fetchProject: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const res = await api.get(`/projects/${id}`);
      set({ currentProject: res.data, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  createProject: async (data) => {
    const res = await api.post('/projects', data);
    get().fetchProjects();
    return res.data;
  },

  deleteProject: async (id) => {
    await api.delete(`/projects/${id}`);
    get().fetchProjects();
  },

  createDemo: async () => {
    const res = await api.post('/demo/seed');
    get().fetchProjects();
    return res.data;
  },
}));
