import { useState } from 'react';
import type { ChatResponse } from '../../services/aiService';
import { chatQuery, getAIJobStatus } from '../../services/aiService';
import DashboardCard from '../shared/DashboardCard';
import ProgressBar from '../shared/ProgressBar';

// ===== Props =====

interface Props {
  projectId: number;
  context?: Record<string, unknown>;
  className?: string;
}

// ===== Component =====

export default function ChatInput({ projectId, context, className = '' }: Props) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState(0);

  const handleSubmit = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setJobProgress(0);

    const res = await chatQuery({
      message: q,
      project_id: projectId,
      context: context || {},
    });

    if (!res.ok) {
      setError(res.message);
    } else {
      setResult(res.data);
      // job_created → 轮询进度
      if (res.data.type === 'job_created' && res.data.jobId) {
        pollJobProgress(res.data.jobId);
      }
    }
    setLoading(false);
  };

  const pollJobProgress = (jobId: string) => {
    const timer = setInterval(async () => {
      const status = await getAIJobStatus(jobId);
      if (status.ok) {
        setJobProgress(status.data.progress || 0);
        if (status.data.status === 'succeeded' || status.data.status === 'failed') {
          clearInterval(timer);
          setJobProgress(status.data.status === 'succeeded' ? 100 : 0);
        }
      } else {
        clearInterval(timer);
      }
    }, 2000);
  };

  const handleAction = (action: { label: string; action: string; params?: Record<string, unknown> }) => {
    if (action.action === 'run_gwas') setInput('做 GWAS 分析');
    else if (action.action === 'run_mr') setInput('做孟德尔随机化分析');
    else if (action.action === 'generate_report') setInput('生成科研报告');
    else if (action.action === 'view_capabilities') setInput('查看可用能力');
    else if (action.action === 'list_jobs') setInput('查看任务进度');
    else if (action.action === 'view_result') setInput('查看分析进度');
    else if (action.action === 'run_capability') {
      const cap = action.params?.capability;
      if (cap === 'gwas_analysis') setInput('做 GWAS 分析');
      else if (cap === 'mendelian_randomization') setInput('做孟德尔随机化分析');
      else if (cap === 'mediation_mr') setInput('做中介 MR 分析');
      else if (cap === 'risk_modeling') setInput('做风险建模');
      else if (cap === 'report_generation') setInput('生成科研报告');
      else if (cap === 'image_segmentation') setInput('上传 MRI 并执行 AI 分割');
      else setInput(`执行 ${cap}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Input area */}
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入问题或指令，如：做 GWAS 分析..."
            disabled={loading}
            className="w-full bg-white border border-border rounded-lg px-3.5 py-2 text-sm text-text-primary
                       placeholder:text-text-muted
                       focus:outline-none focus:ring-2 focus:ring-navy-600/30 focus:border-navy-600
                       disabled:opacity-60 transition-card"
          />
          {loading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <svg className="animate-spin h-4 w-4 text-navy-600" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          )}
        </div>
        <button
          onClick={handleSubmit}
          disabled={loading || !input.trim()}
          className="shrink-0 px-4 py-2 rounded-lg text-sm font-heading font-medium
                     bg-navy-700 text-white hover:bg-navy-800
                     disabled:opacity-40 disabled:cursor-not-allowed transition-card"
        >
          发送
        </button>
      </div>
      <p className="text-[10px] text-text-muted">
        试试：「做 GWAS」「MR 分析」「查看进度」「生成报告」
      </p>

      {/* ---- Error ---- */}
      {error && (
        <div className="flex items-start gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs">
          <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <div className="min-w-0">
            <span className="text-red-700 font-medium">请求失败</span>
            <p className="text-red-500 mt-0.5 truncate">{error}</p>
          </div>
          <button onClick={() => { setError(null); handleSubmit(); }} className="text-red-400 hover:text-red-600 shrink-0 text-[10px] font-medium">重试</button>
        </div>
      )}

      {/* ---- answer (AI 回复) ---- */}
      {result?.type === 'answer' && (
        <DashboardCard padding="md" className="bg-gradient-to-b from-navy-50/20 to-white border-navy-100">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-navy-700 text-white flex items-center justify-center shrink-0 text-xs font-heading font-bold">
              AI
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs text-text-secondary leading-relaxed whitespace-pre-wrap">{result.message}</p>
            </div>
          </div>
          {result.actions && result.actions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-border">
              <span className="text-[10px] text-text-muted self-center">试试：</span>
              {result.actions.slice(0, 4).map((a, i) => (
                <button key={i} onClick={() => handleAction(a)}
                  className="px-2.5 py-1 rounded text-[11px] font-medium bg-white border border-border
                             text-navy-600 hover:text-navy-800 hover:border-navy-600 transition-card">
                  {a.label}
                </button>
              ))}
            </div>
          )}
        </DashboardCard>
      )}

      {/* ---- job_created ---- */}
      {result?.type === 'job_created' && (
        <DashboardCard padding="md" className="bg-green-50/30 border-green-100">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center shrink-0">
              <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-heading font-semibold text-text-primary">任务已创建</p>
              <p className="text-xs text-text-secondary mt-0.5">
                {result.message}
                {result.jobId && <span className="font-mono text-[10px] text-text-muted ml-1">({result.jobId})</span>}
              </p>
              {jobProgress > 0 && jobProgress < 100 && (
                <div className="mt-2 space-y-1">
                  <ProgressBar value={jobProgress} size="sm" />
                  <p className="text-[10px] text-text-muted">{jobProgress}%</p>
                </div>
              )}
              {jobProgress === 100 && (
                <p className="text-[10px] text-green-600 mt-2 font-medium">任务执行完成</p>
              )}
            </div>
          </div>
          {result.actions && result.actions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-border">
              {result.actions.slice(0, 4).map((a, i) => (
                <button key={i} onClick={() => handleAction(a)}
                  className="px-2.5 py-1 rounded text-[11px] font-medium bg-white border border-border
                             text-text-secondary hover:text-text-primary hover:border-navy-600 transition-card">
                  {a.label}
                </button>
              ))}
            </div>
          )}
        </DashboardCard>
      )}

      {/* ---- need_more_info ---- */}
      {result?.type === 'need_more_info' && (
        <DashboardCard padding="md" className="bg-blue-50/30 border-blue-100">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
              <svg className="w-4 h-4 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-heading font-semibold text-text-primary">需要补充信息</p>
              <p className="text-xs text-text-secondary mt-0.5 whitespace-pre-wrap">{result.message}</p>
              {/* Suggested inputs from parameter completer */}
              {result.suggestedInputs && result.suggestedInputs.length > 0 && (
                <div className="mt-2 space-y-1.5">
                  {result.suggestedInputs.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 text-[10px]">
                      <span className="text-text-muted w-16 shrink-0">{s.label || s.field}</span>
                      {s.type === 'upload' ? (
                        <span className="px-2 py-0.5 rounded bg-gold-50 border border-gold-200 text-gold-700">
                          需要上传
                        </span>
                      ) : s.type === 'select' || s.type === 'multi-select' ? (
                        <span className="px-2 py-0.5 rounded bg-white border border-border text-navy-600">
                          {Array.isArray(s.suggested_value) ? s.suggested_value.join(', ') : String(s.suggested_value ?? s.hint ?? '—')}
                        </span>
                      ) : (
                        <span className="text-text-primary font-medium">
                          {s.suggested_value != null ? String(s.suggested_value) : s.hint || '请提供'}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {/* Blocked fields */}
              {result.blockedFields && result.blockedFields.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {result.blockedFields.map((f) => (
                    <span key={f} className="px-2 py-0.5 rounded text-[10px] font-medium bg-gold-50 border border-gold-200 text-gold-700">
                      {f} — 需用户操作
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
          {result.actions && result.actions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-border">
              {result.actions.slice(0, 4).map((a, i) => (
                <button key={i} onClick={() => handleAction(a)}
                  className="px-2.5 py-1 rounded text-[11px] font-medium bg-white border border-border
                             text-text-secondary hover:text-text-primary hover:border-navy-600 transition-card">
                  {a.label}
                </button>
              ))}
            </div>
          )}
        </DashboardCard>
      )}

      {/* ---- job_status ---- */}
      {result?.type === 'job_status' && (
        <DashboardCard padding="md" className="bg-surface-alt/50 border-border">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-surface-alt flex items-center justify-center shrink-0">
              <svg className="w-4 h-4 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-heading font-semibold text-text-primary">任务状态</p>
              <p className="text-xs text-text-secondary mt-0.5 whitespace-pre-wrap">{result.message}</p>
            </div>
          </div>
          {result.actions && result.actions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-border">
              {result.actions.map((a, i) => (
                <button key={i} onClick={() => handleAction(a)}
                  className="px-2.5 py-1 rounded text-[11px] font-medium bg-white border border-border
                             text-text-secondary hover:text-text-primary hover:border-navy-600 transition-card">
                  {a.label}
                </button>
              ))}
            </div>
          )}
        </DashboardCard>
      )}
    </div>
  );
}
