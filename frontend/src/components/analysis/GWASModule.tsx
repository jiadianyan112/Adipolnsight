import { useState, useEffect, useRef } from 'react';
import type { AnalysisTask } from '../../types';
import { createAIGWASJob, getAIJobStatus, getAIJobResult } from '../../services/aiService';
import type { AIJobFromAPI } from '../../services/aiService';
import DashboardCard from '../shared/DashboardCard';
import StatusBadge from '../shared/StatusBadge';
import ProgressBar from '../shared/ProgressBar';
import SecondaryButton from '../shared/SecondaryButton';
import PrimaryButton from '../shared/PrimaryButton';
import { ScatterChart, Scatter, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';

// ===== Props =====

interface Props {
  gwasTask?: AnalysisTask;
  opengwasTask?: AnalysisTask;
  projectId?: number;
  phenotypeName?: string;
  onViewResult?: (taskId: number) => void;
  onRunTask?: (taskType: string) => void;
  onGWASComplete?: (data: GWASResultData) => void;
}

// ===== Types =====

interface ManhattanPoint { chr: number; pos: number; neg_log10_p: number; }
interface QQPoint { expected: number; observed: number; }
interface LeadSNP { snp: string; chr: number; bp: number; ea: string; oa: string; eaf: number; beta: number; se: number; p_value: number; neg_log10_p: number; }
interface SignificantLocus { locus_id: number; chr: number; start: number; end: number; lead_snp: string; n_snps: number; min_pvalue: number; }

export interface GWASResultData {
  gwas_id: string;
  phenotype: string;
  method: string;
  population: string;
  sample_size: number;
  lambda_gc: number;
  significant_loci_count: number;
  lead_snps_count: number;
  significant_loci: SignificantLocus[];
  lead_snps: LeadSNP[];
  manhattan_plot_url: string;
  qq_plot_url: string;
  manhattan_data_points: ManhattanPoint[];
  qq_data_points: QQPoint[];
}

type GWASJobState = 'idle' | 'creating' | 'running' | 'done' | 'failed';

const SIG_THRESHOLD = -Math.log10(5e-8);

// ===== Component =====

export default function GWASModule({ gwasTask, opengwasTask, projectId, phenotypeName, onViewResult, onRunTask, onGWASComplete }: Props) {
  // Legacy task state
  const hasGwas = !!(gwasTask && gwasTask.id);
  const legacyRunning = gwasTask?.status === 'running';
  const legacySuccess = gwasTask?.status === 'success';

  // New AI job state
  const [jobState, setJobState] = useState<GWASJobState>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GWASResultData | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isRunning = legacyRunning || jobState === 'running' || jobState === 'creating';
  const isDone = legacySuccess || jobState === 'done';

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const stopPolling = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  const handleRunGWAS = async () => {
    if (!projectId) return;
    setJobState('creating');
    setError(null);

    const jobResult = await createAIGWASJob(projectId, {
      phenotype_name: phenotypeName || 'Liver_PDFF',
      phenotype_id: phenotypeName || 'Liver_PDFF',
      covariates: ['age', 'sex', 'bmi', 'PC1', 'PC2', 'PC3', 'PC4', 'PC5', 'PC6', 'PC7', 'PC8', 'PC9', 'PC10'],
      population_filter: 'EUR',
      method: 'REGENIE',
      maf_threshold: 0.01,
      hwe_threshold: 1e-6,
      qc_options: { impute_missing: true, remove_outliers: true, normalize_phenotype: true },
    });

    if (!jobResult.ok) {
      setJobState('failed');
      setError(jobResult.message);
      return;
    }

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
          const parsed = r.data.result as GWASResultData;
          setResult(parsed);
          setJobState('done');
          setProgress(100);
          onGWASComplete?.(parsed);
        } else {
          setJobState('failed');
          setError('结果获取失败');
        }
      } else if (j.status === 'failed') {
        stopPolling();
        setJobState('failed');
        setError(j.error_message || 'GWAS 分析执行失败');
      }
    }, 2000);
  };

  // Use backend manhattan data if available, otherwise empty
  const manhattanData = result?.manhattan_data_points || [];
  const leadSnps = result?.lead_snps || [];
  const stats = result ? {
    total: result.sample_size.toLocaleString(),
    loci: String(result.significant_loci_count),
    lead: String(result.lead_snps_count),
  } : {
    total: isDone ? '—' : '—',
    loci: isDone ? '—' : '—',
    lead: isDone ? '—' : '—',
  };

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <span className="shrink-0 w-7 h-7 rounded-lg bg-navy-700 text-white flex items-center justify-center text-xs font-heading font-bold">
          3
        </span>
        <div>
          <h3 className="section-title">分析模块 · 上下文视图</h3>
          <p className="text-xs text-text-muted mt-0.5">A. GWAS — 全基因组关联分析</p>
        </div>
        {result && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-green-50 border border-green-100 text-xs font-heading font-medium text-green-600 ml-auto">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
            GWAS 完成
          </span>
        )}
        {isRunning && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-xs font-heading font-medium text-navy-600 ml-auto">
            <span className="w-1.5 h-1.5 rounded-full bg-navy-600 animate-pulse" />
            GWAS 运行中
          </span>
        )}
      </div>

      {/* Two sub-cards side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ===== GWAS Controls ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">GWAS 分析参数</h4>
          </div>

          <div className="space-y-2 text-xs text-text-secondary mb-3">
            <div className="flex justify-between py-1 border-b border-border-light">
              <span>分析方法</span><span className="font-heading font-semibold text-text-primary">REGENIE</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-light">
              <span>表型</span><span className="font-heading font-semibold text-text-primary">{phenotypeName || 'Liver_PDFF'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-light">
              <span>人群</span><span className="font-heading text-text-primary">EUR</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-light">
              <span>协变量</span><span className="text-text-muted text-[10px]">age, sex, bmi, PC1–10</span>
            </div>
            <div className="flex justify-between py-1">
              <span>QC</span><span className="text-text-muted text-[10px]">MAF≥0.01, HWE≥1e-6</span>
            </div>
          </div>

          {/* Action */}
          {!hasGwas && jobState === 'idle' && (
            <PrimaryButton onClick={handleRunGWAS} className="w-full" size="sm">
              开始 GWAS 分析
            </PrimaryButton>
          )}
          {jobState === 'creating' && (
            <div className="flex items-center gap-2 text-xs text-navy-600">
              <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              创建任务中...
            </div>
          )}
          {hasGwas && onRunTask && jobState === 'idle' && (
            <button onClick={() => onRunTask('gwas_analysis')} className="text-xs text-navy-600 hover:text-navy-800 font-medium">
              使用旧版运行 →
            </button>
          )}
          {jobState === 'failed' && (
            <div className="space-y-2">
              <div className="text-xs text-red-600 bg-red-50 px-3 py-1.5 rounded-lg">{error}</div>
              <PrimaryButton onClick={handleRunGWAS} className="w-full" size="sm">重试</PrimaryButton>
            </div>
          )}
          {isDone && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-3 py-1.5 rounded-lg">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                GWAS 分析完成 — {result?.sample_size?.toLocaleString()} 样本
              </div>
            </div>
          )}
        </DashboardCard>

        {/* ===== Manhattan Plot ===== */}
        <DashboardCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
            <h4 className="font-heading font-semibold text-sm text-text-primary">Manhattan 图</h4>
            {isRunning && <span className="text-xs text-text-muted ml-auto">{progress}%</span>}
            {result && <span className="text-xs text-text-muted ml-auto">λ = {result.lambda_gc.toFixed(2)}</span>}
          </div>

          {isRunning && <ProgressBar value={progress} size="sm" />}
          {jobState === 'running' && <p className="text-[10px] text-text-muted mt-1">{stage}</p>}

          <div className="bg-surface rounded-lg p-2 mt-2" style={{ height: 220 }}>
            <div className="flex items-center justify-between mb-1 px-1">
              <span className="text-[10px] text-text-muted font-medium">曼哈顿图 — {manhattanData.length > 0 ? '后端数据' : '等待分析'}</span>
              {result && <span className="text-[10px] text-text-muted">λ = {result.lambda_gc.toFixed(2)}</span>}
            </div>
            {manhattanData.length > 0 ? (
              <ResponsiveContainer width="100%" height="85%">
                <ScatterChart margin={{ top: 4, right: 8, bottom: 16, left: 28 }}>
                  <XAxis type="number" dataKey="pos" domain={[0, 'auto']} tick={false}
                    axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }} />
                  <YAxis type="number" dataKey="neg_log10_p" domain={[0, 'auto']}
                    tick={{ fontSize: 8, fill: 'var(--color-text-muted)' }}
                    axisLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }}
                    label={{ value: '-log₁₀(p)', angle: -90, position: 'left', offset: -2, style: { fontSize: 9, fill: 'var(--color-text-muted)' } }} />
                  <Scatter data={manhattanData} isAnimationActive={false}>
                    {manhattanData.map((d, i) => (
                      <Cell key={i} fill={d.neg_log10_p > SIG_THRESHOLD ? 'var(--color-danger-600)' : d.neg_log10_p > 5 ? 'var(--color-blue-500)' : 'var(--color-navy-600)'}
                        opacity={d.neg_log10_p > SIG_THRESHOLD ? 0.9 : d.neg_log10_p > 5 ? 0.5 : 0.2} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-[10px] text-text-muted">
                {isRunning ? '分析中...' : '运行 GWAS 分析以查看曼哈顿图'}
              </div>
            )}
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-3 gap-2 mt-3">
            {[
              { label: '样本量', value: stats.total },
              { label: '显著位点', value: stats.loci },
              { label: '先导 SNP', value: stats.lead },
            ].map((s) => (
              <div key={s.label} className="bg-surface rounded-lg p-2 text-center">
                <p className="text-[10px] text-text-muted">{s.label}</p>
                <p className="text-sm font-heading font-bold text-text-primary">{s.value}</p>
              </div>
            ))}
          </div>
        </DashboardCard>
      </div>

      {/* ===== Lead SNPs table ===== */}
      {result && leadSnps.length > 0 && (
        <DashboardCard padding="md">
          <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">
            先导 SNP — {leadSnps.length} 个 (p &lt; 5×10⁻⁸)
          </h4>
          <div className="table-scroll">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-text-muted border-b border-border">
                  <th className="text-left py-1.5 font-medium">SNP</th>
                  <th className="text-right py-1.5 font-medium">Chr</th>
                  <th className="text-right py-1.5 font-medium">BP</th>
                  <th className="text-right py-1.5 font-medium">EA/OA</th>
                  <th className="text-right py-1.5 font-medium">EAF</th>
                  <th className="text-right py-1.5 font-medium">Beta</th>
                  <th className="text-right py-1.5 font-medium">P</th>
                </tr>
              </thead>
              <tbody>
                {leadSnps.slice(0, 10).map((snp) => (
                  <tr key={snp.snp} className="border-b border-border-light last:border-0">
                    <td className="py-1.5 font-mono text-text-primary">{snp.snp}</td>
                    <td className="py-1.5 text-right text-text-secondary">{snp.chr}</td>
                    <td className="py-1.5 text-right text-text-muted text-[10px]">{(snp.bp / 1e6).toFixed(1)}M</td>
                    <td className="py-1.5 text-right font-mono text-text-secondary">{snp.ea}/{snp.oa}</td>
                    <td className="py-1.5 text-right text-text-secondary">{snp.eaf.toFixed(2)}</td>
                    <td className="py-1.5 text-right font-heading font-semibold text-text-primary">{snp.beta.toFixed(3)}</td>
                    <td className="py-1.5 text-right font-heading font-semibold text-green-600">{snp.p_value.toExponential(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DashboardCard>
      )}
    </div>
  );
}
