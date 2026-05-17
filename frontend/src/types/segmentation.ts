/**
 * AdipoInsight 影像分割与表型量化类型定义
 *
 * 覆盖能力 C1（MRI 影像上传与 AI 分割）和 C2（多部位脂肪表型量化）。
 */

// ===== 文件上传 =====

/** 上传文件元信息 */
export interface UploadedFile {
  id: number;
  project_id: number;
  file_name: string;
  file_type: FileType;
  file_path: string;
  file_size: number;
  created_at: string;
}

/** 支持的文件类型 */
export type FileType = 'mri' | 'phenotype' | 'covariates' | 'genotype';

export const FILE_TYPE_LABELS: Record<FileType, string> = {
  mri: 'MRI 影像',
  phenotype: '表型数据',
  covariates: '协变量',
  genotype: '基因组数据',
};

/** 支持的影像格式 */
export const MRI_ACCEPTED_FORMATS = ['.nii', '.nii.gz', '.dcm', '.dicom'] as const;

/** 支持的基因组数据格式 */
export const GENOTYPE_ACCEPTED_FORMATS = ['.bed', '.bim', '.fam', '.vcf', '.vcf.gz', '.pgen', '.pvar', '.psam'] as const;

// ===== 影像分割 C1 =====

/** 分割请求参数 */
export interface SegmentationRequest {
  project_id: number;
  /** 上传后的 MRI 文件 ID */
  file_id: number;
  /** 目标解剖结构（默认全部） */
  target_structures?: SegmentationTarget[];
}

/** 分割目标解剖结构 */
export type SegmentationTarget =
  | 'liver'
  | 'visceral_fat'
  | 'subcutaneous_fat'
  | 'bone_marrow'
  | 'pancreas'
  | 'kidney'
  | 'muscle';

export const DEFAULT_SEGMENTATION_TARGETS: SegmentationTarget[] = [
  'liver',
  'visceral_fat',
  'subcutaneous_fat',
  'bone_marrow',
];

/** 各解剖结构 DICE 相似系数 (0-1) */
export interface DiceScores {
  liver: number;
  pancreas: number;
  visceral_fat: number;
  subcutaneous_fat: number;
  bone_marrow: number;
}

/** 体积与定量指标 */
export interface VolumeMetrics {
  liver_volume_cm3: number;
  visceral_fat_volume_cm3: number;
  subcutaneous_fat_volume_cm3: number;
  pancreatic_fat_fraction_pct: number;
  liver_pdff_pct: number;
  bone_marrow_fat_fraction_pct: number;
  muscle_volume_L: number;
  sat_vat_ratio: number;
  total_body_fat_pct: number;
  bone_density_g_cm3: number;
}

/** 分割质量评估 */
export interface QualityControl {
  status: 'passed' | 'warning' | 'failed';
  overall_quality_score: number;
  motion_artifact_detected: boolean;
  field_inhomogeneity_score: number;
  snr_estimate_db: number;
  coverage_completeness: number;
}

/** 完整的 AI 分割输出 */
export interface SegmentationResult {
  segmentation_id: string;
  model_name: string;
  model_version: string;
  target_regions: string[];
  dice_scores: DiceScores;
  volume_metrics: VolumeMetrics;
  quality_control: QualityControl;
  mask_preview_url: string;
  overlay_preview_url: string;
  warnings: string[];
}

/** @deprecated Use DiceScores instead */
export interface SegmentationDiceScores {
  dice_liver: number;
  dice_visceral_fat: number;
  dice_subcutaneous_fat: number;
  dice_bone_marrow: number;
}

/** 输出文件清单 */
export interface SegmentationOutputFiles {
  segmentation_metrics_json: string;
  fat_quantification_csv: string;
  overlay_preview_png: string;
}

// ===== 脂肪表型量化 C2 =====

/** 表型摘要指标 */
export interface PhenotypeSummary {
  /** 肝脏质子密度脂肪分数 (%) */
  liver_pdff: number;
  /** 内脏脂肪体积 (cm³) */
  visceral_fat_volume: number;
  /** 皮下脂肪体积 (cm³) */
  subcutaneous_fat_volume: number;
  /** 骨髓脂肪分数 (0–1) */
  bone_marrow_fat_fraction: number;
  /** 全身脂肪百分比 (%) */
  total_body_fat_pct: number;
  /** 肌肉体积 (L) */
  muscle_volume: number;
  /** SAT/VAT 比值 */
  sat_vat_ratio: number;
  /** 骨密度 (g/cm²) */
  bone_density: number;
}

/** 表型量化结果 */
export interface PhenotypeQuantificationResult extends PhenotypeSummary {
  qc_status: 'passed' | 'warning' | 'failed';
}

/** 单个表型指标的展示元数据 */
export interface PhenotypeMetricDisplay {
  key: keyof PhenotypeSummary;
  label: string;
  unit: string;
  precision: number;
  highlight: boolean;
}

/** 全部表型指标的展示配置 */
export const PHENOTYPE_METRIC_DISPLAY: PhenotypeMetricDisplay[] = [
  { key: 'total_body_fat_pct', label: '全身脂肪', unit: '%', precision: 1, highlight: true },
  { key: 'visceral_fat_volume', label: '内脏脂肪', unit: 'L', precision: 2, highlight: false },
  { key: 'subcutaneous_fat_volume', label: '皮下脂肪', unit: 'L', precision: 2, highlight: false },
  { key: 'muscle_volume', label: '肌肉体积', unit: 'L', precision: 1, highlight: false },
  { key: 'liver_pdff', label: '肝脏 PDFF', unit: '%', precision: 1, highlight: false },
  { key: 'sat_vat_ratio', label: 'SAT/VAT 比值', unit: '', precision: 2, highlight: false },
  { key: 'bone_marrow_fat_fraction', label: '骨髓脂肪分数', unit: '%', precision: 1, highlight: false },
  { key: 'bone_density', label: '骨密度', unit: 'g/cm²', precision: 2, highlight: false },
];
