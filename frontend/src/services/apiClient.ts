import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed';
    return Promise.reject(new Error(msg));
  },
);

/** AI 专用实例 — baseURL /api，用于 /api/ai/* 端点 */
export const aiApi = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

aiApi.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed';
    return Promise.reject(new Error(msg));
  },
);

export default api;
