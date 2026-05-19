/**
 * AdipoInsight AI API Client
 *
 * 统一的 AI 能力请求封装。所有方法：
 * - 使用已有的 apiClient 实例（baseURL /api/v1，30s timeout）
 * - 返回带类型判别的结果对象（success / error）
 * - loading 由调用方（Store / Component）控制
 * - 页面组件禁止直接 import 此文件，应通过 Store 调用
 */

import api, { aiApi } from './apiClient';
import type {
  AIJob,
  AIJobCreateRequest,
  AIJobErrorCode,
  UploadedFile,
  FileType,
  SegmentationResult,
  PhenotypeQuantificationResult,
  GWASAnalysisRequest,
  GWASAnalysisResult,
  MRAnalysisRequest,
  MRAnalysisResult,
  MediationMRRequest,
  MediationMRResult,
  RiskModelingRequest,
  RiskModelingResult,
  ReportGenerationRequest,
  ReportGenerationResult,
} from '../types';

// ===== 统一返回类型 =====

/** API 调用成功 */
export interface AIServiceOk<T> {
  ok: true;
  data: T;
}

/** API 调用失败 */
export interface AIServiceErr {
  ok: false;
  /** 后端 error_code（如 SCRIPT_NOT_FOUND） */
  errorCode: AIJobErrorCode | 'NETWORK_ERROR' | 'EMPTY_RESPONSE' | 'UNKNOWN';
  /** 人类可读错误消息 */
  message: string;
  /** HTTP 状态码（如有） */
  statusCode: number | null;
}

export type AIServiceResult<T> = AIServiceOk<T> | AIServiceErr;

// ===== 内部辅助 =====

/** 后端列表响应通用 wrapper */
interface ListResponse<T> {
  [key: string]: T[] | number;
}

function unwrapList<T>(res: unknown, key: string): T[] {
  if (res && typeof res === 'object' && key in (res as Record<string, unknown>)) {
    return (res as Record<string, unknown>)[key] as T[];
  }
  return [];
}

function makeErr(
  errorCode: AIJobErrorCode | 'NETWORK_ERROR' | 'EMPTY_RESPONSE' | 'UNKNOWN',
  message: string,
  statusCode: number | null = null,
): AIServiceErr {
  return { ok: false, errorCode, message, statusCode };
}

/**
 * 包装 API 调用，统一处理所有异常。
 * 调用方只需检查 result.ok 判别成功/失败。
 */
async function withErrorBoundary<T>(
  fn: () => Promise<T>,
  emptyMessage = '后端返回空响应',
): Promise<AIServiceResult<T>> {
  try {
    const data = await fn();
    if (data === null || data === undefined) {
      return makeErr('EMPTY_RESPONSE', emptyMessage);
    }
    return { ok: true, data };
  } catch (e: unknown) {
    if (e instanceof Error) {
      // Axios 拦截器已将后端 detail 注入 Error.message
      return makeErr('UNKNOWN', e.message);
    }
    if (typeof e === 'object' && e !== null && 'response' in e) {
      const axiosErr = e as { response?: { status?: number; data?: { detail?: string; error_code?: string } }; message?: string };
      const statusCode = axiosErr.response?.status ?? null;
      const detail = axiosErr.response?.data?.detail ?? axiosErr.message ?? '未知网络错误';
      const code = axiosErr.response?.data?.error_code as AIJobErrorCode | undefined;
      return makeErr(code ?? 'UNKNOWN', detail, statusCode);
    }
    if (typeof e === 'object' && e !== null && 'code' in e) {
      // Network error (ERR_NETWORK, ECONNABORTED, etc.)
      const netErr = e as { code?: string; message?: string };
      return makeErr('NETWORK_ERROR', netErr.message ?? '网络连接失败', null);
    }
    return makeErr('UNKNOWN', String(e));
  }
}

// ===== 文件上传 =====

/**
 * 上传医学影像文件（MRI NIfTI / DICOM）
 *
 * POST /api/v1/projects/{projectId}/files
 * Content-Type: multipart/form-data
 */
export async function uploadMedicalImage(
  projectId: number,
  file: File,
  onProgress?: (pct: number) => void,
): Promise<AIServiceResult<UploadedFile>> {
  const form = new FormData();
  form.append('file', file);
  form.append('file_type', 'mri');

  return withErrorBoundary(async () => {
    const res = await api.post<UploadedFile>(
      `/projects/${projectId}/files`,
      form,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (evt) => {
          if (evt.total && onProgress) {
            onProgress(Math.round((evt.loaded / evt.total) * 100));
          }
        },
      },
    );
    return res.data;
  }, '文件上传返回空响应');
}

/**
 * 上传通用文件（表型/协变量/基因型）
 *
 * POST /api/v1/projects/{projectId}/files
 */
export async function uploadFile(
  projectId: number,
  file: File,
  fileType: FileType,
  onProgress?: (pct: number) => void,
): Promise<AIServiceResult<UploadedFile>> {
  const form = new FormData();
  form.append('file', file);
  form.append('file_type', fileType);

  return withErrorBoundary(async () => {
    const res = await api.post<UploadedFile>(
      `/projects/${projectId}/files`,
      form,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (evt) => {
          if (evt.total && onProgress) {
            onProgress(Math.round((evt.loaded / evt.total) * 100));
          }
        },
      },
    );
    return res.data;
  }, '文件上传返回空响应');
}

/**
 * 获取项目文件列表
 *
 * GET /api/v1/projects/{projectId}/files
 */
export async function listProjectFiles(
  projectId: number,
): Promise<AIServiceResult<UploadedFile[]>> {
  return withErrorBoundary(async () => {
    const res = await api.get<ListResponse<UploadedFile>>(`/projects/${projectId}/files`);
    return unwrapList<UploadedFile>(res.data, 'files');
  }, '文件列表为空');
}

/**
 * 获取文件下载 URL
 *
 * GET /api/v1/files/{fileId}/download
 */
export function getFileDownloadUrl(fileId: number): string {
  return `/api/v1/files/${fileId}/download`;
}

// ===== Job 创建（7 个 AI 能力） =====

/**
 * 创建影像分割任务 — C1
 *
 * POST /api/v1/tasks
 * task_type = "image_segmentation"
 */
export async function createSegmentationJob(
  projectId: number,
  fileId: number,
): Promise<AIServiceResult<AIJob>> {
  const payload: AIJobCreateRequest = {
    project_id: projectId,
    task_type: 'image_segmentation',
    parameters: { file_id: fileId },
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, '影像分割任务创建返回空响应');
}

/**
 * 创建表型量化任务 — C2
 *
 * POST /api/v1/tasks
 * task_type = "phenotype_quantification"
 */
export async function createPhenotypeJob(
  projectId: number,
): Promise<AIServiceResult<AIJob>> {
  const payload: AIJobCreateRequest = {
    project_id: projectId,
    task_type: 'phenotype_quantification',
    parameters: {},
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, '表型量化任务创建返回空响应');
}

/**
 * 创建 GWAS 分析任务 — C3
 *
 * POST /api/v1/tasks
 * task_type = "gwas_analysis"
 */
export async function createGWASJob(
  params: GWASAnalysisRequest,
): Promise<AIServiceResult<AIJob>> {
  const { project_id, ...rest } = params;
  const payload: AIJobCreateRequest = {
    project_id,
    task_type: 'gwas_analysis',
    parameters: rest as unknown as Record<string, unknown>,
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, 'GWAS 分析任务创建返回空响应');
}

/**
 * 创建双样本 MR 分析任务 — C4
 *
 * POST /api/v1/tasks
 * task_type = "mendelian_randomization"
 */
export async function createMRJob(
  params: MRAnalysisRequest,
): Promise<AIServiceResult<AIJob>> {
  const { project_id, ...rest } = params;
  const payload: AIJobCreateRequest = {
    project_id,
    task_type: 'mendelian_randomization',
    parameters: rest as unknown as Record<string, unknown>,
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, 'MR 分析任务创建返回空响应');
}

/**
 * 创建中介 MR 分析任务 — C5
 *
 * POST /api/v1/tasks
 * task_type = "mediation_mr"
 */
export async function createMediationMRJob(
  params: MediationMRRequest,
): Promise<AIServiceResult<AIJob>> {
  const { project_id, ...rest } = params;
  const payload: AIJobCreateRequest = {
    project_id,
    task_type: 'mediation_mr',
    parameters: rest as unknown as Record<string, unknown>,
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, '中介 MR 分析任务创建返回空响应');
}

/**
 * 创建风险建模任务 — C6
 *
 * POST /api/v1/tasks
 * task_type = "risk_modeling"
 */
export async function createRiskModelingJob(
  params: RiskModelingRequest,
): Promise<AIServiceResult<AIJob>> {
  const { project_id, ...rest } = params;
  const payload: AIJobCreateRequest = {
    project_id,
    task_type: 'risk_modeling',
    parameters: rest as unknown as Record<string, unknown>,
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, '风险建模任务创建返回空响应');
}

/**
 * 创建报告生成任务 — C7
 *
 * POST /api/v1/tasks
 * task_type = "report_generation"
 */
export async function createReportJob(
  params: ReportGenerationRequest,
): Promise<AIServiceResult<AIJob>> {
  const { project_id, ...rest } = params;
  const payload: AIJobCreateRequest = {
    project_id,
    task_type: 'report_generation',
    parameters: rest as unknown as Record<string, unknown>,
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, '报告生成任务创建返回空响应');
}

/** 报告任务参数 */
export interface ReportJobParams {
  report_type?: string;
  language?: string;
  project_title?: string;
  selected_job_ids?: string[];
  include_figures?: boolean;
  include_tables?: boolean;
  include_ai_interpretation?: boolean;
}

/**
 * 创建 AI 报告生成任务
 *
 * POST /api/ai/report/jobs
 */
export async function createAIReportJob(
  projectId: number,
  params: ReportJobParams,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return createAIJob(projectId, 'report', {
    project_title: params.project_title || '',
    report_type: params.report_type || 'full',
    language: params.language || 'zh-CN',
    selected_jobs: params.selected_job_ids || [],
    include_figures: params.include_figures ?? true,
    include_tables: params.include_tables ?? true,
    include_ai_interpretation: params.include_ai_interpretation ?? true,
  } as Record<string, unknown>);
}

// ===== 通用 Job 操作 =====

/**
 * 创建自定义 AI 任务（通用入口）
 *
 * POST /api/v1/tasks
 */
export async function createJob(
  projectId: number,
  taskType: AIJob['task_type'],
  parameters: Record<string, unknown> = {},
): Promise<AIServiceResult<AIJob>> {
  const payload: AIJobCreateRequest = {
    project_id: projectId,
    task_type: taskType,
    parameters,
  };
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>('/tasks', payload);
    return res.data;
  }, '任务创建返回空响应');
}

/**
 * 查询任务状态
 *
 * GET /api/v1/tasks/{jobId}
 */
export async function getJobStatus(
  jobId: number,
): Promise<AIServiceResult<AIJob>> {
  return withErrorBoundary(async () => {
    const res = await api.get<AIJob>(`/tasks/${jobId}`);
    return res.data;
  }, `任务 ${jobId} 不存在或查询失败`);
}

/**
 * 查询项目下所有任务
 *
 * GET /api/v1/projects/{projectId}/tasks
 */
export async function listProjectJobs(
  projectId: number,
): Promise<AIServiceResult<AIJob[]>> {
  return withErrorBoundary(async () => {
    const res = await api.get<ListResponse<AIJob>>(`/projects/${projectId}/tasks`);
    return unwrapList<AIJob>(res.data, 'tasks');
  }, '任务列表为空');
}

/**
 * 重跑任务
 *
 * POST /api/v1/tasks/{jobId}/rerun
 */
export async function rerunJob(
  jobId: number,
): Promise<AIServiceResult<AIJob>> {
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>(`/tasks/${jobId}/rerun`);
    return res.data;
  }, '任务重跑返回空响应');
}

/**
 * 运行完整分析流程
 *
 * POST /api/v1/projects/{projectId}/pipeline/run-all
 */
export async function runFullPipeline(
  projectId: number,
): Promise<AIServiceResult<AIJob[]>> {
  return withErrorBoundary(async () => {
    const res = await api.post<ListResponse<AIJob>>(
      `/projects/${projectId}/pipeline/run-all`,
    );
    return unwrapList<AIJob>(res.data, 'tasks');
  }, '流程运行返回空响应');
}

/**
 * 取消任务（后端预留接口）
 *
 * POST /api/v1/tasks/{jobId}/cancel
 *
 * 当前后端未实现，返回约定错误码。
 */
export async function cancelJob(
  jobId: number,
): Promise<AIServiceResult<AIJob>> {
  return withErrorBoundary(async () => {
    const res = await api.post<AIJob>(`/tasks/${jobId}/cancel`);
    return res.data;
  }, `任务 ${jobId} 取消失败`);
}

// ===== 结果查询 =====

/**
 * 获取任务结果
 *
 * GET /api/v1/tasks/{jobId}/result
 */
export async function getJobResult(
  jobId: number,
): Promise<AIServiceResult<{ summary_json: string; output_files_json: string; result_type: string }>> {
  return withErrorBoundary(async () => {
    const res = await api.get<{ summary_json: string; output_files_json: string; result_type: string }>(
      `/tasks/${jobId}/result`,
    );
    return res.data;
  }, `任务 ${jobId} 结果不存在`);
}

/**
 * 获取影像分割结果（已解析）
 *
 * GET /api/v1/tasks/{jobId}/result → 解析 summary_json
 */
export async function getSegmentationResult(
  jobId: number,
): Promise<AIServiceResult<SegmentationResult>> {
  const result = await getJobResult(jobId);
  if (!result.ok) return result;
  try {
    const parsed: SegmentationResult = JSON.parse(result.data.summary_json);
    return { ok: true, data: parsed };
  } catch {
    return makeErr('OUTPUT_JSON_INVALID', '分割结果 JSON 解析失败');
  }
}

/**
 * 获取表型量化结果（已解析）
 *
 * GET /api/v1/tasks/{jobId}/result → 解析 summary_json
 */
export async function getPhenotypeResult(
  jobId: number,
): Promise<AIServiceResult<PhenotypeQuantificationResult>> {
  const result = await getJobResult(jobId);
  if (!result.ok) return result;
  try {
    const parsed: PhenotypeQuantificationResult = JSON.parse(result.data.summary_json);
    return { ok: true, data: parsed };
  } catch {
    return makeErr('OUTPUT_JSON_INVALID', '表型结果 JSON 解析失败');
  }
}

/**
 * 获取 GWAS 分析结果（已解析）
 *
 * GET /api/v1/tasks/{jobId}/result → 解析 summary_json
 */
export async function getGWASResult(
  jobId: number,
): Promise<AIServiceResult<GWASAnalysisResult>> {
  const result = await getJobResult(jobId);
  if (!result.ok) return result;
  try {
    const parsed: GWASAnalysisResult = JSON.parse(result.data.summary_json);
    return { ok: true, data: parsed };
  } catch {
    return makeErr('OUTPUT_JSON_INVALID', 'GWAS 结果 JSON 解析失败');
  }
}

/**
 * 获取 MR 分析结果（已解析）
 *
 * GET /api/v1/tasks/{jobId}/result → 解析 summary_json
 */
export async function getMRResult(
  jobId: number,
): Promise<AIServiceResult<MRAnalysisResult>> {
  const result = await getJobResult(jobId);
  if (!result.ok) return result;
  try {
    const parsed: MRAnalysisResult = JSON.parse(result.data.summary_json);
    return { ok: true, data: parsed };
  } catch {
    return makeErr('OUTPUT_JSON_INVALID', 'MR 结果 JSON 解析失败');
  }
}

/**
 * 获取中介 MR 结果（已解析）
 *
 * GET /api/v1/tasks/{jobId}/result → 解析 summary_json
 */
export async function getMediationMRResult(
  jobId: number,
): Promise<AIServiceResult<MediationMRResult>> {
  const result = await getJobResult(jobId);
  if (!result.ok) return result;
  try {
    const parsed: MediationMRResult = JSON.parse(result.data.summary_json);
    return { ok: true, data: parsed };
  } catch {
    return makeErr('OUTPUT_JSON_INVALID', '中介 MR 结果 JSON 解析失败');
  }
}

/**
 * 获取风险建模结果（已解析）
 *
 * GET /api/v1/tasks/{jobId}/result → 解析 summary_json
 */
export async function getRiskModelingResult(
  jobId: number,
): Promise<AIServiceResult<RiskModelingResult>> {
  const result = await getJobResult(jobId);
  if (!result.ok) return result;
  try {
    const parsed: RiskModelingResult = JSON.parse(result.data.summary_json);
    return { ok: true, data: parsed };
  } catch {
    return makeErr('OUTPUT_JSON_INVALID', '风险建模结果 JSON 解析失败');
  }
}

/**
 * 获取报告生成结果（已解析）
 *
 * GET /api/v1/tasks/{jobId}/result → 解析 summary_json
 */
export async function getReportResult(
  jobId: number,
): Promise<AIServiceResult<ReportGenerationResult>> {
  const result = await getJobResult(jobId);
  if (!result.ok) return result;
  try {
    const parsed: ReportGenerationResult = JSON.parse(result.data.summary_json);
    return { ok: true, data: parsed };
  } catch {
    return makeErr('OUTPUT_JSON_INVALID', '报告结果 JSON 解析失败');
  }
}

// ===== 新 AI API 接口 (/api/ai/*) =====

/** 新 AI API 通用 response envelope */
interface AIApiEnvelope<T> {
  success: boolean;
  data: T;
  error: { code: string; message: string; details?: Record<string, unknown> } | null;
  request_id: string;
}

/** 新 AI API 返回的 Job 对象 */
export interface AIJobFromAPI {
  job_id: string;
  capability_type: string;
  status: string;
  progress: number;
  progress_stage: string;
  input: Record<string, unknown>;
  result: Record<string, unknown> | null;
  output_files: string[];
  error_code: string;
  error_message: string;
  user_facing_error?: {
    user_message: string;
    possible_reasons: string[];
    next_actions: string[];
    technical_summary: string;
  } | null;
  created_at: string;
  started_at: string;
  finished_at: string;
  updated_at: string;
  project_id: number;
}

/** 分割请求参数 */
export interface SegmentationJobParams {
  file_id: number;
  modality?: string;
  target_structures?: string[];
  model_name?: string;
  mode?: string;
}

/**
 * 创建 AI 分割任务（新 /api/ai 接口）
 *
 * POST /api/ai/segmentation/jobs
 */
export async function createAISegmentationJob(
  projectId: number,
  params: SegmentationJobParams,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return withErrorBoundary(async () => {
    const res = await aiApi.post<AIApiEnvelope<AIJobFromAPI>>('/ai/segmentation/jobs', {
      project_id: projectId,
      parameters: {
        file_id: params.file_id,
        modality: params.modality || 'MRI',
        target_structures: params.target_structures || ['liver', 'visceral_fat', 'subcutaneous_fat', 'bone_marrow'],
        model_name: params.model_name || 'TSSA-UNet',
        mode: params.mode || 'mock',
      },
    });
    if (!res.data.success) {
      throw new Error(res.data.error?.message || '创建分割任务失败');
    }
    return res.data.data;
  }, 'AI 分割任务创建返回空响应');
}

/**
 * 查询 AI Job 状态（新 /api/ai 接口）
 *
 * GET /api/ai/jobs/{jobId}
 */
export async function getAIJobStatus(
  jobId: string,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return withErrorBoundary(async () => {
    const res = await aiApi.get<AIApiEnvelope<AIJobFromAPI>>(`/ai/jobs/${jobId}`);
    if (!res.data.success) {
      throw new Error(res.data.error?.message || '查询任务状态失败');
    }
    return res.data.data;
  }, `任务 ${jobId} 不存在或查询失败`);
}

/**
 * 获取 AI Job 结果（新 /api/ai 接口）
 *
 * GET /api/ai/jobs/{jobId}/result
 */
export async function getAIJobResult(
  jobId: string,
): Promise<AIServiceResult<{ result: Record<string, unknown>; output_files: string[]; capability_type: string }>> {
  return withErrorBoundary(async () => {
    const res = await aiApi.get<AIApiEnvelope<{
      result: Record<string, unknown>;
      output_files: string[];
      capability_type: string;
    }>>(`/ai/jobs/${jobId}/result`);
    if (!res.data.success) {
      throw new Error(res.data.error?.message || '获取结果失败');
    }
    return res.data.data;
  }, `任务 ${jobId} 结果不存在`);
}

/**
 * 取消 AI Job（新 /api/ai 接口）
 *
 * POST /api/ai/jobs/{jobId}/cancel
 */
export async function cancelAIJob(
  jobId: string,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return withErrorBoundary(async () => {
    const res = await aiApi.post<AIApiEnvelope<AIJobFromAPI>>(`/ai/jobs/${jobId}/cancel`);
    if (!res.data.success) {
      throw new Error(res.data.error?.message || '取消任务失败');
    }
    return res.data.data;
  }, `取消任务 ${jobId} 失败`);
}

// ===== 通用 AI Job 创建 =====

/** GWAS 任务参数 */
export interface GWASJobParams {
  phenotype_id?: string;
  phenotype_name: string;
  covariates?: string[];
  population_filter?: string;
  method?: string;
  maf_threshold?: number;
  hwe_threshold?: number;
  qc_options?: Record<string, boolean>;
}

/** 通用 AI 任务参数（所有 capability 共用） */
export type AIJobParams =
  | { capability: 'segmentation'; params: SegmentationJobParams }
  | { capability: 'phenotype'; params: Record<string, unknown> }
  | { capability: 'gwas'; params: GWASJobParams }
  | { capability: 'mr'; params: Record<string, unknown> }
  | { capability: 'mediation-mr'; params: Record<string, unknown> }
  | { capability: 'risk-modeling'; params: Record<string, unknown> }
  | { capability: 'report'; params: Record<string, unknown> };

/**
 * 创建 AI 任务（通用入口，自动映射 capability → URL path）
 *
 * POST /api/ai/{capability}/jobs
 */
export async function createAIJob(
  projectId: number,
  capability: string,
  params: Record<string, unknown>,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return withErrorBoundary(async () => {
    const res = await aiApi.post<AIApiEnvelope<AIJobFromAPI>>(`/ai/${capability}/jobs`, {
      project_id: projectId,
      parameters: params,
    });
    if (!res.data.success) {
      throw new Error(res.data.error?.message || '创建任务失败');
    }
    return res.data.data;
  }, `${capability} 任务创建返回空响应`);
}

/**
 * 创建 GWAS 分析任务
 *
 * POST /api/ai/gwas/jobs
 */
export async function createAIGWASJob(
  projectId: number,
  params: GWASJobParams,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return createAIJob(projectId, 'gwas', {
    phenotype_id: params.phenotype_id || '',
    phenotype_name: params.phenotype_name,
    phenotype: params.phenotype_name,
    covariates: params.covariates || ['age', 'sex', 'bmi'],
    population_filter: params.population_filter || 'EUR',
    method: params.method || 'REGENIE',
    maf_threshold: params.maf_threshold ?? 0.01,
    hwe_threshold: params.hwe_threshold ?? 1e-6,
    qc_options: params.qc_options || { impute_missing: true, remove_outliers: true, normalize_phenotype: true },
  } as Record<string, unknown>);
}

/** Mediation MR 任务参数 */
export interface MediationMRJobParams {
  exposure_trait: string;
  outcome_trait: string;
  mediator_source?: string;
  candidate_proteins?: string[];
  total_effect?: number;
  correction_method?: string;
  alpha?: number;
}

/**
 * 创建中介 MR 分析任务
 *
 * POST /api/ai/mediation-mr/jobs
 */
export async function createAIMediationMRJob(
  projectId: number,
  params: MediationMRJobParams,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return createAIJob(projectId, 'mediation-mr', {
    exposure_trait: params.exposure_trait,
    exposure: params.exposure_trait,
    outcome_trait: params.outcome_trait,
    outcome: params.outcome_trait,
    mediator_source: params.mediator_source || 'decode_plasma',
    candidate_proteins: params.candidate_proteins || ['ACY1', 'H6PD', 'SHBG', 'ADH1A', 'POR', 'NAAA'],
    total_effect: params.total_effect ?? 0.44,
    correction_method: params.correction_method || 'fdr',
    alpha: params.alpha ?? 0.05,
  } as Record<string, unknown>);
}

/** Risk Modeling 任务参数 */
export interface RiskModelingJobParams {
  exposure: string;
  outcomes?: string[];
  model_types?: string[];
  covariate_model?: string[];
  grouping?: string;
  quartile_groups?: number[];
}

/**
 * 创建风险建模任务
 *
 * POST /api/ai/risk-modeling/jobs
 */
export async function createAIRiskModelingJob(
  projectId: number,
  params: RiskModelingJobParams,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return createAIJob(projectId, 'risk-modeling', {
    exposure: params.exposure,
    outcome: params.outcomes?.[0] || 'Osteoporosis',
    outcomes: params.outcomes || ['BMD', 'TBS', 'Osteopenia', 'Osteoporosis'],
    model_types: params.model_types || ['OLS', 'RCS', 'MultinomialLogistic'],
    covariate_model: params.covariate_model || ['age', 'sex', 'bmi', 'smoking', 'alcohol', 'physical_activity'],
    grouping: params.grouping || 'quartile',
    quartile_groups: params.quartile_groups || [5.2, 8.1, 12.8, 35.0],
  } as Record<string, unknown>);
}

/** MR 任务参数 */
export interface MRJobParams {
  exposure_trait: string;
  outcome_trait: string;
  exposure_snps?: string[];
  outcome_dataset_id?: string;
  methods?: string[];
  clump_r2?: number;
  clump_kb?: number;
  p_threshold?: number;
}

/**
 * 创建双样本 MR 分析任务
 *
 * POST /api/ai/mr/jobs
 */
export async function createAIMRJob(
  projectId: number,
  params: MRJobParams,
): Promise<AIServiceResult<AIJobFromAPI>> {
  return createAIJob(projectId, 'mr', {
    exposure_trait: params.exposure_trait,
    exposure: params.exposure_trait,
    outcome_trait: params.outcome_trait,
    outcome: params.outcome_trait,
    exposure_snps: params.exposure_snps || [],
    outcome_dataset_id: params.outcome_dataset_id || '',
    methods: params.methods || ['IVW', 'MR-Egger', 'Weighted Median', 'Weighted Mode'],
    clump_r2: params.clump_r2 ?? 0.001,
    clump_kb: params.clump_kb ?? 10000,
    p_threshold: params.p_threshold ?? 5e-8,
  } as Record<string, unknown>);
}

// ===== AI Agent 自然语言接口 =====

export interface AgentQueryRequest {
  query: string;
  project_id?: number;
  context?: Record<string, unknown>;
  auto_run?: boolean;
}

export interface AgentNextAction {
  label: string;
  action: string;
  params: Record<string, unknown>;
}

export interface AgentQueryResponse {
  answer_type: 'job_created' | 'need_more_info' | 'unsupported' | 'error';
  message: string;
  capability_type: string;
  job_id: string;
  job_status: string;
  extracted_params: Record<string, unknown>;
  missing_params: string[];
  clarification_question: string;
  intent_confidence: number;
  next_actions: AgentNextAction[];
}

/**
 * AI Agent 自然语言交互
 *
 * POST /api/ai/agent
 */
export async function agentQuery(
  payload: AgentQueryRequest,
): Promise<AIServiceResult<AgentQueryResponse>> {
  return withErrorBoundary(async () => {
    const res = await aiApi.post<AIApiEnvelope<AgentQueryResponse>>('/ai/agent', payload);
    if (!res.data.success) {
      throw new Error(res.data.error?.message || 'Agent query failed');
    }
    return res.data.data;
  }, 'AI Agent 请求失败');
}

// ===== AI Chat 接口 =====

export interface ChatRequest {
  message: string;
  project_id?: number;
  context?: Record<string, unknown>;
}

export interface ChatAction {
  label: string;
  action: string;
  params: Record<string, unknown>;
}

export interface ChatResponse {
  type: 'answer' | 'job_created' | 'need_more_info' | 'job_status' | 'error';
  message: string;
  jobId?: string;
  capabilityType?: string;
  actions?: ChatAction[];
  suggestedInputs?: Array<{
    field: string;
    label: string;
    suggested_value: unknown;
    type: string;
    options?: unknown[];
    hint?: string;
  }>;
  blockedFields?: string[];
  metadata?: Record<string, unknown>;
}

/**
 * AI 聊天助手
 *
 * POST /api/ai/chat
 */
export async function chatQuery(
  payload: ChatRequest,
): Promise<AIServiceResult<ChatResponse>> {
  return withErrorBoundary(async () => {
    const res = await aiApi.post<AIApiEnvelope<ChatResponse>>('/ai/chat', payload);
    if (!res.data.success) {
      throw new Error(res.data.error?.message || 'Chat query failed');
    }
    return res.data.data;
  }, 'AI Chat 请求失败');
}

// ===== 报告结果适配 =====

/**
 * 报告结果可能的原始形态：
 * - 后端新 API 返回: { result: {...}, output_files: [...], capability_type: "..." }
 * - result 字段包含完整的 ReportGenerationResult
 *
 * 此函数统一适配不同嵌套层级，确保页面组件拿到一致的 ReportGenerationResult。
 */

function hasStringField(obj: unknown, field: string): obj is Record<string, unknown> {
  return typeof obj === 'object' && obj !== null && field in obj;
}

function isReportObject(obj: unknown): obj is Record<string, unknown> {
  return hasStringField(obj, 'report_id') && hasStringField(obj, 'title');
}

export function adaptReportResult(raw: unknown): ReportGenerationResult | null {
  if (!raw || typeof raw !== 'object') return null;

  const obj = raw as Record<string, unknown>;

  // 情况 1: { result: <report>, output_files: [...] } — 来自 getAIJobResult
  if (obj.result && typeof obj.result === 'object' && isReportObject(obj.result)) {
    return obj.result as unknown as ReportGenerationResult;
  }

  // 情况 2: 直接是 report 对象 — 来自 getReportResult (旧 API)
  if (isReportObject(obj)) {
    return obj as unknown as ReportGenerationResult;
  }

  // 情况 3: 就是 ReportGenerationResult，但缺少必要字段
  return null;
}
