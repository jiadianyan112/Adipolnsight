import { useState, useEffect, useRef } from 'react';
import type { AnalysisTask } from '../../types';
import { createAIMRJob, getAIJobStatus, getAIJobResult } from '../../services/aiService';
import type { AIJobFromAPI } from '../../services/aiService';
import DashboardCard from '../shared/DashboardCard';
import StatusBadge from '../shared/StatusBadge';
import ProgressBar from '../shared/ProgressBar';
import SecondaryButton from '../shared/SecondaryButton';
import PrimaryButton from '../shared/PrimaryButton';
import AIInterpretationPanel from '../result/AIInterpretationPanel';
import { Scatter, XAxis, YAxis, ResponsiveContainer, Line, ComposedChart, Cell } from 'recharts';

// ===== Props =====

interface Props {
  mrTask?: AnalysisTask;
  projectId?: number;
  exposureName?: string;
  outcomeName?: string;
  onViewResult?: (taskId: number) => void;
  onRunTask?: (taskType: string) => void;
  onMRComplete?: (data: MRResultData) => void;
}

// ===== Types =====

interface MREstimate {
  method: string;
  beta: number;
  se: number;
  odds_ratio: number;
  ci_lower: number;
  ci_upper: number;
  p_value: number;
  n_snps: number;
}

interface MRHeterogeneity {
  method: string;
  q_statistic: number;
  q_df: number;
  q_pval: number;
}

interface MRPleiotropy {
  egger_intercept: number;
  se: number;
  pval: number;
  interpretation: string;
}

interface ScatterPoint {
  exposure_effect: number;
  outcome_effect: number;
  se: number;
}

interface ForestItem {
  label: string;
  beta: number;
  ci_lower: number;
  ci_upper: number;
  or_label: string;
  p_value: number;
}

interface LeaveOneOutItem {
  snp: string;
  beta: number;
  se: number;
  ci_lower: number;
  ci_upper: number;
}

export interface MRResultData {
  mr_id: string;
  exposure: string;
  outcome: string;
  primary_method: string;
  n_snps: number;
  beta: number;
  se: number;
  p_value: number;
  odds_ratio: number;
  ci_95: [number, number];
  estimates: MREstimate[];
  heterogeneity: MRHeterogeneity[];
  pleiotropy: MRPleiotropy;
  scatter_plot_url: string;
  forest_plot_url: string;
  funnel_plot_url: string;
  leave_one_out_url: string;
  scatter_data_points: ScatterPoint[];
  forest_data: ForestItem[];
  leave_one_out_data: LeaveOneOutItem[];
}

type MRJobState = 'idle' | 'creating' | 'running' | 'done' | 'failed';

// ===== Component =====

export default function MRModule({ mrTask, projectId, exposureName, outcomeName, onViewResult, onRunTask, onMRComplete }: Props) {
  const hasMr = !!(mrTask && mrTask.id);
  const legacyRunning = mrTask?.status === 'running';
  const legacySuccess = mrTask?.status === 'success';

  const [jobState, setJobState] = useState<MRJobState>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MRResultData | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isRunning = legacyRunning || jobState === 'running' || jobState === 'creating';
  const isDone = legacySuccess || jobState === 'done';

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const stopPolling = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  const handleRunMR = async () => {
    if (!projectId) return;
    setJobState('creating');
    setError(null);

    const jobResult = await createAIMRJob(projectId, {
      exposure_trait: exposureName || 'Liver_PDFF',
      outcome_trait: outcomeName || 'Osteoporosis',
      exposure_snps: [],
      outcome_dataset_id: 'ukb-b-12141',
      methods: ['IVW', 'MR-Egger', 'Weighted Median', 'Weighted Mode'],
      clump_r2: 0.001,
      clump_kb: 10000,
      p_threshold: 5e-8,
    });

    if (!jobResult.ok) { setJobState('failed'); setError(jobResult.message); return; }

    setJobState('running');
    setJobId(jobResult.data.job_id);
    setProgress(0);
    setStage('开始执行');

    const jId = jobResult.data.job_id;
    pollRef.current = setInterval(async () => {
      const status = await getAIJobStatus(jId);
      if (!status.ok) { stopPolling(); setJobState('failed'); setError(status.message); return; }
      const j = status.data;
      setProgress(j.progress);
      setStage(j.progress_stage);

      if (j.status === 'succeeded') {
        stopPolling();
        const r = await getAIJobResult(jId);
        if (r.ok && r.data.result) {
          const parsed = r.data.result as MRResultData;
          setResult(parsed);
          setJobState('done');
          setProgress(100);
          onMRComplete?.(parsed);
        } else { setJobState('failed'); setError('结果获取失败'); }
      } else if (j.status === 'failed') {
        stopPolling();
        setJobState('failed');
        setError(j.error_message || 'MR 分析执行失败');
      }
    }, 2000);
  };

  const estimates = result?.estimates || [];
  const scatterPoints = result?.scatter_data_points || [];
  const beta = result?.beta ?? 0;

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <span className="shrink-0 w-7 h-7 rounded-lg bg-navy-700 text-white flex items-center justify-center text-xs font-heading font-bold">3</span>
        <div>
          <h3 className="section-title">分析模块 · 上下文视图</h3>
          <p className="text-xs text-text-muted mt-0.5">B. MR — 孟德尔随机化分析</p>
        </div>
        {result && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-green-50 border border-green-100 text-xs font-heading font-medium text-green-600 ml-auto">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500" />MR 完成
          </span>
        )}
        {isRunning && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-xs font-heading font-medium text-navy-600 ml-auto">
            <span className="w-1.5 h-1.5 rounded-full bg-navy-600 animate-pulse" />MR 运行中
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ===== MR Controls ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">MR 分析参数</h4>
          </div>

          <div className="space-y-2 text-xs text-text-secondary mb-3">
            <div className="flex justify-between py-1 border-b border-border-light">
              <span>暴露</span><span className="font-heading font-semibold text-text-primary">{exposureName || 'Liver_PDFF'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-light">
              <span>结局</span><span className="font-heading font-semibold text-text-primary">{outcomeName || 'Osteoporosis'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-light">
              <span>结局数据集</span><span className="text-text-muted text-[10px]">ukb-b-12141</span>
            </div>
            <div className="flex justify-between py-1">
              <span>方法</span><span className="text-text-muted text-[10px]">IVW, MR-Egger, W-Median, W-Mode</span>
            </div>
          </div>

          {!hasMr && jobState === 'idle' && (
            <PrimaryButton onClick={handleRunMR} className="w-full" size="sm">开始 MR 分析</PrimaryButton>
          )}
          {jobState === 'creating' && (
            <div className="flex items-center gap-2 text-xs text-navy-600"><svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>创建任务中...</div>
          )}
          {hasMr && onRunTask && jobState === 'idle' && (<button onClick={() => onRunTask('mendelian_randomization')} className="text-xs text-navy-600 hover:text-navy-800 font-medium">使用旧版运行 →</button>)}
          {jobState === 'failed' && (<div className="space-y-2"><div className="text-xs text-red-600 bg-red-50 px-3 py-1.5 rounded-lg">{error}</div><PrimaryButton onClick={handleRunMR} className="w-full" size="sm">重试</PrimaryButton></div>)}
          {isDone && result && (
            <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-3 py-1.5 rounded-lg">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              MR 完成 — IVW β={result.beta.toFixed(3)} p={result.p_value.toExponential(1)}
            </div>
          )}
        </DashboardCard>

        {/* ===== Scatter Plot ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">散点图 — SNP 效应</h4>
            {result && <span className="text-xs text-text-muted ml-auto">IVW β = {result.beta.toFixed(3)}</span>}
          </div>
          {isRunning && <ProgressBar value={progress} size="sm" />}

          <div className="bg-surface rounded-lg p-2 mt-2" style={{ height: 220 }}>
            {scatterPoints.length > 0 ? (
              <ResponsiveContainer width="100%" height="85%">
                <ComposedChart margin={{ top: 4, right: 8, bottom: 16, left: 28 }}>
                  <XAxis type="number" dataKey="exposure_effect" domain={['auto', 'auto']} tick={{ fontSize: 8, fill: 'var(--color-text-muted)' }} axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }} />
                  <YAxis type="number" dataKey="outcome_effect" domain={['auto', 'auto']} tick={{ fontSize: 8, fill: 'var(--color-text-muted)' }} axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }} />
                  <Scatter data={scatterPoints} isAnimationActive={false} name="SNPs">
                    {scatterPoints.map((_, i) => (<Cell key={i} fill="var(--color-navy-600)" opacity={0.4} />))}
                  </Scatter>
                  <Line data={[{ exposure_effect: -0.3, outcome_effect: -0.3 * beta }, { exposure_effect: 0.3, outcome_effect: 0.3 * beta }]}
                    dataKey="outcome_effect" stroke="var(--color-danger-600)" strokeWidth={1.5} dot={false} isAnimationActive={false} name="IVW" />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-[10px] text-text-muted">{isRunning ? '分析中...' : '运行 MR 分析以查看散点图'}</div>
            )}
          </div>
        </DashboardCard>
      </div>

      {/* ===== MR Estimates Table ===== */}
      {result && estimates.length > 0 && (
        <DashboardCard padding="md">
          <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">MR 估计值</h4>
          <div className="table-scroll">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-text-muted border-b border-border">
                  <th className="text-left py-1.5 font-medium">方法</th>
                  <th className="text-right py-1.5 font-medium">nSNP</th>
                  <th className="text-right py-1.5 font-medium">β</th>
                  <th className="text-right py-1.5 font-medium">SE</th>
                  <th className="text-right py-1.5 font-medium">OR</th>
                  <th className="text-right py-1.5 font-medium">95% CI</th>
                  <th className="text-right py-1.5 font-medium">P</th>
                </tr>
              </thead>
              <tbody>
                {estimates.map((est) => (
                  <tr key={est.method} className="border-b border-border-light last:border-0">
                    <td className="py-1.5 text-text-secondary font-heading font-semibold">{est.method}</td>
                    <td className="py-1.5 text-right text-text-secondary">{est.n_snps}</td>
                    <td className="py-1.5 text-right font-heading font-semibold text-text-primary">{est.beta.toFixed(3)}</td>
                    <td className="py-1.5 text-right text-text-muted">{est.se.toFixed(3)}</td>
                    <td className="py-1.5 text-right font-heading text-text-primary">{est.odds_ratio.toFixed(2)}</td>
                    <td className="py-1.5 text-right text-text-muted text-[10px]">[{est.ci_lower.toFixed(2)}–{est.ci_upper.toFixed(2)}]</td>
                    <td className={`py-1.5 text-right font-heading font-semibold ${est.p_value < 0.05 ? 'text-green-600' : 'text-text-muted'}`}>{est.p_value.toExponential(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DashboardCard>
      )}

      {/* ===== Sensitivity Analyses ===== */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Heterogeneity */}
          <DashboardCard padding="md">
            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">异质性检验 (Cochran's Q)</h4>
            <div className="table-scroll">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="text-text-muted border-b border-border">
                    <th className="text-left py-1.5 font-medium">方法</th>
                    <th className="text-right py-1.5 font-medium">Q</th>
                    <th className="text-right py-1.5 font-medium">df</th>
                    <th className="text-right py-1.5 font-medium">P</th>
                  </tr>
                </thead>
                <tbody>
                  {result.heterogeneity.map((h) => (
                    <tr key={h.method} className="border-b border-border-light last:border-0">
                      <td className="py-1.5 text-text-secondary font-heading font-semibold">{h.method}</td>
                      <td className="py-1.5 text-right text-text-primary font-heading">{h.q_statistic.toFixed(1)}</td>
                      <td className="py-1.5 text-right text-text-muted">{h.q_df}</td>
                      <td className={`py-1.5 text-right font-heading ${h.q_pval < 0.05 ? 'text-gold-600 font-semibold' : 'text-text-muted'}`}>{h.q_pval.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </DashboardCard>

          {/* Pleiotropy */}
          <DashboardCard padding="md">
            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">水平多效性检验 (MR-Egger Intercept)</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-surface rounded-lg p-2.5"><p className="text-text-muted">Intercept</p><p className="font-heading font-bold text-text-primary mt-0.5">{result.pleiotropy.egger_intercept.toFixed(5)}</p></div>
              <div className="bg-surface rounded-lg p-2.5"><p className="text-text-muted">SE</p><p className="font-heading font-bold text-text-primary mt-0.5">{result.pleiotropy.se.toFixed(5)}</p></div>
              <div className="bg-surface rounded-lg p-2.5"><p className="text-text-muted">P value</p><p className={`font-heading font-bold mt-0.5 ${result.pleiotropy.pval > 0.05 ? 'text-green-600' : 'text-gold-600'}`}>{result.pleiotropy.pval.toFixed(3)}</p></div>
              <div className="bg-surface rounded-lg p-2.5"><p className="text-text-muted">解读</p><p className="font-heading font-bold text-text-primary mt-0.5 text-[10px]">{result.pleiotropy.interpretation}</p></div>
            </div>
          </DashboardCard>
        </div>
      )}

      {/* ===== Forest Plot + Leave-one-out Placeholders ===== */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Forest Plot Placeholder */}
          <DashboardCard padding="md">
            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">森林图</h4>
            <div className="aspect-[4/3] bg-surface-alt rounded-xl border border-border flex flex-col items-center justify-center gap-2">
              <svg className="w-8 h-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v17.25M9 6.75h10.5M9 12h7.5M9 17.25h4.5" />
              </svg>
              <span className="text-[10px] text-text-muted">森林图 (Forest Plot)</span>
              <span className="text-[9px] text-text-muted">运行真实 TwoSampleMR 后生成</span>
              <div className="mt-2 space-y-1 w-48">
                {result.forest_data.slice(0, 5).map((f) => (
                  <div key={f.label} className="flex items-center gap-2 px-2 text-[10px]">
                    <span className="w-16 text-right text-text-secondary font-heading">{f.label}</span>
                    <div className="flex-1 h-2 bg-surface-alt rounded-full relative">
                      <div className="absolute inset-y-0 bg-navy-600/20 rounded-full" style={{ left: '20%', right: '20%' }} />
                      <div className="absolute top-0 h-2 w-1 bg-navy-600 rounded" style={{ left: '50%' }} />
                    </div>
                    <span className="w-20 text-left text-text-muted font-mono">{f.or_label}</span>
                  </div>
                ))}
              </div>
            </div>
          </DashboardCard>

          {/* Leave-one-out Placeholder */}
          <DashboardCard padding="md">
            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">Leave-one-out 分析</h4>
            <div className="aspect-[4/3] bg-surface-alt rounded-xl border border-border flex flex-col items-center justify-center gap-2">
              <svg className="w-8 h-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3l-1.5 15M15 3h5.25A2.25 2.25 0 0122.5 5.25v13.5A2.25 2.25 0 0120.25 21H15M15 3l1.5 15" />
              </svg>
              <span className="text-[10px] text-text-muted">Leave-one-out 分析</span>
              <span className="text-[9px] text-text-muted">运行真实 TwoSampleMR 后生成</span>
              <span className="text-[10px] text-text-secondary font-heading mt-1">IVW β = {result.beta.toFixed(3)} (all SNPs)</span>
            </div>
          </DashboardCard>
        </div>
      )}

      {/* ===== AI Interpretation ===== */}
      {result && projectId && (
        <AIInterpretationPanel
          jobType="mr"
          resultData={result as unknown as Record<string, unknown>}
          projectId={projectId}
          sourceJobId={jobId || undefined}
        />
      )}
    </div>
  );
}
