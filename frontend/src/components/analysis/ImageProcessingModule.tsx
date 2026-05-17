import { useState, useEffect, useRef } from 'react';
import type { AnalysisTask, UploadedFile, DiceScores, VolumeMetrics, QualityControl } from '../../types';
import { uploadMedicalImage, createAISegmentationJob, getAIJobStatus, getAIJobResult } from '../../services/aiService';
import type { AIJobFromAPI } from '../../services/aiService';
import DashboardCard from '../shared/DashboardCard';
import ProgressBar from '../shared/ProgressBar';
import MiniChartCard from '../shared/MiniChartCard';
import MetricSummaryCard from '../shared/MetricSummaryCard';
import PrimaryButton from '../shared/PrimaryButton';
import SecondaryButton from '../shared/SecondaryButton';
import StatusBadge from '../shared/StatusBadge';

interface Props {
  imageTask?: AnalysisTask;
  projectId?: number;
  onViewResult?: (taskId: number) => void;
  onSaveAndContinue?: () => void;
  onUploadComplete?: (file: UploadedFile) => void;
  onSegmentationComplete?: (data: SegmentationResultFromAPI) => void;
}

/** 支持的医学影像文件后缀 */
const MEDICAL_IMAGE_EXTENSIONS = ['.nii', '.nii.gz', '.dcm', '.dicom', '.zip', '.nrrd'];

/** 上传状态机 */
type UploadState = 'idle' | 'uploading' | 'success' | 'failed';

/** AI 分割状态机 */
type SegState = 'idle' | 'creating' | 'running' | 'done' | 'failed';

/** 从后端 SkillOutput 或 AIJobFromAPI result 解析的分割结果 */
interface SegmentationResultFromAPI {
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

const EMPTY_PHENOTYPE_CARD = (title: string, unit: string) => ({
  title, value: '—', unit, trend: undefined as 'up' | 'down' | 'stable' | undefined,
  trendValue: '等待分析结果', sparkline: [] as { v: number }[], sparklineColor: 'var(--color-text-muted)',
});

function BodyScanIllustration() {
  return (
    <svg width="120" height="160" viewBox="0 0 120 160" fill="none" className="shrink-0">
      {/* Background glow */}
      <ellipse cx="60" cy="80" rx="45" ry="70" fill="url(#scanGlow)" opacity="0.3" />
      {/* Body outline */}
      <ellipse cx="60" cy="35" rx="16" ry="18" stroke="var(--color-navy-400)" strokeWidth="1" fill="none" opacity="0.6" />
      <line x1="44" y1="50" x2="44" y2="130" stroke="var(--color-navy-400)" strokeWidth="1" opacity="0.4" />
      <line x1="76" y1="50" x2="76" y2="130" stroke="var(--color-navy-400)" strokeWidth="1" opacity="0.4" />
      <path d="M44 55 Q60 65 76 55" stroke="var(--color-navy-400)" strokeWidth="1" opacity="0.4" fill="none" />
      <path d="M44 130 Q60 140 76 130" stroke="var(--color-navy-400)" strokeWidth="1" opacity="0.4" fill="none" />
      {/* Scan lines */}
      {[65, 72, 79, 86, 93, 100, 107, 114, 121].map((y, i) => (
        <line
          key={y}
          x1={44 + Math.sin(i * 0.5) * 4}
          y1={y}
          x2={76 - Math.sin(i * 0.7) * 3}
          y2={y}
          stroke="var(--color-navy-400)"
          strokeWidth="0.5"
          opacity={0.15 + i * 0.03}
        />
      ))}
      {/* Spine indicator */}
      <line x1="60" y1="50" x2="60" y2="130" stroke="var(--color-navy-400)" strokeWidth="0.5" opacity="0.2" strokeDasharray="3 3" />
      {/* Scan focus crosshair */}
      <circle cx="60" cy="90" r="30" stroke="var(--color-blue-400)" strokeWidth="0.5" opacity="0.3" strokeDasharray="4 4" />
      <circle cx="60" cy="90" r="22" stroke="var(--color-blue-400)" strokeWidth="0.5" opacity="0.2" />
      {/* Liver region highlight */}
      <ellipse cx="58" cy="75" rx="8" ry="5" fill="var(--color-blue-400)" opacity="0.12" />
      {/* Status dot */}
      <circle cx="52" cy="75" r="2" fill="var(--color-blue-500)" opacity="0.8">
        <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite" />
      </circle>
      <defs>
        <radialGradient id="scanGlow" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="var(--color-blue-400)" stopOpacity="0.8" />
          <stop offset="100%" stopColor="var(--color-blue-400)" stopOpacity="0" />
        </radialGradient>
      </defs>
    </svg>
  );
}

export default function ImageProcessingModule({ imageTask, projectId, onViewResult, onSaveAndContinue, onUploadComplete, onSegmentationComplete }: Props) {
  // ---- 上传状态 ----
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadedFileData, setUploadedFileData] = useState<UploadedFile | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // ---- AI 分割状态 ----
  const [segState, setSegState] = useState<SegState>('idle');
  const [segJobId, setSegJobId] = useState<string | null>(null);
  const [segProgress, setSegProgress] = useState<number>(0);
  const [segStage, setSegStage] = useState<string>('');
  const [segError, setSegError] = useState<string | null>(null);
  const [segResult, setSegResult] = useState<SegmentationResultFromAPI | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ---- 衍生状态 ----
  const isRunning = imageTask?.status === 'running' || segState === 'running';
  const isSuccess = imageTask?.status === 'success' || segState === 'done';
  const taskProgress = segState === 'running' ? segProgress : (imageTask?.progress ?? 0);

  // 清理轮询
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  /** 校验文件后缀是否在医学影像格式白名单中 */
  const isValidMedicalImage = (name: string): boolean => {
    const lower = name.toLowerCase();
    return MEDICAL_IMAGE_EXTENSIONS.some((ext) => lower.endsWith(ext));
  };

  /** 文件选择：校验格式，不立即上传 */
  const handleFileSelect = (file: File) => {
    if (!isValidMedicalImage(file.name)) {
      setUploadState('failed');
      setUploadError(`不支持的文件格式：${file.name.split('.').pop()}。支持：${MEDICAL_IMAGE_EXTENSIONS.join(', ')}`);
      return;
    }
    setSelectedFile(file);
    setUploadedFileName(file.name);
    setUploadState('idle');
    setUploadError(null);
    setUploadedFileData(null);
  };

  /** 执行真实上传 */
  const handleUpload = async () => {
    if (!selectedFile || !projectId) {
      setUploadError('请先选择文件');
      return;
    }
    setUploadState('uploading');
    setUploadError(null);
    setUploadProgress(0);

    const result = await uploadMedicalImage(
      projectId,
      selectedFile,
      (pct: number) => setUploadProgress(pct),
    );

    if (result.ok) {
      setUploadState('success');
      setUploadProgress(100);
      setUploadedFileData(result.data);
      onUploadComplete?.(result.data);
    } else {
      setUploadState('failed');
      setUploadError(result.message);
      setUploadProgress(0);
    }
  };

  /** 停止轮询 */
  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  /** 开始 AI 分割 */
  const handleStartSegmentation = async () => {
    if (!uploadedFileData || !projectId) return;
    setSegState('creating');
    setSegError(null);

    const result = await createAISegmentationJob(projectId, {
      file_id: uploadedFileData.id,
      modality: 'MRI',
      target_structures: ['liver', 'visceral_fat', 'subcutaneous_fat', 'bone_marrow'],
      model_name: 'TSSA-UNet',
      mode: 'mock',
    });

    if (!result.ok) {
      setSegState('failed');
      setSegError(result.message);
      return;
    }

    setSegState('running');
    setSegJobId(result.data.job_id);
    setSegProgress(0);
    setSegStage('开始执行');

    // 开始轮询
    const jobId = result.data.job_id;
    pollRef.current = setInterval(async () => {
      const status = await getAIJobStatus(jobId);
      if (!status.ok) {
        stopPolling();
        setSegState('failed');
        setSegError(status.message);
        return;
      }
      const job = status.data;
      setSegProgress(job.progress);
      setSegStage(job.progress_stage);

      if (job.status === 'succeeded') {
        stopPolling();
        // 获取结果
        const jobResult = await getAIJobResult(jobId);
        if (jobResult.ok && jobResult.data.result) {
          const parsed = jobResult.data.result as SegmentationResultFromAPI;
          setSegResult(parsed);
          setSegState('done');
          setSegProgress(100);
          onSegmentationComplete?.(parsed);
        } else {
          setSegState('failed');
          setSegError('结果获取失败');
        }
      } else if (job.status === 'failed') {
        stopPolling();
        setSegState('failed');
        setSegError(job.error_message || '分割任务执行失败');
      }
    }, 2000);
  };

  return (
    <DashboardCard padding="lg" className="space-y-5">
      {/* Section header with numbered badge */}
      <div className="flex items-center gap-3">
        <span className="shrink-0 w-7 h-7 rounded-lg bg-navy-700 text-white flex items-center justify-center text-xs font-heading font-bold">
          1
        </span>
        <div>
          <h3 className="section-title">影像处理模块</h3>
          <p className="text-xs text-text-muted mt-0.5">AI 驱动的 MRI 身体成分分析</p>
        </div>
        {imageTask && (
          <StatusBadge status={imageTask.status} />
        )}
      </div>

      {/* ===== MRI Upload Card ===== */}
      <div className="card-dashboard p-4 bg-surface-alt/50">
        <div className="flex items-center gap-1.5 mb-3">
          <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          <h4 className="font-heading font-semibold text-sm text-text-primary">上传 MRI 影像</h4>
        </div>

        <div className="flex gap-4">
          {/* Upload zone + progress */}
          <div className="flex-1 min-w-0 space-y-3">
            {/* ---- AI 分割进度条（task running） ---- */}
            {isRunning && (
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-text-secondary font-medium">AI 影像分割进行中...</span>
                  <span className="text-text-muted font-heading">{taskProgress}%</span>
                </div>
                <ProgressBar value={taskProgress} size="sm" />
              </div>
            )}

            {/* ---- 上传进度条 ---- */}
            {uploadState === 'uploading' && (
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-text-secondary font-medium">上传中...</span>
                  <span className="text-text-muted font-heading">{uploadProgress}%</span>
                </div>
                <ProgressBar value={uploadProgress} size="sm" />
              </div>
            )}

            {/* ---- 上传成功 ---- */}
            {uploadState === 'success' && uploadedFileData && segState === 'idle' && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-lg text-xs">
                <svg className="w-4 h-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                <span className="text-green-700 font-medium">上传成功</span>
                <span className="text-text-muted ml-auto font-mono text-[10px]">file#{uploadedFileData.id}</span>
              </div>
            )}

            {/* ---- 正在创建分割任务 ---- */}
            {segState === 'creating' && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-xs">
                <svg className="animate-spin h-4 w-4 text-navy-600" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-navy-700 font-medium">正在创建 AI 分割任务...</span>
              </div>
            )}

            {/* ---- 分割任务运行中 ---- */}
            {(segState === 'running' || isRunning) && (
              <div className="space-y-2 px-3 py-2 bg-blue-50/50 border border-blue-100 rounded-lg">
                <div className="flex items-center gap-2 text-xs">
                  <svg className="animate-spin h-4 w-4 text-navy-600" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="font-medium text-navy-700">
                    AI 影像分割进行中
                    {segJobId && <span className="text-text-muted font-mono ml-1">(job:{segJobId})</span>}
                  </span>
                  <span className="ml-auto text-text-muted font-heading">{segProgress}%</span>
                </div>
                <ProgressBar value={segProgress} size="sm" />
                <p className="text-[10px] text-text-muted">{segStage}</p>
              </div>
            )}

            {/* ---- 分割成功 ---- */}
            {segState === 'done' && segResult && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-lg text-xs">
                <svg className="w-4 h-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                <span className="text-green-700 font-medium">AI 分割完成</span>
                <span className="text-text-muted ml-auto">QC: <span className={segResult.quality_control.status === 'passed' ? 'text-green-600' : 'text-gold-600'}>{segResult.quality_control.status}</span></span>
              </div>
            )}

            {/* ---- 分割失败 ---- */}
            {segState === 'failed' && segError && (
              <div className="flex items-start gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs">
                <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <div className="min-w-0">
                  <span className="text-red-700 font-medium">AI 分割失败</span>
                  <p className="text-red-500 mt-0.5 truncate">{segError}</p>
                </div>
                <button onClick={() => { setSegState('idle'); setSegError(null); }}
                  className="text-red-400 hover:text-red-600 shrink-0 text-[10px] font-medium">
                  重试
                </button>
              </div>
            )}

            {/* ---- 上传失败 ---- */}
            {uploadState === 'failed' && uploadError && (
              <div className="flex items-start gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs">
                <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <div className="min-w-0">
                  <span className="text-red-700 font-medium">上传失败</span>
                  <p className="text-red-500 mt-0.5 truncate">{uploadError}</p>
                </div>
                <button onClick={() => { setUploadState('idle'); setUploadError(null); }}
                  className="text-red-400 hover:text-red-600 shrink-0 text-[10px] font-medium">
                  重试
                </button>
              </div>
            )}

            {/* Upload dropzone */}
            <label
              className={`
                upload-dropzone flex items-center gap-4 p-4 cursor-pointer
                ${uploadState === 'success' ? 'border-green-400 bg-green-50/50' : ''}
                ${uploadState === 'failed' ? 'border-red-300 bg-red-50/30' : ''}
              `}
            >
              <input
                type="file"
                className="hidden"
                accept=".nii,.nii.gz,.dcm,.dicom,.zip,.nrrd"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFileSelect(f);
                }}
              />
              <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-navy-700">
                  {uploadedFileName || '上传文件'}
                </p>
                <p className="text-xs text-text-muted mt-0.5">NIfTI、DICOM、NRRD — 拖拽或点击上传</p>
                <div className="flex gap-1.5 mt-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">.nii/.nii.gz</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">.dcm</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">.zip</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">.nrrd</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0 ml-auto">
                {selectedFile && uploadState === 'idle' && (
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleUpload(); }}
                    className="px-3 py-1 rounded text-[11px] font-medium bg-navy-700 text-white hover:bg-navy-800 transition-card"
                  >
                    上传
                  </button>
                )}
                {uploadState === 'success' && segState === 'idle' && (
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleStartSegmentation(); }}
                    className="px-3 py-1 rounded text-[11px] font-medium bg-gold-500 text-navy-950 hover:bg-gold-600 transition-card"
                  >
                    开始 AI 分割
                  </button>
                )}
                {uploadState === 'success' && segState !== 'idle' && (
                  <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                )}
                {uploadState === 'uploading' && (
                  <svg className="animate-spin h-5 w-5 text-navy-600" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
              </div>
            </label>
          </div>

          {/* Body scan illustration */}
          <div className="hidden md:flex items-center justify-center bg-white rounded-xl border border-border p-2 shrink-0" style={{ width: 130 }}>
            <BodyScanIllustration />
          </div>
        </div>
      </div>

      {/* ===== Analysed Body Fat Phenotypes ===== */}
      <div>
        <h4 className="section-title-sm mb-3">已分析脂肪表型</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3">
          {segResult ? [
            { title: '肝脏 PDFF', value: segResult.volume_metrics.liver_pdff_pct.toFixed(1), unit: '%', dice: segResult.dice_scores.liver, color: 'var(--color-blue-500)' },
            { title: '内脏脂肪体积', value: (segResult.volume_metrics.visceral_fat_volume_cm3 / 1000).toFixed(2), unit: 'L', dice: segResult.dice_scores.visceral_fat, color: 'var(--color-teal-600)' },
            { title: '皮下脂肪体积', value: (segResult.volume_metrics.subcutaneous_fat_volume_cm3 / 1000).toFixed(2), unit: 'L', dice: segResult.dice_scores.subcutaneous_fat, color: 'var(--color-green-600)' },
            { title: '骨髓脂肪分数', value: segResult.volume_metrics.bone_marrow_fat_fraction_pct.toFixed(1), unit: '%', dice: segResult.dice_scores.bone_marrow, color: 'var(--color-gold-500)' },
          ].map(({ title, value, unit, dice, color }) => (
            <MiniChartCard
              key={title}
              title={title}
              value={value}
              unit={unit}
              sparkline={[{ v: Number(value) * 0.85 }, { v: Number(value) * 0.92 }, { v: Number(value) }]}
              sparklineColor={color}
              trend="up"
              trendValue={`DICE: ${dice.toFixed(2)}`}
            />
          )) : [
            EMPTY_PHENOTYPE_CARD('肝脏 PDFF', '%'),
            EMPTY_PHENOTYPE_CARD('内脏脂肪体积', 'L'),
            EMPTY_PHENOTYPE_CARD('皮下脂肪体积', 'L'),
            EMPTY_PHENOTYPE_CARD('骨髓脂肪分数', '%'),
          ].map((fp) => (
            <MiniChartCard
              key={fp.title}
              title={fp.title}
              value={fp.value}
              unit={fp.unit}
              sparkline={fp.sparkline}
              sparklineColor={fp.sparklineColor}
              trend={fp.trend}
              trendValue={fp.trendValue}
            />
          ))}
        </div>
      </div>

      {/* ===== Summary ===== */}
      {segResult ? (
        <MetricSummaryCard
          title="分析摘要"
          metrics={[
            { label: '肝脏 DICE', value: segResult.dice_scores.liver.toFixed(2), unit: '', highlight: true },
            { label: '胰腺 DICE', value: segResult.dice_scores.pancreas.toFixed(2), unit: '' },
            { label: '内脏脂肪 DICE', value: segResult.dice_scores.visceral_fat.toFixed(2), unit: '' },
            { label: '皮下脂肪 DICE', value: segResult.dice_scores.subcutaneous_fat.toFixed(2), unit: '' },
            { label: '骨髓 DICE', value: segResult.dice_scores.bone_marrow.toFixed(2), unit: '' },
            { label: 'QC 综合评分', value: segResult.quality_control.overall_quality_score.toFixed(2), unit: '', highlight: true },
            { label: 'SNR', value: segResult.quality_control.snr_estimate_db.toFixed(1), unit: 'dB' },
            { label: '运动伪影', value: segResult.quality_control.motion_artifact_detected ? '有' : '无', unit: '' },
          ]}
          columns={4}
        />
      ) : (
        <MetricSummaryCard
          title="分析摘要"
          metrics={[
            { label: '肝脏 DICE', value: '—', unit: '' },
            { label: '胰腺 DICE', value: '—', unit: '' },
            { label: '内脏脂肪 DICE', value: '—', unit: '' },
            { label: '皮下脂肪 DICE', value: '—', unit: '' },
            { label: '骨髓 DICE', value: '—', unit: '' },
            { label: 'QC 综合评分', value: '—', unit: '' },
            { label: 'SNR', value: '—', unit: 'dB' },
            { label: '运动伪影', value: '—', unit: '' },
          ]}
          columns={4}
        />
      )}

      {/* ===== QC & Warnings ===== */}
      {segResult && segResult.warnings.length > 0 && (
        <div className="space-y-1.5">
          <h4 className="section-title-sm">质量警告</h4>
          {segResult.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2 px-3 py-2 bg-gold-50 border border-gold-200 rounded-lg text-xs text-gold-700">
              <svg className="w-3.5 h-3.5 text-gold-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* ===== Actions ===== */}
      <div className="flex items-center gap-3 pt-1">
        {segState === 'done' && (
          <PrimaryButton variant="gold" onClick={onSaveAndContinue} size="lg">
            保存并继续分析 →
          </PrimaryButton>
        )}
        {segState === 'idle' && uploadState === 'success' && (
          <PrimaryButton variant="primary" onClick={handleStartSegmentation} size="lg">
            开始 AI 影像分割
          </PrimaryButton>
        )}
        {segState === 'idle' && uploadState !== 'success' && (
          <span className="text-xs text-text-muted">
            请先上传 MRI 影像文件
          </span>
        )}
        {segState === 'running' && (
          <span className="text-xs text-navy-600 font-medium flex items-center gap-2">
            <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            AI 分割进行中 — {segProgress}%
          </span>
        )}
        {segState === 'failed' && (
          <div className="flex items-center gap-2">
            <PrimaryButton variant="primary" onClick={handleStartSegmentation} size="md">
              重新开始 AI 分割
            </PrimaryButton>
            <span className="text-xs text-danger-600 font-medium">{segError}</span>
          </div>
        )}
        {isSuccess && segState !== 'done' && imageTask && onViewResult && (
          <SecondaryButton onClick={() => onViewResult(imageTask.id)}>
            查看历史分割结果
          </SecondaryButton>
        )}
      </div>
    </DashboardCard>
  );
}
