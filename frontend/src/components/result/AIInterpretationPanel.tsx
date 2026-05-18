/**
 * AI 解读面板 — 可复用的"AI 解释"组件
 *
 * 嵌入各分析模块的结果区域，提供一键 AI 解读功能。
 * 通过创建 result_interpretation job 异步获取 LLM 解读。
 */

import { useState, useEffect, useRef } from 'react';
import { createAIJob, getAIJobStatus, getAIJobResult } from '../../services/aiService';
import DashboardCard from '../shared/DashboardCard';
import ProgressBar from '../shared/ProgressBar';

// ===== Props =====

interface Props {
  /** 分析类型 */
  jobType: 'segmentation' | 'gwas' | 'mr' | 'mediation_mr' | 'risk_modeling';
  /** 原始分析结果 JSON */
  resultData: Record<string, unknown>;
  /** 当前项目 ID */
  projectId: number;
  /** 源 Job ID（可选，用于追溯） */
  sourceJobId?: string;
  /** 额外的 CSS class */
  className?: string;
}

// ===== Types =====

interface InterpretationResult {
  summary: string;
  keyFindings: string[];
  cautions: string[];
  recommendedNextSteps: string[];
  plainLanguageExplanation: string;
  evidenceJobId: string;
}

type PanelState = 'idle' | 'creating' | 'running' | 'done' | 'failed';

const JOB_TYPE_LABELS: Record<string, string> = {
  segmentation: '影像分割',
  gwas: 'GWAS',
  mr: '孟德尔随机化',
  mediation_mr: '中介 MR',
  risk_modeling: '风险建模',
};

const FALLBACK_TEXT = 'AI 解读暂时不可用，请查看原始分析结果。稍后重试。';

// ===== Component =====

export default function AIInterpretationPanel({
  jobType,
  resultData,
  projectId,
  sourceJobId,
  className = '',
}: Props) {
  const [state, setState] = useState<PanelState>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [interpretation, setInterpretation] = useState<InterpretationResult | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  // ===== 触发解读 =====

  const handleInterpret = async () => {
    setState('creating');
    setError(null);

    const res = await createAIJob(projectId, 'interpretation', {
      sourceJobId: sourceJobId || `job_${jobType}_${Date.now()}`,
      jobType,
      jobResult: resultData,
      audience: 'researcher',
      language: 'zh',
    });

    if (!res.ok) {
      setState('failed');
      setError(res.message);
      return;
    }

    setState('running');
    setProgress(0);

    const jId = res.data.job_id;
    pollRef.current = setInterval(async () => {
      const status = await getAIJobStatus(jId);
      if (!status.ok) {
        stopPolling();
        setState('failed');
        setError(status.message);
        return;
      }

      const d = status.data;
      setProgress(d.progress || 0);

      if (d.status === 'succeeded') {
        stopPolling();
        const result = await getAIJobResult(jId);
        if (result.ok && result.data.result) {
          setInterpretation(result.data.result as unknown as InterpretationResult);
          setState('done');
        } else {
          // 尝试从 job status 本身获取 result
          const jobResult = (d as unknown as Record<string, unknown>).result as Record<string, unknown> | undefined;
          if (jobResult) {
            setInterpretation(jobResult as unknown as InterpretationResult);
            setState('done');
          } else {
            setState('failed');
            setError(result.ok ? '结果解析失败' : result.message);
          }
        }
      } else if (d.status === 'failed') {
        stopPolling();
        setState('failed');
        setError(d.error_message || '解读任务执行失败');
      }
    }, 2000);
  };

  // ===== Idle: 显示按钮 =====

  if (state === 'idle') {
    return (
      <div className={className}>
        <button
          onClick={handleInterpret}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-heading font-medium
                     bg-gradient-to-r from-navy-700 to-navy-800 text-white
                     hover:from-navy-800 hover:to-navy-900
                     shadow-sm hover:shadow-md transition-all duration-200"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
          AI 解读 {JOB_TYPE_LABELS[jobType] || jobType} 结果
        </button>
      </div>
    );
  }

  // ===== Creating / Running: 显示进度 =====

  if (state === 'creating' || state === 'running') {
    return (
      <DashboardCard padding="md" className={`bg-blue-50/20 border-blue-100 ${className}`}>
        <div className="flex items-center gap-3">
          <svg className="animate-spin h-4 w-4 text-navy-600 shrink-0" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-heading font-semibold text-text-primary">
              {state === 'creating' ? '正在创建 AI 解读任务...' : 'AI 正在分析结果...'}
            </p>
            {state === 'running' && (
              <div className="mt-2 space-y-1">
                <ProgressBar value={progress} size="sm" />
                <p className="text-[10px] text-text-muted">{progress}%</p>
              </div>
            )}
          </div>
        </div>
      </DashboardCard>
    );
  }

  // ===== Failed: 显示错误 + 重试 =====

  if (state === 'failed') {
    return (
      <DashboardCard padding="md" className={`bg-red-50/20 border-red-100 ${className}`}>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-heading font-semibold text-red-700">AI 解读失败</p>
            <p className="text-xs text-red-500 mt-0.5">{error || FALLBACK_TEXT}</p>
          </div>
          <button
            onClick={handleInterpret}
            className="shrink-0 text-xs text-navy-600 hover:text-navy-800 font-medium"
          >
            重试
          </button>
        </div>
      </DashboardCard>
    );
  }

  // ===== Done: 展示解读结果 =====

  if (!interpretation) return null;

  const { summary, keyFindings, cautions, recommendedNextSteps, plainLanguageExplanation, evidenceJobId } = interpretation;

  return (
    <DashboardCard padding="lg" className={`bg-gradient-to-b from-navy-50/30 to-white border-navy-100 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-navy-700 text-white flex items-center justify-center">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        <h4 className="font-heading font-semibold text-sm text-text-primary">
          AI 解读 · {JOB_TYPE_LABELS[jobType] || jobType}
        </h4>
        {evidenceJobId && (
          <span className="text-[10px] text-text-muted font-mono ml-auto">
            job: {evidenceJobId}
          </span>
        )}
      </div>

      {/* Summary */}
      {summary && (
        <div className="mb-4">
          <p className="text-sm text-text-secondary leading-relaxed">{summary}</p>
        </div>
      )}

      {/* Key Findings */}
      {keyFindings && keyFindings.length > 0 && (
        <div className="mb-4">
          <h5 className="text-xs font-heading font-semibold text-navy-700 mb-2">关键发现</h5>
          <ul className="space-y-1.5">
            {keyFindings.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                <span className="w-1.5 h-1.5 rounded-full bg-navy-600 shrink-0 mt-1.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Cautions */}
      {cautions && cautions.length > 0 && (
        <div className="mb-4">
          <h5 className="text-xs font-heading font-semibold text-gold-600 mb-2">注意事项</h5>
          <ul className="space-y-1">
            {cautions.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-[11px] text-gold-700">
                <svg className="w-3.5 h-3.5 text-gold-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Next Steps */}
      {recommendedNextSteps && recommendedNextSteps.length > 0 && (
        <div className="mb-4">
          <h5 className="text-xs font-heading font-semibold text-navy-700 mb-2">下一步建议</h5>
          <ul className="space-y-1">
            {recommendedNextSteps.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-[11px] text-navy-600">
                <span className="font-heading font-bold text-navy-400 text-[10px] shrink-0 mt-0.5">{i + 1}.</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Plain Language Explanation */}
      {plainLanguageExplanation && (
        <div>
          <h5 className="text-xs font-heading font-semibold text-navy-700 mb-2">通俗解释</h5>
          <div className="bg-surface rounded-lg px-3 py-2.5 border border-border-light">
            <p className="text-xs text-text-secondary leading-relaxed">
              {plainLanguageExplanation}
            </p>
          </div>
        </div>
      )}
    </DashboardCard>
  );
}
