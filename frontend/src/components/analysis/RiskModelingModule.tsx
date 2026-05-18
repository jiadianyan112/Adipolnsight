import { useState, useEffect, useRef } from 'react';
import type { AnalysisTask } from '../../types';
import { createAIRiskModelingJob, getAIJobStatus, getAIJobResult } from '../../services/aiService';
import type { AIJobFromAPI } from '../../services/aiService';
import DashboardCard from '../shared/DashboardCard';
import StatusBadge from '../shared/StatusBadge';
import ProgressBar from '../shared/ProgressBar';
import PrimaryButton from '../shared/PrimaryButton';
import AIInterpretationPanel from '../result/AIInterpretationPanel';

// ===== Types =====

interface OLSResult { outcome: string; model: string; beta: number; se: number; p_value: number; r_squared: number; n_observations: number; interpretation: string; }
interface RCSPoint { pdf_pct: number; log_odds_ratio: number; odds_ratio: number; ci_lower: number; ci_upper: number; }
interface LogisticResult { outcome: string; reference: string; odds_ratio: number; ci_lower: number; ci_upper: number; p_value: number; auc: number; }
interface AdjustedOR { quartile: string; label: string; pdf_range: string; osteopenia_or: number; osteopenia_ci_lower: number; osteopenia_ci_upper: number; osteoporosis_or: number; osteoporosis_ci_lower: number; osteoporosis_ci_upper: number; p_trend: number; }

export interface RiskModelingResultData {
  risk_id: string;
  exposure: string;
  outcome: string;
  outcomes: string[];
  model_types: string[];
  grouping: string;
  covariate_model: string[];
  quartile_groups: number[];
  ols_results: OLSResult[];
  rcs_curve_data: RCSPoint[];
  multinomial_logistic_results: LogisticResult[];
  adjusted_odds_ratios: AdjustedOR[];
  interpretation_summary: string;
  rcs_plot_url: string;
  or_forest_plot_url: string;
}

interface Props {
  riskTask?: AnalysisTask;
  projectId?: number;
  exposureName?: string;
  outcomeName?: string;
  onViewResult?: (taskId: number) => void;
  onRunTask?: (taskType: string) => void;
}

type JobState = 'idle' | 'creating' | 'running' | 'done' | 'failed';

export default function RiskModelingModule({ riskTask, projectId, exposureName, outcomeName, onRunTask }: Props) {
  const hasTask = !!(riskTask && riskTask.id);
  const [jobState, setJobState] = useState<JobState>('idle');
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RiskModelingResultData | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);
  const stop = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  const handleRun = async () => {
    if (!projectId) return;
    setJobState('creating'); setError(null);
    const jr = await createAIRiskModelingJob(projectId, {
      exposure: exposureName || 'Liver_PDFF',
      outcomes: ['BMD', 'TBS', 'Osteopenia', 'Osteoporosis'],
      model_types: ['OLS', 'RCS', 'MultinomialLogistic'],
      covariate_model: ['age', 'sex', 'bmi', 'smoking', 'alcohol', 'physical_activity'],
      grouping: 'quartile',
      quartile_groups: [5.2, 8.1, 12.8, 35.0],
    });
    if (!jr.ok) { setJobState('failed'); setError(jr.message); return; }
    setJobState('running'); setProgress(0); setStage('开始执行');
    const jId = jr.data.job_id;
    pollRef.current = setInterval(async () => {
      const s = await getAIJobStatus(jId);
      if (!s.ok) { stop(); setJobState('failed'); setError(s.message); return; }
      setProgress(s.data.progress); setStage(s.data.progress_stage);
      if (s.data.status === 'succeeded') { stop(); const r = await getAIJobResult(jId); if (r.ok && r.data.result) { setResult(r.data.result as RiskModelingResultData); setJobState('done'); } else { setJobState('failed'); setError('结果获取失败'); } }
      else if (s.data.status === 'failed') { stop(); setJobState('failed'); setError(s.data.error_message || '执行失败'); }
    }, 2000);
  };

  const isDone = jobState === 'done';
  const isRunning = jobState === 'running' || jobState === 'creating';
  const ors = result?.adjusted_odds_ratios || [];
  const ols = result?.ols_results || [];
  const logistic = result?.multinomial_logistic_results || [];
  const rcs = result?.rcs_curve_data || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="shrink-0 w-7 h-7 rounded-lg bg-navy-700 text-white flex items-center justify-center text-xs font-heading font-bold">6</span>
        <div><h3 className="section-title">风险建模</h3><p className="text-xs text-text-muted mt-0.5">肝脏脂肪与骨质疏松风险分层</p></div>
        {isDone && <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-green-50 border border-green-100 text-xs font-heading font-medium text-green-600 ml-auto">建模完成</span>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Controls */}
        <DashboardCard padding="md">
          <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">建模参数</h4>
          <div className="space-y-2 text-xs text-text-secondary mb-3">
            <div className="flex justify-between py-1 border-b border-border-light"><span>暴露</span><span className="font-heading font-semibold text-text-primary">{exposureName || 'Liver_PDFF'}</span></div>
            <div className="flex justify-between py-1 border-b border-border-light"><span>结局</span><span className="text-text-primary text-[10px]">BMD, TBS, Osteopenia, Osteoporosis</span></div>
            <div className="flex justify-between py-1 border-b border-border-light"><span>模型</span><span className="text-text-muted text-[10px]">OLS, RCS, Multinomial</span></div>
            <div className="flex justify-between py-1"><span>分组</span><span className="font-heading text-text-primary">四分位</span></div>
          </div>
          {!hasTask && jobState === 'idle' && <PrimaryButton onClick={handleRun} className="w-full" size="sm">开始风险建模</PrimaryButton>}
          {jobState === 'failed' && <div className="space-y-2"><div className="text-xs text-red-600 bg-red-50 px-3 py-1.5 rounded-lg">{error}</div><PrimaryButton onClick={handleRun} className="w-full" size="sm">重试</PrimaryButton></div>}
          {isRunning && <div className="space-y-2"><ProgressBar value={progress} size="sm" /><p className="text-[10px] text-text-muted">{stage}</p></div>}
          {isDone && <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-3 py-1.5 rounded-lg"><svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>建模完成</div>}
        </DashboardCard>

        {/* OLS Results */}
        <div className="lg:col-span-2">
          <DashboardCard padding="md">
            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">OLS 回归 — PDFF 每增加 1 SD</h4>
            {ols.length > 0 ? (
              <div className="table-scroll"><table className="w-full text-[11px]"><thead><tr className="text-text-muted border-b border-border"><th className="text-left py-1.5 font-medium">结局</th><th className="text-right py-1.5 font-medium">β</th><th className="text-right py-1.5 font-medium">SE</th><th className="text-right py-1.5 font-medium">P</th><th className="text-right py-1.5 font-medium">R²</th><th className="text-right py-1.5 font-medium">N</th></tr></thead>
                <tbody>{ols.map((o) => (<tr key={o.outcome} className="border-b border-border-light last:border-0"><td className="py-1.5 font-heading font-semibold text-text-primary">{o.outcome}</td><td className="py-1.5 text-right font-heading font-semibold text-text-primary">{o.beta.toFixed(3)}</td><td className="py-1.5 text-right text-text-muted">{o.se.toFixed(3)}</td><td className={`py-1.5 text-right font-heading font-semibold ${o.p_value < 0.05 ? 'text-green-600' : 'text-text-muted'}`}>{o.p_value.toExponential(1)}</td><td className="py-1.5 text-right text-text-secondary">{o.r_squared.toFixed(2)}</td><td className="py-1.5 text-right text-text-muted">{o.n_observations.toLocaleString()}</td></tr>))}</tbody></table></div>
            ) : (<div className="text-center py-8 text-text-muted text-xs">{isRunning ? '分析中...' : '运行风险建模以查看结果'}</div>)}
          </DashboardCard>
        </div>
      </div>

      {/* Adjusted OR by Quartile */}
      {isDone && ors.length > 0 && (
        <DashboardCard padding="md">
          <h4 className="font-heading font-semibold text-sm text-text-primary mb-4">四分位风险分层 — 调整后 OR</h4>
          <div className="table-scroll">
            <table className="w-full text-[11px]">
              <thead><tr className="text-text-muted border-b-2 border-border"><th className="text-left py-1.5 font-heading font-semibold">四分位</th><th className="text-left py-1.5 font-heading font-semibold">PDFF 范围</th><th className="text-right py-1.5 font-heading font-semibold">Osteopenia OR</th><th className="text-right py-1.5 font-heading font-semibold">Osteoporosis OR</th><th className="text-right py-1.5 font-heading font-semibold">P trend</th></tr></thead>
              <tbody>
                {ors.map((or) => (
                  <tr key={or.quartile} className={`border-b border-border-light last:border-0 ${or.quartile === 'Q4' ? 'bg-red-50/30' : ''}`}>
                    <td className="py-2 px-2 font-heading font-bold text-text-primary">{or.quartile} <span className="text-text-muted font-normal text-[10px]">({or.label})</span></td>
                    <td className="py-2 px-2 text-text-secondary font-mono text-[10px]">{or.pdf_range}</td>
                    <td className="py-2 px-2 text-right font-heading font-semibold">{or.osteopenia_or.toFixed(2)} <span className="text-text-muted text-[10px] font-normal">[{or.osteopenia_ci_lower.toFixed(2)}–{or.osteopenia_ci_upper.toFixed(2)}]</span></td>
                    <td className={`py-2 px-2 text-right font-heading font-bold ${or.osteoporosis_or > 1.3 ? 'text-red-600' : 'text-text-primary'}`}>{or.osteoporosis_or.toFixed(2)} <span className="text-text-muted text-[10px] font-normal">[{or.osteoporosis_ci_lower.toFixed(2)}–{or.osteoporosis_ci_upper.toFixed(2)}]</span></td>
                    <td className="py-2 px-2 text-right font-heading font-semibold text-green-600">{or.p_trend.toExponential(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-center gap-3 mt-4 h-12 bg-surface rounded-lg">
            {ors.map((or, i) => (
              <div key={or.quartile} className="flex items-center gap-2 text-[10px]">
                <span className="text-text-muted w-6 text-right">{or.quartile}</span>
                <div className="w-20 h-6 bg-white rounded border border-border relative flex items-center justify-center">
                  <span className={`font-heading font-bold text-xs ${or.osteoporosis_or > 1.3 ? 'text-red-600' : 'text-text-primary'}`}>{or.osteoporosis_or.toFixed(2)}x</span>
                </div>
                {i < ors.length - 1 && <span className="text-text-muted">→</span>}
              </div>
            ))}
          </div>
        </DashboardCard>
      )}

      {/* Logistic + RCS placeholders + Interpretation */}
      {isDone && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Logistic Results */}
          <DashboardCard padding="md">
            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">多分类 Logistic 回归</h4>
            {logistic.length > 0 ? (
              <div className="space-y-2">
                {logistic.map((l) => (
                  <div key={l.outcome} className="bg-surface rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-heading font-semibold text-sm text-text-primary">{l.outcome}</span>
                      <span className="text-[10px] text-text-muted">vs {l.reference}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[10px]">
                      <div><span className="text-text-muted">OR</span><p className="font-heading font-bold text-text-primary">{l.odds_ratio.toFixed(2)}</p></div>
                      <div><span className="text-text-muted">95% CI</span><p className="font-heading text-text-primary">[{l.ci_lower.toFixed(2)}–{l.ci_upper.toFixed(2)}]</p></div>
                      <div><span className="text-text-muted">AUC</span><p className="font-heading font-bold text-navy-600">{l.auc.toFixed(2)}</p></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </DashboardCard>

          {/* RCS Curve Placeholder */}
          <DashboardCard padding="md">
            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">RCS 剂量-反应曲线</h4>
            <div className="aspect-[4/3] bg-surface-alt rounded-xl border border-border flex flex-col items-center justify-center gap-2">
              <svg className="w-8 h-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3l-1.5 15M15 3h5.25A2.25 2.25 0 0122.5 5.25v13.5A2.25 2.25 0 0120.25 21H15" />
              </svg>
              <span className="text-[10px] text-text-muted">RCS 剂量-反应曲线</span>
              <span className="text-[9px] text-text-muted">运行真实 statsmodels 后生成</span>
              {rcs.length > 0 && <span className="text-[10px] text-text-secondary font-heading mt-1">{rcs.length} 个数据点就绪</span>}
            </div>
          </DashboardCard>
        </div>
      )}

      {/* AI Interpretation */}
      {isDone && result?.interpretation_summary && (
        <DashboardCard padding="md" className="bg-blue-50/30 border-blue-100">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-navy-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
            <div>
              <h4 className="font-heading font-semibold text-sm text-navy-700 mb-1">AI 风险解读</h4>
              <p className="text-xs text-navy-600 leading-relaxed">{result.interpretation_summary}</p>
            </div>
          </div>
        </DashboardCard>
      )}

      {/* ===== AI Interpretation ===== */}
      {result && projectId && (
        <AIInterpretationPanel
          jobType="risk_modeling"
          resultData={result as unknown as Record<string, unknown>}
          projectId={projectId}
        />
      )}
    </div>
  );
}
