import type { AnalysisTask } from '../../types';
import DashboardCard from '../shared/DashboardCard';
import StatusBadge from '../shared/StatusBadge';
import ProgressBar from '../shared/ProgressBar';
import SecondaryButton from '../shared/SecondaryButton';
import { Scatter, XAxis, YAxis, ResponsiveContainer, Line, ComposedChart, Cell } from 'recharts';

interface Props {
  mrTask?: AnalysisTask;
  onViewResult?: (taskId: number) => void;
  onRunTask?: (taskType: string) => void;
}

// Generate mock MR scatter data — SNP-exposure vs SNP-outcome effects
function generateMRData() {
  const data: { exposure: number; outcome: number; se: number }[] = [];
  const beta = 0.38; // causal effect slope
  for (let i = 0; i < 80; i++) {
    const exposure = (Math.random() - 0.5) * 0.6;
    const outcome = exposure * beta + (Math.random() - 0.5) * 0.15;
    const se = 0.02 + Math.random() * 0.06;
    data.push({ exposure, outcome, se });
  }
  return data;
}

const MR_SCATTER_DATA = generateMRData();

const IVW_LINE = [
  { exposure: -0.3, outcome: -0.3 * 0.38 },
  { exposure: 0.3, outcome: 0.3 * 0.38 },
];

const MR_ESTIMATES = [
  { method: 'IVW', beta: 0.38, ciLow: 0.21, ciHigh: 0.55, pval: '0.004' },
  { method: 'Weighted Median', beta: 0.34, ciLow: 0.15, ciHigh: 0.52, pval: '0.018' },
  { method: 'MR-Egger', beta: 0.42, ciLow: -0.04, ciHigh: 0.88, pval: '0.072' },
  { method: 'Weighted Mode', beta: 0.36, ciLow: 0.18, ciHigh: 0.54, pval: '0.009' },
];

export default function MRModule({ mrTask, onViewResult, onRunTask }: Props) {
  const hasMr = mrTask && mrTask.id;
  const mrRunning = mrTask?.status === 'running';
  const mrSuccess = mrTask?.status === 'success';

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
            B. MR — 孟德尔随机化分析
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-xs font-heading font-medium text-navy-600 ml-auto">
          <span className="w-1.5 h-1.5 rounded-full bg-navy-600" />
          MR 进行中
        </span>
      </div>

      {/* Two sub-cards side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ===== 上传结局数据 ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">上传结局数据</h4>
          </div>

          <label className="upload-dropzone flex flex-col items-center justify-center gap-2 p-5 text-center cursor-pointer mb-3">
            <input type="file" className="hidden" />
            <div className="w-9 h-9 rounded-full bg-teal-50 flex items-center justify-center">
              <svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m0 0l6.75-6.75M12 19.5l-6.75-6.75" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-navy-700">上传结局数据</p>
              <p className="text-xs text-text-muted mt-0.5">
                结局性状的 GWAS 汇总统计数据
              </p>
            </div>
            <div className="flex gap-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">.tsv</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">.csv</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white border border-border text-text-secondary">OpenGWAS ID</span>
            </div>
          </label>

          {/* MR task status + download link */}
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2.5 bg-surface rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-text-secondary">MR 分析</span>
                {mrTask && <StatusBadge status={mrTask.status} />}
              </div>
              <div className="flex items-center gap-2">
                {!hasMr && onRunTask && (
                  <button onClick={() => onRunTask('mendelian_randomization')} className="text-xs text-navy-600 hover:text-navy-800 font-medium">
                    运行 →
                  </button>
                )}
                {mrSuccess && onViewResult && (
                  <SecondaryButton size="sm" onClick={() => onViewResult(mrTask!.id)}>查看结果</SecondaryButton>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-surface rounded-lg">
              <span className="text-xs font-medium text-text-secondary">下载示例结局数据</span>
              <a href="#" className="text-xs text-teal-600 hover:text-teal-800 font-medium" onClick={(e) => e.preventDefault()}>
                下载 →
              </a>
            </div>
          </div>
        </DashboardCard>

        {/* ===== MR 分析 Progress ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">MR 分析 Progress</h4>
            {mrRunning && <span className="text-xs text-text-muted ml-auto">{mrTask?.progress || 0}%</span>}
          </div>

          {mrRunning && <ProgressBar value={mrTask?.progress || 0} size="sm" />}

          {/* MR Scatter Plot */}
          <div className="bg-surface rounded-lg p-2 mt-2" style={{ height: 220 }}>
            <div className="flex items-center justify-between mb-1 px-1">
              <span className="text-[10px] text-text-muted font-medium">散点图 — SNP 效应</span>
              <span className="text-[10px] text-text-muted">
                IVW β = 0.38
              </span>
            </div>
            <ResponsiveContainer width="100%" height="85%">
              <ComposedChart margin={{ top: 4, right: 8, bottom: 16, left: 28 }}>
                <XAxis
                  type="number"
                  dataKey="exposure"
                  domain={[-0.35, 0.35]}
                  tick={{ fontSize: 8, fill: 'var(--color-text-muted)' }}
                  axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }}
                  label={{ value: 'SNP-暴露效应', position: 'bottom', offset: 2, style: { fontSize: 9, fill: 'var(--color-text-muted)' } }}
                />
                <YAxis
                  type="number"
                  dataKey="outcome"
                  domain={[-0.2, 0.2]}
                  tick={{ fontSize: 8, fill: 'var(--color-text-muted)' }}
                  axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }}
                  label={{ value: 'SNP-结局效应', angle: -90, position: 'left', offset: -2, style: { fontSize: 9, fill: 'var(--color-text-muted)' } }}
                />
                <Scatter data={MR_SCATTER_DATA} isAnimationActive={false} name="SNPs">
                  {MR_SCATTER_DATA.map((_, i) => (
                    <Cell key={i} fill="var(--color-navy-600)" opacity={0.4} />
                  ))}
                </Scatter>
                <Line
                  data={IVW_LINE}
                  dataKey="outcome"
                  stroke="var(--color-danger-600)"
                  strokeWidth={1.5}
                  dot={false}
                  isAnimationActive={false}
                  name="IVW"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* MR Estimates table */}
          <div className="mt-3 table-scroll">
            <table className="w-full text-[11px]" aria-label="MR estimates table">
              <thead>
                <tr className="text-text-muted border-b border-border">
                  <th className="text-left py-1.5 font-medium">方法</th>
                  <th className="text-right py-1.5 font-medium">β</th>
                  <th className="text-right py-1.5 font-medium">95% CI</th>
                  <th className="text-right py-1.5 font-medium">P</th>
                </tr>
              </thead>
              <tbody>
                {MR_ESTIMATES.map((row) => (
                  <tr key={row.method} className="border-b border-border-light last:border-0">
                    <td className="py-1.5 text-text-secondary font-medium">{row.method}</td>
                    <td className="py-1.5 text-right font-heading font-semibold text-text-primary">{row.beta.toFixed(2)}</td>
                    <td className="py-1.5 text-right text-text-muted">[{row.ciLow.toFixed(2)}, {row.ciHigh.toFixed(2)}]</td>
                    <td className={`py-1.5 text-right font-heading font-semibold ${Number(row.pval) < 0.05 ? 'text-green-600' : 'text-text-muted'}`}>
                      {row.pval}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DashboardCard>
      </div>
    </div>
  );
}
