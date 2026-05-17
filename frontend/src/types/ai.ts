/**
 * AdipoInsight AI 能力核心类型定义
 *
 * 所有 AI 能力类型、适配器模式、能力配置均在此定义。
 * 前端组件和 API client 均引用此文件，不直接硬编码能力名称。
 */

// ===== AI 能力类型枚举 =====

/** 8 项 AI 分析能力，对应后端 task_type */
export type AICapabilityType =
  | 'image_segmentation'
  | 'phenotype_quantification'
  | 'gwas_analysis'
  | 'opengwas_fetch'
  | 'mendelian_randomization'
  | 'mediation_mr'
  | 'risk_modeling'
  | 'report_generation';

/** AI 能力人类可读标签 */
export const AI_CAPABILITY_LABELS: Record<AICapabilityType, string> = {
  image_segmentation: 'AI 影像分割',
  phenotype_quantification: '脂肪表型量化',
  gwas_analysis: 'GWAS 全基因组关联分析',
  opengwas_fetch: 'OpenGWAS 数据获取',
  mendelian_randomization: '双样本孟德尔随机化',
  mediation_mr: '中介孟德尔随机化分析',
  risk_modeling: '疾病风险建模',
  report_generation: '科研报告生成',
};

/** 工作流分组 */
export type WorkflowGroup = 'imaging' | 'genetics' | 'causal' | 'risk' | 'report';

/** AI 能力 → 工作流分组映射 */
export const AI_CAPABILITY_WORKFLOW: Record<AICapabilityType, WorkflowGroup> = {
  image_segmentation: 'imaging',
  phenotype_quantification: 'imaging',
  gwas_analysis: 'genetics',
  opengwas_fetch: 'genetics',
  mendelian_randomization: 'causal',
  mediation_mr: 'causal',
  risk_modeling: 'risk',
  report_generation: 'report',
};

/** 能力依赖关系：key 依赖 values 中的能力先完成 */
export const AI_CAPABILITY_DEPENDS_ON: Partial<Record<AICapabilityType, AICapabilityType[]>> = {
  phenotype_quantification: ['image_segmentation'],
  gwas_analysis: ['phenotype_quantification'],
  mendelian_randomization: ['gwas_analysis'],
  mediation_mr: ['gwas_analysis', 'mendelian_randomization'],
  risk_modeling: ['phenotype_quantification', 'mendelian_randomization', 'mediation_mr'],
  report_generation: [
    'image_segmentation',
    'gwas_analysis',
    'mendelian_randomization',
    'mediation_mr',
    'risk_modeling',
  ],
};

/** Pipeline 默认执行顺序 */
export const PIPELINE_ORDER: AICapabilityType[] = [
  'image_segmentation',
  'phenotype_quantification',
  'gwas_analysis',
  'opengwas_fetch',
  'mendelian_randomization',
  'mediation_mr',
  'risk_modeling',
  'report_generation',
];

// ===== 适配器模式 =====

/** AI 适配器运行模式 */
export type AIAdapterMode = 'mock' | 'real' | 'hybrid';

/** 各能力当前使用的适配器模式 */
export type AIAdapterModeMap = Record<AICapabilityType, AIAdapterMode>;

// ===== 参数类型基础 =====

/** 所有 AI 能力 Request 的基础字段 */
export interface AIRequestBase {
  project_id: number;
  task_type: AICapabilityType;
  /** 能力特定参数，由各具体 Request 类型定义 */
  parameters: Record<string, unknown>;
}

/** 所有 AI 能力 Result 的基础字段 */
export interface AIResultBase {
  id: number;
  task_id: number;
  project_id: number;
  result_type: AICapabilityType;
  /** JSON 字符串，各具体 Result 类型负责 parse */
  summary_json: string;
  /** JSON 字符串数组 */
  output_files_json: string;
  created_at: string;
}
