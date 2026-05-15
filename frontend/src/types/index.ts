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

export const TASK_TYPE_LABELS: Record<string, string> = {
  image_segmentation: 'AI 影像分割',
  gwas_analysis: 'GWAS 分析',
  opengwas_fetch: 'OpenGWAS 数据获取',
  mendelian_randomization: '孟德尔随机化分析',
  mediation_mr: '中介 MR 分析',
  risk_modeling: '风险建模',
  report_generation: '报告生成',
};

export const PIPELINE_ORDER = [
  'image_segmentation', 'gwas_analysis', 'opengwas_fetch',
  'mendelian_randomization', 'mediation_mr', 'risk_modeling', 'report_generation',
];
