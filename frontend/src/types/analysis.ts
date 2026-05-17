/**
 * AdipoInsight 遗传分析与风险建模类型定义
 *
 * 覆盖能力 C3（GWAS）、C4（双样本 MR）、C5（中介 MR）、
 * C6（风险建模）、C7（报告生成）。
 */

// ===== GWAS 分析 C3 =====

/** GWAS 分析请求参数 */
export interface GWASAnalysisRequest {
  project_id: number;
  /** 表型名称（如 Liver_PDFF） */
  phenotype: string;
  /** 协变量列表（如 age, sex, bmi, PC1-PC10） */
  covariates?: string[];
  /** MAF 过滤阈值 */
  maf_threshold?: number;
  /** HWE p-value 过滤阈值 */
  hwe_threshold?: number;
}

/** GWAS 汇总统计 */
export interface GWASSummary {
  phenotype: string;
  sample_size: number;
  significant_loci_count: number;
  lead_snps_count: number;
  lambda_gc: number;
}

/** 单个显著位点 */
export interface GWASSignificantLocus {
  locus_id: number;
  chr: number;
  start: number;
  end: number;
  lead_snp: string;
  n_snps: number;
  min_pvalue: number;
}

/** 单个先导 SNP */
export interface GWASLeadSNP {
  snp: string;
  chr: number;
  bp: number;
  ea: string;
  oa: string;
  beta: number;
  se: number;
  p_value: number;
}

/** GWAS 完整结果 */
export interface GWASAnalysisResult extends GWASSummary {
  significant_loci: GWASSignificantLocus[];
  lead_snps: GWASLeadSNP[];
}

/** GWAS 输出文件 */
export interface GWASOutputFiles {
  gwas_summary_stats_tsv: string;
  lead_snps_csv: string;
  significant_loci_csv: string;
  gwas_summary_json: string;
}

// ===== OpenGWAS 数据获取 =====

/** OpenGWAS 获取请求 */
export interface OpenGWASFetchRequest {
  project_id: number;
  outcome_id: string;
}

/** OpenGWAS 获取结果 */
export interface OpenGWASFetchResult {
  outcome_id: string;
  outcome_name: string;
  matched_snps: number;
  proxy_snps_used: number;
  source: string;
}

// ===== 双样本 MR C4 =====

/** MR 分析方法 */
export type MRMethod = 'IVW' | 'MR-Egger' | 'Weighted Median' | 'Weighted Mode';

export const MR_METHODS: MRMethod[] = ['IVW', 'MR-Egger', 'Weighted Median', 'Weighted Mode'];

/** MR 分析请求参数 */
export interface MRAnalysisRequest {
  project_id: number;
  exposure: string;
  outcome: string;
  /** Clumping R² 阈值 */
  clump_r2?: number;
  /** Clumping 窗口 (kb) */
  clump_kb?: number;
  /** 工具变量 p-value 阈值 */
  p_threshold?: number;
  /** 使用的 MR 方法列表（默认全部 4 种） */
  methods?: MRMethod[];
}

/** 单个 MR 方法的估计值 */
export interface MREstimate {
  method: MRMethod;
  beta: number;
  se: number;
  or: number;
  ci_lower: number;
  ci_upper: number;
  p_value: number;
}

/** MR 异质性检验 */
export interface MRHeterogeneity {
  method: string;
  q_statistic: number;
  q_df: number;
  q_pval: number;
}

/** MR 多效性检验 */
export interface MRPleiotropy {
  egger_intercept: number;
  se: number;
  pval: number;
}

/** MR 完整结果 */
export interface MRAnalysisResult {
  exposure: string;
  outcome: string;
  estimates: MREstimate[];
  heterogeneity: MRHeterogeneity[];
  pleiotropy: MRPleiotropy;
  primary_method: MRMethod;
  primary_beta: number;
  primary_or: number;
  primary_ci_lower: number;
  primary_ci_upper: number;
  primary_p_value: number;
}

/** MR 输出文件 */
export interface MROutputFiles {
  mr_results_csv: string;
  heterogeneity_csv: string;
  pleiotropy_csv: string;
  mr_summary_json: string;
}

// ===== 中介 MR C5 =====

/** 中介 MR 请求参数 */
export interface MediationMRRequest {
  project_id: number;
  exposure: string;
  outcome: string;
  /** 中介数据源 */
  mediator_source: MediatorSource;
  /** 多重检验校正方法 */
  correction_method?: 'bonferroni' | 'fdr' | 'none';
  /** 显著性阈值 */
  alpha?: number;
}

/** 中介数据来源 */
export type MediatorSource = 'decode_plasma' | 'metabolite_gwas' | 'gwas_catalog' | 'custom';

export const MEDIATOR_SOURCE_LABELS: Record<MediatorSource, string> = {
  decode_plasma: 'deCODE 血浆蛋白 pQTL (4,907)',
  metabolite_gwas: '代谢物 GWAS 数据',
  gwas_catalog: 'GWAS Catalog / OpenGWAS',
  custom: '自定义上传',
};

/** 单个中介蛋白结果 */
export interface MediatorProteinResult {
  protein: string;
  beta_a: number;
  beta_b: number;
  indirect_effect: number;
  se: number;
  proportion_mediated: number;
  p_mediation: number;
  significant: boolean;
}

/** 中介 MR 完整结果 */
export interface MediationMRResult {
  exposure: string;
  outcome: string;
  mediator_source: MediatorSource;
  tested_proteins: number;
  significant_mediators: number;
  top_mediators: MediatorProteinResult[];
  /** 总间接效应 */
  total_indirect_effect: number;
  /** 总直接效应 */
  total_direct_effect: number;
  /** 总效应 */
  total_effect: number;
  /** 总效应 p-value */
  total_effect_pvalue: number;
}

/** 中介 MR 输出文件 */
export interface MediationMROutputFiles {
  mediation_results_csv: string;
  candidate_proteins_csv: string;
  mediation_summary_json: string;
}

// ===== 风险建模 C6 =====

/** 风险等级 */
export type RiskLevel = 'Low' | 'Medium' | 'High';

export const RISK_LEVEL_COLORS: Record<RiskLevel, string> = {
  Low: 'text-green-600',
  Medium: 'text-gold-600',
  High: 'text-danger-600',
};

/** 风险建模请求参数 */
export interface RiskModelingRequest {
  project_id: number;
  exposure: string;
  outcome: string;
  /** 暴露分组方式 */
  grouping?: 'quartile' | 'tertile' | 'median';
  /** 包含的协变量 */
  covariates?: string[];
}

/** OLS 回归结果 */
export interface OLSResult {
  model: string;
  beta: number;
  se: number;
  p_value: number;
}

/** 限制性立方样条 (RCS) 节点 */
export interface RCSKnot {
  knot: number;
  estimate: number;
  se: number;
  p_value: number;
}

/** 风险建模完整结果 */
export interface RiskModelingResult {
  exposure: string;
  outcome: string;
  grouping: string;
  reference_group: string;
  pdff_quartile: string;
  osteopenia_aor: number;
  osteoporosis_aor: number;
  risk_level: RiskLevel;
  model_type: string;
  ols_results: OLSResult[];
  rcs_results: RCSKnot[];
  auc: number;
}

/** 风险建模输出文件 */
export interface RiskModelingOutputFiles {
  ols_results_csv: string;
  rcs_results_csv: string;
  risk_summary_json: string;
}

// ===== 报告生成 C7 =====

/** 报告类型 */
export type ReportType = 'summary' | 'full' | 'competition';

export const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  summary: '摘要报告',
  full: '完整报告',
  competition: '竞赛报告',
};

/** 报告生成请求 */
export interface ReportGenerationRequest {
  project_id: number;
  /** 项目标题 */
  project_title?: string;
  /** 包含的任务 ID 列表（空 = 全部已完成） */
  selected_jobs?: string[];
  /** 包含的分析模块 */
  selected_modules?: ReportModule[];
  /** 报告类型 */
  report_type?: ReportType;
  /** 语言 */
  language?: 'zh-CN' | 'en';
  /** 模板名称 */
  template?: string;
  /** 是否包含图表 */
  include_figures?: boolean;
  /** 是否包含数据表 */
  include_tables?: boolean;
  /** 是否包含 AI 解读 */
  include_ai_interpretation?: boolean;
  /** 自定义备注 */
  custom_notes?: string;
}

/** 报告包含的分析模块 */
export type ReportModule =
  | 'segmentation'
  | 'phenotype'
  | 'gwas'
  | 'mr'
  | 'mediation_mr'
  | 'risk_modeling'
  | 'discussion'
  | 'limitations'
  | 'methods'
  | 'references';

export const REPORT_MODULE_LABELS: Record<ReportModule, string> = {
  segmentation: 'AI 影像分割',
  phenotype: '脂肪表型量化',
  gwas: 'GWAS 全基因组关联分析',
  mr: '孟德尔随机化因果推断',
  mediation_mr: '中介 MR 血浆蛋白分析',
  risk_modeling: '疾病风险建模',
  discussion: '讨论与结论',
  limitations: '研究限制',
  methods: '方法学',
  references: '参考文献',
};

// ===== 报告结果 =====

/** 报告章节 */
export interface ReportSection {
  /** 章节序号 (1, 2, 3...) */
  number: number;
  /** 章节标题 */
  title: string;
  /** Markdown 内容 */
  content: string;
  /** 章节状态 */
  status: 'complete' | 'pending' | 'skipped';
  /** 章节摘要（1-2 句话） */
  summary: string;
  /** 支撑本章节的 job ID 列表 */
  evidence_job_ids: string[];
  /** 关联的图表引用 */
  related_figures: RelatedFigureRef[];
  /** 关联的表格引用 */
  related_tables: RelatedTableRef[];
}

/** 章节内关联的图表引用 */
export interface RelatedFigureRef {
  figure_id: string;
  caption: string;
  type: string;
}

/** 章节内关联的表格引用 */
export interface RelatedTableRef {
  table_id: string;
  caption: string;
  columns: string[];
}

/** 报告图表 */
export interface ReportFigure {
  figure_id: string;
  /** 图表编号 (Figure 1, Figure 2...) */
  number: number;
  /** 图表标题 */
  caption: string;
  /** 图表 URL */
  url: string;
  /** 图表类型 */
  type: 'manhattan' | 'scatter' | 'forest' | 'rcs_curve' | 'qq_plot' | 'heatmap' | 'bar_chart' | 'segmentation_overlay' | 'mechanism_diagram' | 'other';
  /** 所属章节 */
  section_number: number;
  /** 替代文本 */
  alt_text: string;
  /** 数据来源 job ID */
  source_job_id: string;
  /** 图片尺寸 */
  dimensions?: { width: number; height: number };
}

/** 报告表格 */
export interface ReportTable {
  table_id: string;
  /** 表格编号 (Table 1, Table 2...) */
  number: number;
  /** 表格标题 */
  caption: string;
  /** 列定义 */
  columns: TableColumn[];
  /** 行数据 */
  rows: Record<string, unknown>[];
  /** 所属章节 */
  section_number: number;
  /** 数据来源 job ID */
  source_job_id: string;
  /** 表格脚注 */
  footnotes: string[];
}

export interface TableColumn {
  key: string;
  label: string;
  align?: 'left' | 'center' | 'right';
  format?: 'number' | 'scientific' | 'percentage' | 'text';
  precision?: number;
}

/** 参考文献 */
export interface ReportReference {
  ref_id: string;
  /** 引用序号 [1], [2]... */
  number: number;
  /** 引用文本（AMA/Vancouver 格式） */
  text: string;
  /** DOI */
  doi?: string;
  /** 引用类型 */
  type: 'gwas_catalog' | 'opengwas' | 'published_paper' | 'database' | 'method' | 'other';
  /** 在正文中的引用位置 */
  cited_in_sections: number[];
}

/** 导出格式 */
export interface ExportFormat {
  format: 'pdf' | 'docx' | 'html' | 'markdown' | 'latex';
  label: string;
  /** 是否已生成 */
  available: boolean;
  /** 下载 URL */
  url: string;
  /** 文件大小 (bytes) */
  file_size?: number;
}

/** 报告元信息 */
export interface ReportMetadata {
  /** 报告版本 */
  version: string;
  /** 生成时间 */
  generated_at: string;
  /** 生成耗时 (seconds) */
  generation_time_seconds: number;
  /** 使用的 AI 模型（如 mock） */
  ai_model: string;
  /** 包含的数据源 */
  data_sources: string[];
  /** 分析方法 */
  analysis_methods: string[];
  /** 利益冲突声明 */
  conflict_of_interest: string;
  /** 致谢 */
  acknowledgments: string;
}

/** 报告生成结果 */
export interface ReportGenerationResult {
  report_id: string;
  project_id: number;
  /** 报告标题 */
  title: string;
  /** 报告副标题 */
  subtitle: string;
  /** 报告类型 */
  report_type: ReportType;
  /** 语言 */
  language: 'zh-CN' | 'en';
  /** 章节 */
  sections: ReportSection[];
  /** 图表 */
  figures: ReportFigure[];
  /** 表格 */
  tables: ReportTable[];
  /** 参考文献 */
  references: ReportReference[];
  /** 研究限制 */
  limitations: string[];
  /** 关键发现摘要 */
  key_findings: string[];
  /** 导出格式 */
  export_formats: ExportFormat[];
  /** 元信息 */
  metadata: ReportMetadata;
  /** Markdown 正文 */
  content_markdown: string;
  /** 完成的章节数 */
  completed_sections: number;
  /** 总章节数 */
  total_sections: number;
  /** AI 解读文本 */
  ai_interpretation: string;
  /** 输出文件列表 */
  output_files: string[];
}

/** 报告输出文件 */
export interface ReportOutputFiles {
  final_report_md: string;
  final_report_pdf: string;
  final_report_docx: string;
  figures_archive_zip: string;
  tables_csv: string;
}
