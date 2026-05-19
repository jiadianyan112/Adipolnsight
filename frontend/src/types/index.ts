/**
 * AdipoInsight 类型定义总入口
 *
 * 向后兼容：所有旧类型保持此文件导出。
 * 新增 AI 类型分别定义在 ai.ts / job.ts / segmentation.ts / analysis.ts。
 */

// ===== 旧类型（v0.1.0 兼容） =====

export interface Project {
  id: number;
  name: string;
  research_goal: string;
  exposure: string;
  outcome: string;
  mediator_set: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  research_goal: string;
  exposure: string;
  outcome: string;
  mediator_set: string;
}

export interface AnalysisTask {
  id: number;
  project_id: number;
  task_type: string;
  task_name: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  progress: number;
  input_json: string;
  output_json: string;
  error_code: string;
  error_message: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisResult {
  id: number;
  task_id: number;
  project_id: number;
  result_type: string;
  summary_json: string;
  output_files_json: string;
  created_at: string;
}

export interface Report {
  id: number;
  project_id: number;
  title: string;
  content_markdown: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface FileAsset {
  id: number;
  project_id: number;
  file_name: string;
  file_type: string;
  file_path: string;
  file_size: number;
  created_at: string;
}

// ===== 旧常量（保留兼容，建议迁移至 ai.ts 中的新定义） =====

/** 分析类型中文标签（紧凑版，用于 Tab、Badge 等） */
export const TASK_TYPE_LABELS: Record<string, string> = {
  image_segmentation: '影像分割',
  gwas_analysis: 'GWAS 全基因组关联',
  opengwas_fetch: 'OpenGWAS 数据获取',
  mendelian_randomization: '孟德尔随机化',
  mediation_mr: '中介孟德尔随机化',
  risk_modeling: '风险建模',
  report_generation: '科研报告生成',
};

/** @deprecated 使用 ai.ts 中的 PIPELINE_ORDER（含 phenotype_quantification） */
export const PIPELINE_ORDER = [
  'image_segmentation', 'gwas_analysis', 'opengwas_fetch',
  'mendelian_randomization', 'mediation_mr', 'risk_modeling', 'report_generation',
];

// ===== 新 AI 类型重导出 =====

export type { AICapabilityType, AIAdapterMode, WorkflowGroup, AIRequestBase, AIResultBase } from './ai';
export {
  AI_CAPABILITY_LABELS,
  AI_CAPABILITY_WORKFLOW,
  AI_CAPABILITY_DEPENDS_ON,
} from './ai';

export type {
  AIJobStatus,
  AIJobProgress,
  AIJobErrorCode,
  AIJob,
  AIJobCreateRequest,
  AIJobPollingConfig,
  AIJobStoreState,
} from './job';
export {
  AI_JOB_TERMINAL_STATUSES,
  AI_JOB_STATUS_LABELS,
  AI_JOB_ERROR_LABELS,
  PROGRESS_STAGES,
  DEFAULT_POLLING_CONFIG,
  AI_JOB_TERMINAL_STATUS_VALUES,
} from './job';
export { isTerminalStatus, isSuccessStatus, isFailedStatus } from './job';

export type {
  UploadedFile,
  FileType,
  SegmentationTarget,
  SegmentationRequest,
  DiceScores,
  VolumeMetrics,
  QualityControl,
  SegmentationDiceScores,
  SegmentationResult,
  SegmentationOutputFiles,
  PhenotypeSummary,
  PhenotypeQuantificationResult,
  PhenotypeMetricDisplay,
} from './segmentation';
export {
  FILE_TYPE_LABELS,
  MRI_ACCEPTED_FORMATS,
  GENOTYPE_ACCEPTED_FORMATS,
  DEFAULT_SEGMENTATION_TARGETS,
  PHENOTYPE_METRIC_DISPLAY,
} from './segmentation';

export type {
  GWASAnalysisRequest,
  GWASSummary,
  GWASSignificantLocus,
  GWASLeadSNP,
  GWASAnalysisResult,
  GWASOutputFiles,
  OpenGWASFetchRequest,
  OpenGWASFetchResult,
  MRMethod,
  MRAnalysisRequest,
  MREstimate,
  MRHeterogeneity,
  MRPleiotropy,
  MRAnalysisResult,
  MROutputFiles,
  MediationMRRequest,
  MediatorSource,
  MediatorProteinResult,
  MediationMRResult,
  MediationMROutputFiles,
  RiskLevel,
  RiskModelingRequest,
  OLSResult,
  RCSKnot,
  RiskModelingResult,
  RiskModelingOutputFiles,
  ReportGenerationRequest,
  ReportSection,
  ReportGenerationResult,
  ReportOutputFiles,
  ReportFigure,
  ReportTable,
  ReportReference,
  ExportFormat,
} from './analysis';
export {
  MR_METHODS,
  MEDIATOR_SOURCE_LABELS,
  RISK_LEVEL_COLORS,
} from './analysis';

// ===== LLM 类型重导出 =====

export type {
  LLMProviderName,
  LLMTaskType,
  LLMMessageRole,
  LLMMessage,
  LLMResponseFormat,
  LLMRequest,
  LLMUsage,
  LLMResponse,
  LLMError,
  LLMIntentResult,
  LLMResultInterpretation,
  LLMErrorExplanation,
  LLMReportEnhancement,
  LLMChatContext,
} from './llm';
export {
  LLM_PROVIDER_LABELS,
  LLM_TASK_LABELS,
} from './llm';
