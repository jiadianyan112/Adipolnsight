import type { AnalysisTask } from '../../types';
import DashboardCard from '../shared/DashboardCard';
import StatusBadge from '../shared/StatusBadge';
import ProgressBar from '../shared/ProgressBar';
import SecondaryButton from '../shared/SecondaryButton';
import { ScatterChart, Scatter, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';

interface Props {
  gwasTask?: AnalysisTask;
  opengwasTask?: AnalysisTask;
  onViewResult?: (taskId: number) => void;
  onRunTask?: (taskType: string) => void;
}

// Generate mock Manhattan plot data — points clustered along chromosomes
function generateManhattanData() {
  const data: { chr: number; pos: number; pval: number }[] = [];
  const chrSizes = [250, 240, 200, 190, 180, 170, 160, 150, 140, 140, 135, 135,
    115, 110, 105, 100, 95, 80, 65, 55, 45, 50];
  for (let chr = 0; chr < 22; chr++) {
    const n = chrSizes[chr];
    for (let i = 0; i < n; i++) {
      const basePos = chr * 12 + (i / n) * 10;
      let pval = -Math.log10(Math.random() * 0.8 + 0.01);
      // Create some significant peaks
      if (i === Math.floor(n * 0.3) && chr % 3 === 0) pval = 7 + Math.random() * 3;
      if (i === Math.floor(n * 0.7) && chr % 4 === 1) pval = 5 + Math.random() * 3;
      if (i === Math.floor(n * 0.5) && chr === 5) pval = 9 + Math.random() * 2;
      data.push({ chr, pos: basePos, pval });
    }
  }
  return data;
}

const MANHATTAN_DATA = generateManhattanData();
const SIG_THRESHOLD = -Math.log10(5e-8); // ~7.3

export default function GWASModule({ gwasTask, opengwasTask, onViewResult, onRunTask }: Props) {
  const hasGwas = gwasTask && gwasTask.id;
  const gwasRunning = gwasTask?.status === 'running';
  const gwasSuccess = gwasTask?.status === 'success';

  const hasOpenGwas = opengwasTask && opengwasTask.id;
  const opengwasSuccess = opengwasTask?.status === 'success';

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <span className="shrink-0 w-7 h-7 rounded-lg bg-navy-700 text-white flex items-center justify-center text-xs font-heading font-bold">
          3
        </span>
        <div>
          <h3 className="section-title">分析模块 · 上下文视图</h3>
          <p className="text-xs text-text-muted mt-0.5">
            A. GWAS — 全基因组关联分析
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-xs font-heading font-medium text-navy-600 ml-auto">
          <span className="w-1.5 h-1.5 rounded-full bg-navy-600" />
          GWAS 进行中
        </span>
      </div>

      {/* Two sub-cards side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ===== Upload Genomic Data ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">上传基因组数据</h4>
          </div>

          <label className="upload-dropzone flex flex-col items-center justify-center gap-2 p-5 text-center cursor-pointer mb-3">
            <input type="file" className="hidden" />
            <div className="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center">
              <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m0 0l6.75-6.75M12 19.5l-6.75-6.75" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-navy-700">上传基因组数据</p>
              <p className="text-xs text-text-muted mt-0.5">支持 PLINK / VCF / BED 格式</p>
            </div>
          </label>

          {/* GWAS + OpenGWAS task status */}
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2.5 bg-surface rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-text-secondary">GWAS 分析</span>
                {gwasTask && <StatusBadge status={gwasTask.status} />}
              </div>
              <div className="flex items-center gap-2">
                {!hasGwas && onRunTask && (
                  <button onClick={() => onRunTask('gwas_analysis')} className="text-xs text-navy-600 hover:text-navy-800 font-medium">
                    运行 →
                  </button>
                )}
                {gwasSuccess && onViewResult && (
                  <SecondaryButton size="sm" onClick={() => onViewResult(gwasTask!.id)}>查看结果</SecondaryButton>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-surface rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-text-secondary">OpenGWAS 数据获取</span>
                {opengwasTask && <StatusBadge status={opengwasTask.status} />}
              </div>
              <div className="flex items-center gap-2">
                {!hasOpenGwas && onRunTask && (
                  <button onClick={() => onRunTask('opengwas_fetch')} className="text-xs text-navy-600 hover:text-navy-800 font-medium">
                    获取 →
                  </button>
                )}
                {opengwasSuccess && onViewResult && (
                  <SecondaryButton size="sm" onClick={() => onViewResult(opengwasTask!.id)}>查看结果</SecondaryButton>
                )}
              </div>
            </div>
          </div>
        </DashboardCard>

        {/* ===== GWAS 分析进度 ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">GWAS 分析进度</h4>
            {gwasRunning && <span className="text-xs text-text-muted ml-auto">{gwasTask?.progress || 0}%</span>}
          </div>

          {gwasRunning && <ProgressBar value={gwasTask?.progress || 0} size="sm" />}

          {/* Manhattan Plot */}
          <div className="bg-surface rounded-lg p-2 mt-2" style={{ height: 220 }}>
            <div className="flex items-center justify-between mb-1 px-1">
              <span className="text-[10px] text-text-muted font-medium">曼哈顿图 — 预览</span>
              <span className="text-[10px] text-text-muted">
                λ = 1.02
              </span>
            </div>
            <ResponsiveContainer width="100%" height="85%">
              <ScatterChart margin={{ top: 4, right: 8, bottom: 16, left: 28 }}>
                <XAxis
                  type="number"
                  dataKey="pos"
                  domain={[0, 265]}
                  tick={false}
                  axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }}
                  label={{ value: 'Chromosome', position: 'bottom', offset: 2, style: { fontSize: 9, fill: 'var(--color-text-muted)' } }}
                />
                <YAxis
                  type="number"
                  dataKey="pval"
                  domain={[0, 12]}
                  tick={{ fontSize: 8, fill: 'var(--color-text-muted)' }}
                  axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }}
                  label={{ value: '-log₁₀(p)', angle: -90, position: 'left', offset: -2, style: { fontSize: 9, fill: 'var(--color-text-muted)' } }}
                />
                <Scatter data={MANHATTAN_DATA} isAnimationActive={false}>
                  {MANHATTAN_DATA.map((d, i) => {
                    const significant = d.pval > SIG_THRESHOLD;
                    const top = d.pval > 7;
                    return (
                      <Cell
                        key={i}
                        fill={top ? 'var(--color-danger-600)' : significant ? 'var(--color-blue-500)' : 'var(--color-navy-600)'}
                        opacity={top ? 0.9 : significant ? 0.5 : 0.2}
                      />
                    );
                  })}
                </Scatter>
                {/* Significance line would go here — Recharts ReferenceLine equivalent */}
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-3 gap-2 mt-3">
            {[
              { label: 'SNP 总数', value: '4,528' },
              { label: '显著位点', value: gwasSuccess ? '12' : '—' },
              { label: '先导 SNP', value: gwasSuccess ? '7' : '—' },
            ].map((s) => (
              <div key={s.label} className="bg-surface rounded-lg p-2 text-center">
                <p className="text-[10px] text-text-muted">{s.label}</p>
                <p className="text-sm font-heading font-bold text-text-primary">{s.value}</p>
              </div>
            ))}
          </div>
        </DashboardCard>
      </div>
    </div>
  );
}
