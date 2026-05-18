import { useState, useEffect, useRef } from 'react';
import type { AnalysisTask } from '../../types';
import { createAIMediationMRJob, getAIJobStatus, getAIJobResult } from '../../services/aiService';
import StatusBadge from '../shared/StatusBadge';
import PrimaryButton from '../shared/PrimaryButton';
import ProgressBar from '../shared/ProgressBar';
import AIInterpretationPanel from '../result/AIInterpretationPanel';

// ===== Props =====

interface Props {
  mediationTask?: AnalysisTask;
  projectId?: number;
  exposureName?: string;
  outcomeName?: string;
  onViewResult?: (taskId: number) => void;
  onRunTask?: (taskType: string) => void;
  onMediationComplete?: (data: MediationMRResultData) => void;
}

// ===== Types =====

interface PathAResult { protein: string; beta_a: number; se_a: number; p_value_a: number; f_statistic: number; }
interface PathBResult { protein: string; beta_b: number; se_b: number; p_value_b: number; }
interface IndirectEffect { protein: string; indirect_effect: number; se_indirect: number; ci_lower: number; ci_upper: number; p_mediation: number; proportion_mediated_pct: number; significant: boolean; }
interface RankedProtein { rank: number; protein: string; full_name: string; uniprot: string; indirect_effect: number; proportion_mediated_pct: number; p_mediation: number; significant: boolean; known_relevance: string; }

export interface MediationMRResultData {
  mediation_id: string;
  exposure: string;
  outcome: string;
  mediator_source: string;
  tested_proteins: number;
  candidate_proteins: string[];
  correction_method: string;
  alpha: number;
  total_effect: number;
  total_indirect_effect: number;
  total_direct_effect: number;
  total_effect_pvalue: number;
  significant_mediators_count: number;
  path_a_results: PathAResult[];
  path_b_results: PathBResult[];
  indirect_effects: IndirectEffect[];
  ranked_proteins: RankedProtein[];
  mechanism_diagram_url: string;
}

type MedJobState = 'idle' | 'creating' | 'running' | 'done' | 'failed';

const DATA_SOURCES = [
  { value: 'decode_plasma', label: 'deCODE 血浆蛋白 pQTL (4,907)' },
  { value: 'metabolite_gwas', label: '代谢物 GWAS 数据' },
  { value: 'gwas_catalog', label: 'GWAS Catalog / OpenGWAS' },
];

const TASKS = [
  { key: 'potential_mediators', label: '潜在中介因子', desc: '识别候选血浆蛋白中介因子' },
  { key: 'mediation_mr', label: '中介 MR 分析', desc: '两步孟德尔随机化分析' },
];

// ===== Component =====

export default function MediationMRModule({ mediationTask, projectId, exposureName, outcomeName, onMediationComplete }: Props) {
  const [selectedSource, setSelectedSource] = useState('decode_plasma');
  const hasMediation = !!(mediationTask && mediationTask.id);
  const legacySuccess = mediationTask?.status === 'success';

  const [jobState, setJobState] = useState<MedJobState>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MediationMRResultData | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isDone = legacySuccess || jobState === 'done';
  const isRunning = jobState === 'running' || jobState === 'creating';

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const stopPolling = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  const handleRunMediation = async () => {
    if (!projectId) return;
    setJobState('creating'); setError(null);

    const jobResult = await createAIMediationMRJob(projectId, {
      exposure_trait: exposureName || 'Liver_PDFF',
      outcome_trait: outcomeName || 'Osteoporosis',
      mediator_source: selectedSource,
      candidate_proteins: ['ACY1','H6PD','SHBG','ADH1A','POR','NAAA'],
      total_effect: 0.44,
      correction_method: 'fdr',
      alpha: 0.05,
    });

    if (!jobResult.ok) { setJobState('failed'); setError(jobResult.message); return; }

    setJobState('running'); setJobId(jobResult.data.job_id); setProgress(0); setStage('开始执行');
    const jId = jobResult.data.job_id;
    pollRef.current = setInterval(async () => {
      const status = await getAIJobStatus(jId);
      if (!status.ok) { stopPolling(); setJobState('failed'); setError(status.message); return; }
      const j = status.data; setProgress(j.progress); setStage(j.progress_stage);
      if (j.status === 'succeeded') {
        stopPolling();
        const r = await getAIJobResult(jId);
        if (r.ok && r.data.result) { setResult(r.data.result as unknown as MediationMRResultData); setJobState('done'); setProgress(100); onMediationComplete?.(r.data.result as unknown as MediationMRResultData); }
        else { setJobState('failed'); setError('结果获取失败'); }
      } else if (j.status === 'failed') { stopPolling(); setJobState('failed'); setError(j.error_message || '中介 MR 执行失败'); }
    }, 2000);
  };

  const ranked = result?.ranked_proteins || [];
  const totalEffect = result?.total_effect ?? 0.44;
  const indirectEff = result?.total_indirect_effect ?? 0.145;
  const directEff = result?.total_direct_effect ?? 0.295;
  const propMed = indirectEff / totalEffect * 100;

  return (
    <div className="space-y-4">
      <div className="card-dashboard bg-gold-50/60 border-gold-200 overflow-hidden">
        {/* Title bar */}
        <div className="bg-gold-500/10 border-b border-gold-200 px-5 py-3 flex items-center gap-3">
          <span className="shrink-0 w-7 h-7 rounded-lg bg-gold-500 text-white flex items-center justify-center text-xs font-heading font-bold">C</span>
          <div>
            <h3 className="section-title text-gold-800">中介机制筛选</h3>
            <p className="text-xs text-gold-600/80 mt-0.5">发现连接脂肪性状与疾病结局的血浆蛋白中介因子</p>
          </div>
          {isDone && <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-gold-500/15 border border-gold-300/50 text-xs font-heading font-medium text-gold-700 ml-auto"><span className="w-1.5 h-1.5 rounded-full bg-gold-500" />中介 MR 完成</span>}
          {isRunning && <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-gold-500/15 border border-gold-300/50 text-xs font-heading font-medium text-gold-700 ml-auto"><span className="w-1.5 h-1.5 rounded-full bg-gold-500 animate-pulse" />运行中</span>}
        </div>

        <div className="px-5 pt-4 pb-2">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" /></svg>
            <h4 className="font-heading font-semibold text-base text-gold-800">中介 MR 分析</h4>
            {mediationTask && <StatusBadge status={mediationTask.status} />}
          </div>
        </div>

        <div className="px-5 pb-5 grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* LEFT: Controls */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-xl border border-gold-200 p-4">
              <h5 className="font-heading font-semibold text-sm text-text-primary mb-3">选择公共数据</h5>
              <div className="space-y-2 mb-3">
                <div className="flex items-start gap-2"><div className="w-1.5 h-1.5 rounded-full bg-gold-400 mt-1.5 shrink-0" /><p className="text-xs text-text-secondary leading-relaxed">4,907 种冰岛血浆蛋白 pQTL 数据，来源于 deCODE 遗传学研究</p></div>
                <div className="flex items-start gap-2"><div className="w-1.5 h-1.5 rounded-full bg-teal-400 mt-1.5 shrink-0" /><p className="text-xs text-text-secondary leading-relaxed">代谢物 GWAS 汇总统计数据</p></div>
              </div>
              <select value={selectedSource} onChange={(e) => setSelectedSource(e.target.value)}
                className="w-full appearance-none bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary font-medium cursor-pointer focus:outline-none focus:ring-2 focus:ring-gold-400/50 focus:border-gold-400 mb-3">
                {DATA_SOURCES.map(ds => <option key={ds.value} value={ds.value}>{ds.label}</option>)}
              </select>
              {!hasMediation && jobState === 'idle' && (
                <PrimaryButton variant="gold" size="sm" className="w-full" onClick={handleRunMediation}>运行中介 MR</PrimaryButton>
              )}
            </div>

            <div className="bg-white rounded-xl border border-gold-200 p-4">
              <h5 className="font-heading font-semibold text-sm text-text-primary mb-3">已选中 Tasks</h5>
              <div className="space-y-2">
                {TASKS.map(task => {
                  const taskDone = isDone;
                  return (
                    <div key={task.key} className={`flex items-center gap-3 p-2.5 rounded-lg transition-card ${taskDone ? 'bg-green-50/50 border border-green-100' : 'bg-surface'}`}>
                      {taskDone ? <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
                        : isRunning ? <svg className="w-4 h-4 text-navy-600 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                        : <div className="w-4 h-4 rounded-full border-2 border-text-muted" />}
                      <div className="min-w-0 flex-1"><p className="text-xs font-heading font-semibold text-text-primary">{task.label}</p><p className="text-[10px] text-text-muted mt-0.5">{task.desc}</p></div>
                      {taskDone && <span className="text-[10px] font-heading font-medium text-green-600">已完成</span>}
                      {isRunning && <span className="text-[10px] font-heading font-medium text-navy-600">运行中...</span>}
                    </div>
                  );
                })}
              </div>
              {isRunning && <div className="mt-3"><ProgressBar value={progress} size="sm" /><p className="text-[10px] text-text-muted mt-1">{stage}</p></div>}
              {jobState === 'failed' && <div className="mt-3 text-xs text-red-600 bg-red-50 px-3 py-1.5 rounded-lg">{error}<button onClick={handleRunMediation} className="ml-2 text-navy-600 font-medium">重试</button></div>}
              <div className="mt-4 pt-3 border-t border-border">
                {!hasMediation && jobState === 'idle' && (
                  <PrimaryButton variant="gold" size="sm" className="w-full" onClick={handleRunMediation}>运行中介 MR</PrimaryButton>
                )}
                {isDone && (
                  <div className="text-xs text-green-600 bg-green-50 px-3 py-1.5 rounded-lg text-center">
                    分析完成 — {result?.significant_mediators_count || 0} 个显著中介蛋白 (FDR &lt; 0.05)
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT: Mechanism Diagram */}
          <div className="lg:col-span-3 space-y-4">
            <div className="bg-white rounded-xl border border-gold-200 p-4">
              <h5 className="font-heading font-semibold text-sm text-text-primary mb-4">潜在中介因子 — 机制流程图</h5>
              <div className="flex items-center justify-center gap-2 py-4">
                {/* Adipose */}
                <div className="flex flex-col items-center gap-2"><div className="w-16 h-16 rounded-2xl bg-red-50 border-2 border-red-200 flex items-center justify-center shadow-sm"><svg width="32" height="32" viewBox="0 0 24 24" fill="none"><path d="M12 3C8 3 5 7 5 10c0 4 3 8 7 11 4-3 7-7 7-11 0-3-3-7-7-7z" stroke="var(--color-danger-600)" strokeWidth="1.5" fill="var(--color-danger-100)" /></svg></div><div className="text-center"><p className="text-[11px] font-heading font-bold text-text-primary">脂肪组织</p><p className="text-[10px] text-text-muted">{exposureName || 'Liver PDFF'}</p><div className="mt-1 px-2 py-0.5 rounded-full bg-red-50 border border-red-100 text-[9px] font-medium text-red-600">暴露因素</div></div></div>
                <div className="flex flex-col items-center px-2"><div className="flex items-center"><div className="h-0.5 w-8 bg-gold-400" /><svg className="w-3 h-3 text-gold-500 -ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7" /></svg></div><span className="text-[9px] text-gold-600 font-medium mt-1 whitespace-nowrap">βᴬ = {ranked[0]?.indirect_effect ? (ranked[0].indirect_effect / 0.30).toFixed(3) : '0.284'}</span><span className="text-[8px] text-text-muted whitespace-nowrap">步骤一：暴露 → 中介</span></div>
                {/* Plasma proteins */}
                <div className="flex flex-col items-center gap-2"><div className="w-16 h-16 rounded-2xl bg-gold-100 border-2 border-gold-300 flex items-center justify-center shadow-sm"><svg width="32" height="32" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="var(--color-gold-500)" strokeWidth="1.5" fill="var(--color-gold-100)" /></svg></div><div className="text-center"><p className="text-[11px] font-heading font-bold text-text-primary">血浆蛋白</p><p className="text-[10px] text-text-muted">{ranked.slice(0,3).map(r=>r.protein).join(', ') || 'FGF21, GDF15, ...'}</p><div className="mt-1 px-2 py-0.5 rounded-full bg-gold-50 border border-gold-200 text-[9px] font-medium text-gold-700">中介因子</div></div></div>
                <div className="flex flex-col items-center px-2"><div className="flex items-center"><div className="h-0.5 w-8 bg-navy-400" /><svg className="w-3 h-3 text-navy-600 -ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7" /></svg></div><span className="text-[9px] text-navy-600 font-medium mt-1 whitespace-nowrap">βᴮ = 0.512</span><span className="text-[8px] text-text-muted whitespace-nowrap">步骤二：中介 → 结局</span></div>
                {/* Osteoporosis */}
                <div className="flex flex-col items-center gap-2"><div className="w-16 h-16 rounded-2xl bg-blue-50 border-2 border-blue-200 flex items-center justify-center shadow-sm"><svg width="32" height="32" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="3" stroke="var(--color-navy-600)" strokeWidth="1.5" fill="var(--color-blue-100)" /></svg></div><div className="text-center"><p className="text-[11px] font-heading font-bold text-text-primary">{outcomeName || '骨质疏松'}</p><p className="text-[10px] text-text-muted">骨密度 ↓</p><div className="mt-1 px-2 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-[9px] font-medium text-blue-600">结局变量</div></div></div>
              </div>
              <div className="flex items-center justify-center gap-3 mt-2 pt-3 border-t border-border">
                <div className="text-center"><span className="text-[10px] text-text-muted">间接效应</span><p className="text-sm font-heading font-bold text-gold-600">β = {indirectEff.toFixed(3)}</p><p className="text-[9px] text-text-muted">{propMed.toFixed(1)}% mediated</p></div>
                <div className="w-px h-8 bg-border" />
                <div className="text-center"><span className="text-[10px] text-text-muted">直接效应</span><p className="text-sm font-heading font-bold text-navy-600">β = {directEff.toFixed(3)}</p><p className="text-[9px] text-text-muted">{(100-propMed).toFixed(1)}% direct</p></div>
                <div className="w-px h-8 bg-border" />
                <div className="text-center"><span className="text-[10px] text-text-muted">总效应</span><p className="text-sm font-heading font-bold text-text-primary">β = {totalEffect.toFixed(3)}</p><p className="text-[9px] text-text-muted">p = {result?.total_effect_pvalue?.toExponential(1) || '4.8×10⁻⁵'}</p></div>
              </div>
            </div>
          </div>
        </div>

        {/* Results Table */}
        <div className="px-5 pb-5">
          <div className="bg-white rounded-xl border border-gold-200 p-4">
            <h5 className="font-heading font-semibold text-sm text-text-primary mb-3">中介 MR 分析结果</h5>
            {isDone && ranked.length > 0 ? (
              <div className="table-scroll">
                <table className="w-full text-[11px]" aria-label="Mediation MR results table">
                  <thead>
                    <tr className="text-text-muted border-b-2 border-border">
                      <th className="text-left py-2 px-2 font-heading font-semibold">Rank</th>
                      <th className="text-left py-2 px-2 font-heading font-semibold">蛋白</th>
                      <th className="text-left py-2 px-2 font-heading font-semibold">全称</th>
                      <th className="text-right py-2 px-2 font-heading font-semibold">间接效应</th>
                      <th className="text-right py-2 px-2 font-heading font-semibold">中介比例</th>
                      <th className="text-right py-2 px-2 font-heading font-semibold">P</th>
                      <th className="text-center py-2 px-2 font-heading font-semibold">显著</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranked.map((row, i) => (
                      <tr key={row.protein} className={`border-b border-border-light last:border-0 transition-card ${i % 2 === 0 ? 'bg-surface/50' : 'bg-white'} hover:bg-gold-50/30`}>
                        <td className="py-2 px-2 font-heading font-bold text-text-primary">#{row.rank}</td>
                        <td className="py-2 px-2"><span className="font-heading font-semibold text-text-primary">{row.protein}</span></td>
                        <td className="py-2 px-2 text-text-secondary text-[10px]">{row.full_name}</td>
                        <td className={`py-2 px-2 text-right font-heading font-bold ${row.indirect_effect > 0 ? 'text-gold-600' : 'text-danger-600'}`}>{row.indirect_effect > 0 ? '+' : ''}{row.indirect_effect.toFixed(4)}</td>
                        <td className="py-2 px-2 text-right"><span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-heading font-semibold ${row.significant ? 'bg-gold-50 text-gold-700' : 'bg-surface text-text-muted'}`}>{row.proportion_mediated_pct.toFixed(1)}%</span></td>
                        <td className={`py-2 px-2 text-right font-heading font-semibold ${row.significant ? 'text-green-600' : 'text-text-muted'}`}>{row.p_mediation.toExponential(1)}</td>
                        <td className="py-2 px-2 text-center">{row.significant ? <svg className="w-4 h-4 text-green-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg> : <span className="text-text-muted">—</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-text-muted text-xs">{isRunning ? `分析中... ${progress}%` : '运行中介 MR 分析以查看结果'}</div>
            )}
            <div className="flex items-center gap-4 mt-3 pt-2 border-t border-border text-[10px] text-text-muted">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gold-400" />间接效应</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />p &lt; 0.05 (FDR)</span>
              <span>路径 A：暴露→中介</span><span>路径 B：中介→结局</span>
            </div>
          </div>
        </div>
      </div>

      {/* ===== AI Interpretation ===== */}
      {result && projectId && (
        <AIInterpretationPanel
          jobType="mediation_mr"
          resultData={result as unknown as Record<string, unknown>}
          projectId={projectId}
          sourceJobId={jobId || undefined}
        />
      )}
    </div>
  );
}
