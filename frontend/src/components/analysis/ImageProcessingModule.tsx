import { useState } from 'react';
import type { AnalysisTask } from '../../types';
import DashboardCard from '../shared/DashboardCard';
import ProgressBar from '../shared/ProgressBar';
import MiniChartCard from '../shared/MiniChartCard';
import MetricSummaryCard from '../shared/MetricSummaryCard';
import PrimaryButton from '../shared/PrimaryButton';
import SecondaryButton from '../shared/SecondaryButton';
import StatusBadge from '../shared/StatusBadge';

interface Props {
  imageTask?: AnalysisTask;
  onViewResult?: (taskId: number) => void;
  onSaveAndContinue?: () => void;
}

const PHENOTYPE_DATA = [
  {
    title: '肝脏脂肪分数',
    value: '12.4',
    unit: '%',
    trend: 'up' as const,
    trendValue: '+2.1% 相对基线',
    sparkline: [
      { v: 8.2 }, { v: 9.1 }, { v: 9.8 }, { v: 10.5 }, { v: 11.0 },
      { v: 11.3 }, { v: 11.7 }, { v: 12.0 }, { v: 12.2 }, { v: 12.4 },
    ],
    sparklineColor: 'var(--color-blue-500)',
  },
  {
    title: '胰腺脂肪分数',
    value: '8.7',
    unit: '%',
    trend: 'stable' as const,
    trendValue: '±0.3% 波动范围',
    sparkline: [
      { v: 8.5 }, { v: 8.8 }, { v: 8.6 }, { v: 8.9 }, { v: 8.7 },
      { v: 8.5 }, { v: 8.8 }, { v: 8.6 }, { v: 8.9 }, { v: 8.7 },
    ],
    sparklineColor: 'var(--color-teal-600)',
  },
  {
    title: '肾周脂肪',
    value: '245',
    unit: 'cm³',
    trend: 'down' as const,
    trendValue: '-4.2 cm³ 相对基线',
    sparkline: [
      { v: 258 }, { v: 255 }, { v: 253 }, { v: 251 }, { v: 249 },
      { v: 248 }, { v: 247 }, { v: 246 }, { v: 245 }, { v: 245 },
    ],
    sparklineColor: 'var(--color-green-600)',
  },
  {
    title: '骨髓脂肪分数',
    value: '68.2',
    unit: '%',
    trend: 'up' as const,
    trendValue: '+4.5% 相对基线',
    sparkline: [
      { v: 60.1 }, { v: 61.5 }, { v: 63.0 }, { v: 64.2 }, { v: 65.3 },
      { v: 66.1 }, { v: 66.8 }, { v: 67.4 }, { v: 67.9 }, { v: 68.2 },
    ],
    sparklineColor: 'var(--color-gold-500)',
  },
];

const SUMMARY_METRICS = [
  { label: '全身脂肪', value: '32.5', unit: '%', highlight: true },
  { label: '内脏脂肪', value: '2.84', unit: 'L' },
  { label: '皮下脂肪', value: '8.12', unit: 'L' },
  { label: '肌肉体积', value: '24.7', unit: 'L' },
  { label: '肝脏 PDFF', value: '12.4', unit: '%' },
  { label: '胰腺 PDFF', value: '8.7', unit: '%' },
  { label: '骨密度', value: '1.24', unit: 'g/cm²' },
  { label: 'SAT/VAT 比值', value: '2.86', unit: '' },
];

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

export default function ImageProcessingModule({ imageTask, onViewResult, onSaveAndContinue }: Props) {
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);

  const isRunning = imageTask?.status === 'running';
  const isSuccess = imageTask?.status === 'success';
  const taskProgress = imageTask?.progress ?? 0;

  const handleFileSelect = (file: File) => {
    setUploadedFile(file.name);
    setUploadProgress(0);
    // Simulate upload progress
    let p = 0;
    const iv = setInterval(() => {
      p += Math.random() * 15 + 5;
      if (p >= 100) { p = 100; clearInterval(iv); }
      setUploadProgress(Math.min(100, Math.round(p)));
    }, 200);
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
            {/* Progress bar area */}
            {(isRunning || uploadProgress !== null) && (
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-text-secondary font-medium">
                    {isRunning ? 'AI 影像分割进行中...' : '上传中...'}
                  </span>
                  <span className="text-text-muted font-heading">
                    {isRunning ? `${taskProgress}%` : `${uploadProgress}%`}
                  </span>
                </div>
                <ProgressBar value={isRunning ? taskProgress : uploadProgress ?? 0} size="sm" />
              </div>
            )}

            {/* Upload dropzone */}
            <label
              className={`
                upload-dropzone flex items-center gap-4 p-4 cursor-pointer
                ${uploadedFile ? 'border-green-400 bg-green-50/50' : ''}
              `}
            >
              <input type="file" className="hidden" onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFileSelect(f);
              }} />
              <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-navy-700">
                  {uploadedFile || '上传文件'}
                </p>
                <p className="text-xs text-text-muted mt-0.5">NIfTI、DICOM — 拖拽或点击上传</p>
                <div className="flex gap-1.5 mt-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">DICOM</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">NIfTI</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">JPG/PNG</span>
                </div>
              </div>
              {uploadedFile && (
                <svg className="w-5 h-5 text-green-500 shrink-0 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              )}
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
          {PHENOTYPE_DATA.map((fp) => (
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
      <MetricSummaryCard
        title="分析摘要"
        metrics={SUMMARY_METRICS}
        columns={4}
      />

      {/* ===== Actions ===== */}
      <div className="flex items-center gap-3 pt-1">
        <PrimaryButton variant="gold" onClick={onSaveAndContinue} size="lg">
          保存并继续分析 →
        </PrimaryButton>
        {isSuccess && imageTask && onViewResult && (
          <SecondaryButton onClick={() => onViewResult(imageTask.id)}>
            查看影像分割结果
          </SecondaryButton>
        )}
        {!isSuccess && imageTask && (
          <span className="text-xs text-text-muted">
            AI 影像分割状态：<span className="font-medium text-text-secondary">{imageTask.status}</span>
          </span>
        )}
      </div>
    </DashboardCard>
  );
}
