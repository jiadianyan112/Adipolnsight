/**
 * AI 影像分割结果展示组件
 *
 * 渲染完整的 TSSA-UNet 分割结果，包括 DICE、体积、QC、警告。
 * 结果数据来自后端 SkillOutput（通过 AI Job API），前端不做任何伪造。
 */

import type { DiceScores, VolumeMetrics, QualityControl } from '../../types';
import DashboardCard from '../shared/DashboardCard';
import StatusBadge from '../shared/StatusBadge';

// ===== Props =====

interface Props {
  /** 完整的分割结果（来自后端 getAIJobResult） */
  data: SegmentationResultData | null;
  /** 当前加载状态 */
  loading?: boolean;
  /** 错误信息 */
  error?: string | null;
  /** 关闭回调 */
  onClose?: () => void;
}

export interface SegmentationResultData {
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

// ===== 常量 =====

const REGION_LABELS: Record<string, string> = {
  liver: '肝脏',
  pancreas: '胰腺',
  visceral_fat: '内脏脂肪',
  subcutaneous_fat: '皮下脂肪',
  bone_marrow: '骨髓',
  kidney: '肾脏',
  muscle: '肌肉',
};

const DICE_GRADE = (score: number): { label: string; color: string } => {
  if (score >= 0.92) return { label: '优秀', color: 'text-green-600' };
  if (score >= 0.88) return { label: '良好', color: 'text-navy-600' };
  if (score >= 0.83) return { label: '临界', color: 'text-gold-600' };
  return { label: '需改进', color: 'text-danger-600' };
};

// ===== Loading / Empty / Failed states =====

function LoadingState() {
  return (
    <DashboardCard padding="lg">
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-3 text-text-muted">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="font-heading text-sm">加载分割结果...</span>
        </div>
      </div>
    </DashboardCard>
  );
}

function EmptyState() {
  return (
    <DashboardCard padding="lg">
      <div className="text-center py-12 text-text-muted">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-surface-alt flex items-center justify-center">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.53 16.122a3 3 0 00-5.78 1.128 2.25 2.25 0 01-2.4 2.245 4.5 4.5 0 008.4-2.245c0-.399-.078-.78-.22-1.128zm0 0a15.998 15.998 0 003.388-1.62m-5.043-.025a15.994 15.994 0 011.622-3.395m3.42 3.42a15.995 15.995 0 004.764-4.648l3.876-5.814a1.151 1.151 0 00-1.597-1.597L14.146 6.32a15.996 15.996 0 00-4.649 4.763m3.42 3.42a6.776 6.776 0 00-3.42-3.42" />
          </svg>
        </div>
        <p className="text-sm font-heading font-medium">暂无分割结果</p>
        <p className="text-xs mt-1">请先上传 MRI 影像并运行 AI 分割</p>
      </div>
    </DashboardCard>
  );
}

function FailedState({ message, onClose }: { message: string; onClose?: () => void }) {
  return (
    <DashboardCard padding="lg">
      <div className="text-center py-8">
        <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-red-50 flex items-center justify-center">
          <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <p className="text-sm font-heading font-medium text-red-700">结果加载失败</p>
        <p className="text-xs text-red-500 mt-1 max-w-md mx-auto">{message}</p>
        {onClose && (
          <button onClick={onClose} className="mt-3 text-xs text-navy-600 hover:text-navy-800 font-medium">
            关闭
          </button>
        )}
      </div>
    </DashboardCard>
  );
}

// ===== 主组件 =====

export default function SegmentationResultView({ data, loading, error, onClose }: Props) {
  // --- Loading ---
  if (loading) return <LoadingState />;

  // --- Failed ---
  if (error) return <FailedState message={error} onClose={onClose} />;

  // --- Empty ---
  if (!data) return <EmptyState />;

  const { dice_scores, volume_metrics, quality_control, warnings } = data;

  return (
    <DashboardCard padding="lg" className="space-y-5">
      {/* ===== Header ===== */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="font-heading font-semibold text-text-primary">
            影像分割结果
          </h3>
          <span className="text-xs text-text-muted font-mono">{data.segmentation_id}</span>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={quality_control.status} />
          {onClose && (
            <button onClick={onClose}
              className="text-xs text-text-muted hover:text-text-secondary font-medium transition-card">
              关闭
            </button>
          )}
        </div>
      </div>

      {/* Model info bar */}
      <div className="flex items-center gap-3 px-3 py-2 bg-surface rounded-lg text-xs">
        <span className="flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
          <span className="font-heading font-semibold text-text-primary">{data.model_name}</span>
        </span>
        <span className="text-text-muted">v{data.model_version}</span>
        <span className="text-border">|</span>
        <span className="text-text-muted">
          分割区域：
          {data.target_regions.map((r) => REGION_LABELS[r] || r).join('、')}
        </span>
      </div>

      {/* ===== DICE Scores Grid ===== */}
      <div>
        <h4 className="section-title-sm mb-3">DICE 相似系数</h4>
        <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
          {(['liver', 'pancreas', 'visceral_fat', 'subcutaneous_fat', 'bone_marrow'] as const).map((region) => {
            const score = dice_scores?.[region];
            const grade = score != null ? DICE_GRADE(score) : { label: '—', color: 'text-text-muted' };
            return (
              <div key={region}
                className="bg-surface rounded-lg p-3 text-center border border-border-light">
                <p className="text-[10px] text-text-muted mb-1">{REGION_LABELS[region] || region}</p>
                <p className={`text-lg font-heading font-bold ${grade.color}`}>
                  {score != null ? score.toFixed(3) : '—'}
                </p>
                <p className={`text-[10px] font-medium ${grade.color}`}>{grade.label}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* ===== Volume Metrics ===== */}
      <div>
        <h4 className="section-title-sm mb-3">体积与定量指标</h4>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {([
            { key: 'liver_volume_cm3' as const, label: '肝脏体积', unit: 'cm³', precision: 0 },
            { key: 'visceral_fat_volume_cm3' as const, label: '内脏脂肪体积', unit: 'cm³', precision: 0 },
            { key: 'subcutaneous_fat_volume_cm3' as const, label: '皮下脂肪体积', unit: 'cm³', precision: 0 },
            { key: 'liver_pdff_pct' as const, label: '肝脏 PDFF', unit: '%', precision: 1 },
            { key: 'pancreatic_fat_fraction_pct' as const, label: '胰腺脂肪分数', unit: '%', precision: 1 },
            { key: 'bone_marrow_fat_fraction_pct' as const, label: '骨髓脂肪分数', unit: '%', precision: 1 },
            { key: 'muscle_volume_L' as const, label: '肌肉体积', unit: 'L', precision: 1 },
            { key: 'sat_vat_ratio' as const, label: 'SAT/VAT 比值', unit: '', precision: 2 },
            { key: 'total_body_fat_pct' as const, label: '全身脂肪百分比', unit: '%', precision: 1 },
            { key: 'bone_density_g_cm3' as const, label: '骨密度', unit: 'g/cm³', precision: 2 },
          ] as const).map(({ key, label, unit, precision }) => {
            const value = volume_metrics?.[key];
            return (
              <div key={key}
                className="bg-surface rounded-lg p-2.5 border border-border-light">
                <p className="text-[10px] text-text-muted truncate">{label}</p>
                <p className="text-sm font-heading font-bold text-text-primary mt-0.5">
                  {value != null ? value.toFixed(precision) : '—'}
                  {unit && <span className="text-[10px] text-text-muted ml-0.5 font-normal">{unit}</span>}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* ===== Quality Control ===== */}
      <div>
        <h4 className="section-title-sm mb-3">质量控制</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {([
            { key: 'overall_quality_score' as const, label: '综合质量评分', format: (v: number) => v.toFixed(2) },
            { key: 'snr_estimate_db' as const, label: 'SNR 估计', format: (v: number) => `${v.toFixed(1)} dB` },
            { key: 'field_inhomogeneity_score' as const, label: '磁场不均匀性', format: (v: number) => v.toFixed(2) },
            { key: 'coverage_completeness' as const, label: '覆盖完整度', format: (v: number) => `${(v * 100).toFixed(0)}%` },
          ] as const).map(({ key, label, format }) => {
            const value = quality_control?.[key];
            return (
              <div key={key}
                className="bg-surface rounded-lg p-2.5 border border-border-light">
                <p className="text-[10px] text-text-muted">{label}</p>
                <p className="text-sm font-heading font-bold text-text-primary mt-0.5">
                  {value != null ? format(value) : '—'}
                </p>
              </div>
            );
          })}
          {/* Motion artifact flag */}
          <div className="bg-surface rounded-lg p-2.5 border border-border-light">
            <p className="text-[10px] text-text-muted">运动伪影</p>
            <p className={`text-sm font-heading font-bold mt-0.5 ${quality_control?.motion_artifact_detected ? 'text-danger-600' : 'text-green-600'}`}>
              {quality_control?.motion_artifact_detected ? '检测到' : '未检测到'}
            </p>
          </div>
        </div>
      </div>

      {/* ===== Preview Images (Placeholder) ===== */}
      <div>
        <h4 className="section-title-sm mb-3">分割预览</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Overlay Preview */}
          <div className="bg-surface-alt rounded-xl border border-border p-4 text-center">
            <p className="text-xs font-medium text-text-secondary mb-3">分割叠加预览</p>
            <div className="aspect-[4/3] bg-white rounded-lg border border-border flex items-center justify-center">
              {data.overlay_preview_url ? (
                <img
                  src={data.overlay_preview_url}
                  alt="Segmentation overlay"
                  className="max-w-full max-h-full object-contain rounded"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                  }}
                />
              ) : null}
              <div className={data.overlay_preview_url ? 'hidden' : 'flex flex-col items-center gap-2'}>
                <svg className="w-8 h-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
                </svg>
                <span className="text-[10px] text-text-muted">分割叠加预览</span>
                <span className="text-[9px] text-text-muted">运行真实模型后生成</span>
              </div>
            </div>
          </div>

          {/* Mask Preview */}
          <div className="bg-surface-alt rounded-xl border border-border p-4 text-center">
            <p className="text-xs font-medium text-text-secondary mb-3">分割 Mask 预览</p>
            <div className="aspect-[4/3] bg-white rounded-lg border border-border flex items-center justify-center">
              {data.mask_preview_url ? (
                <img
                  src={data.mask_preview_url}
                  alt="Segmentation mask"
                  className="max-w-full max-h-full object-contain rounded"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                  }}
                />
              ) : null}
              <div className={data.mask_preview_url ? 'hidden' : 'flex flex-col items-center gap-2'}>
                <svg className="w-8 h-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                </svg>
                <span className="text-[10px] text-text-muted">分割 Mask 预览</span>
                <span className="text-[9px] text-text-muted">运行真实模型后生成</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ===== Warnings ===== */}
      {warnings && warnings.length > 0 && (
        <div className="space-y-1.5">
          <h4 className="section-title-sm text-gold-600">质量警告</h4>
          {warnings.map((w, i) => (
            <div key={i}
              className="flex items-start gap-2 px-3 py-2 bg-gold-50 border border-gold-200 rounded-lg text-xs text-gold-700">
              <svg className="w-3.5 h-3.5 text-gold-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}
    </DashboardCard>
  );
}
