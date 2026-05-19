import { useEffect, useState, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import { useTaskStore } from '../stores/taskStore';
import { createAIReportJob, getAIJobStatus, getAIJobResult, adaptReportResult } from '../services/aiService';
import { isSuccessStatus, isFailedStatus, TASK_TYPE_LABELS } from '../types';
import type { ReportGenerationResult } from '../types';
import { usePolling } from '../hooks/usePolling';
import { useToastStore } from '../stores/toastStore';
import ReportViewer from '../components/report/ReportViewer';
import PageShell from '../components/shared/PageShell';
import DashboardCard from '../components/shared/DashboardCard';
import PrimaryButton from '../components/shared/PrimaryButton';
import SecondaryButton from '../components/shared/SecondaryButton';
import ProgressBar from '../components/shared/ProgressBar';

type PageState = 'loading' | 'no_data' | 'selecting' | 'generating' | 'preview' | 'error';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const nav = useNavigate();
  const loc = useLocation();
  const { currentProject, fetchProject } = useProjectStore();
  const { tasks, fetchTasks } = useTaskStore();

  const [pageState, setPageState] = useState<PageState>('loading');
  const [report, setReport] = useState<ReportGenerationResult | null>(null);
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([]);
  const [genProgress, setGenProgress] = useState(0);
  const [genStage, setGenStage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [generatingJobId, setGeneratingJobId] = useState<string | null>(null);
  const [pollJobId, setPollJobId] = useState<string | null>(null);
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load project and tasks
  useEffect(() => {
    fetchProject(pid);
    fetchTasks(pid);
  }, [pid]);

  // Check for pre-existing report job from navigation state (workspace pass-through)
  useEffect(() => {
    const jobId = loc.state?.reportJobId as string | undefined;
    if (!jobId) return;
    setPageState('generating');
    setGeneratingJobId(jobId);
    setPollJobId(jobId);
    setGenProgress(5);
    setGenStage('报告生成中...');
    setSelectedJobIds([]); // Prevent selection state from overriding
    // Clear navigation state to avoid re-triggering on refresh
    nav(`/projects/${pid}/report`, { replace: true, state: {} });
  }, []);

  // Auto-detect completed jobs when tasks load
  useEffect(() => {
    // Skip auto-detection if we were passed a jobId from workspace
    if (loc.state?.reportJobId) return;

    if (tasks.length > 0 && pageState === 'loading') {
      const completedIds = tasks
        .filter((t) => t.status === 'success' && t.id > 0)
        .map((t) => String(t.id));
      if (completedIds.length > 0) {
        setSelectedJobIds(completedIds);
        setPageState('selecting');
      } else {
        setPageState('no_data');
      }
    } else if (tasks.length > 0 && pageState === 'loading') {
      setPageState('no_data');
    } else if (tasks.length === 0 && pageState === 'loading') {
      const timer = setTimeout(() => {
        setPageState((s) => (s === 'loading' ? 'no_data' : s));
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [tasks, pageState, loc.state?.reportJobId]);

  // Cleanup progress timer on unmount
  useEffect(() => () => {
    if (progressTimerRef.current) clearInterval(progressTimerRef.current);
  }, []);

  // Client-side progress animation — independent of API polling
  useEffect(() => {
    if (pageState !== 'generating') {
      if (progressTimerRef.current) { clearInterval(progressTimerRef.current); progressTimerRef.current = null; }
      return;
    }
    progressTimerRef.current = setInterval(() => {
      setGenProgress((prev) => {
        if (prev >= 90) return prev;
        if (prev >= 70) return prev + Math.random() * 2;
        return prev + Math.random() * 6;
      });
    }, 600);
    return () => {
      if (progressTimerRef.current) { clearInterval(progressTimerRef.current); progressTimerRef.current = null; }
    };
  }, [pageState]);

  // Unified polling for report job status
  usePolling({
    enabled: pageState === 'generating' && !!pollJobId,
    intervalMs: 2000,
    maxIntervalMs: 10_000,
    backoffFactor: 1.5,
    maxRetries: 300,
    immediate: true,
    visibilityAware: true,
    onTick: async () => {
      const jId = pollJobId;
      if (!jId) return false;

      const status = await getAIJobStatus(jId);
      if (!status.ok) {
        setPageState('error');
        setError(status.message);
        return false;
      }

      const s = status.data.status;

      if (isSuccessStatus(s)) {
        setGenProgress(100);
        setGenStage('完成');

        const r = await getAIJobResult(jId);
        if (!r.ok) {
          setPageState('error');
          setError(r.message || '获取报告结果失败');
          return false;
        }

        const adapted = adaptReportResult(r.data);
        if (adapted) {
          setReport(adapted);
          setPageState('preview');
          useToastStore.getState().addToast({
            type: 'success',
            message: '科研报告生成完成',
            description: '可查看、导出或返回工作区继续分析',
            dedupKey: 'report-generation',
          });
        } else {
          setPageState('error');
          setError('报告结果解析失败：数据结构不匹配');
          useToastStore.getState().addToast({
            type: 'error',
            message: '报告解析失败',
            description: '数据结构不匹配，请联系管理员',
            dedupKey: 'report-generation',
          });
        }
        return false;
      }

      if (isFailedStatus(s)) {
        setPageState('error');
        setError(status.data.error_message || status.data.user_facing_error?.user_message || '报告生成失败');
        useToastStore.getState().addToast({
          type: 'error',
          message: '报告生成失败',
          description: status.data.error_message || '请检查错误日志并重试',
          dedupKey: 'report-generation',
        });
        return false;
      }

      // Running — update progress from backend
      if (typeof status.data.progress === 'number') {
        setGenProgress((prev) => Math.max(prev, status.data.progress));
      }
      if (status.data.progress_stage) {
        setGenStage(status.data.progress_stage);
      }

      return true;
    },
    onError: () => {
      setPageState('error');
      setError('轮询报告状态时出错');
    },
  });

  const handleGenerate = async () => {
    if (!selectedJobIds.length) return;

    setPageState('generating');
    setPollJobId(null);
    setError(null);
    setGenProgress(0);
    setGenStage('创建报告任务...');

    const jobResult = await createAIReportJob(pid, {
      report_type: 'full',
      language: 'zh-CN',
      selected_job_ids: selectedJobIds,
      include_figures: true,
      include_tables: true,
      include_ai_interpretation: true,
    });

    if (!jobResult.ok) {
      setPageState('error');
      setError(jobResult.message);
      return;
    }

    const jId = jobResult.data.job_id;
    setGeneratingJobId(jId);
    setGenProgress(5);
    setGenStage('报告生成中...');
    // Trigger polling by setting the job ID
    setPollJobId(jId);
  };

  const toggleJob = (jobId: string) => {
    setSelectedJobIds((prev) =>
      prev.includes(jobId) ? prev.filter((j) => j !== jobId) : [...prev, jobId]
    );
  };

  // ===== Loading =====
  if (pageState === 'loading') {
    return (
      <PageShell>
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-text-muted">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="font-heading">加载项目数据...</span>
          </div>
        </div>
      </PageShell>
    );
  }

  // ===== Preview =====
  if (pageState === 'preview' && report) {
    return (
      <PageShell>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xl font-heading font-bold text-text-primary">科研报告</h2>
            <p className="text-sm text-text-muted mt-0.5">{currentProject?.name || `项目 ${pid}`}</p>
          </div>
          <div className="flex gap-2">
            <SecondaryButton onClick={() => { setPageState('selecting'); setReport(null); }}>
              重新生成
            </SecondaryButton>
            <PrimaryButton onClick={() => nav(`/projects/${pid}`)}>
              返回工作区
            </PrimaryButton>
          </div>
        </div>
        <ReportViewer
          report={report}
          onExport={(format) => console.log('Export:', format)}
        />
      </PageShell>
    );
  }

  // ===== Generating =====
  if (pageState === 'generating') {
    return (
      <PageShell>
        <div className="max-w-lg mx-auto py-16">
          <DashboardCard padding="lg" className="text-center space-y-5">
            <div className="w-16 h-16 mx-auto rounded-full bg-blue-50 flex items-center justify-center">
              <svg className="animate-spin h-8 w-8 text-navy-600" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
            <div>
              <h3 className="font-heading font-semibold text-text-primary">正在生成科研报告</h3>
              <p className="text-sm text-text-muted mt-1">
                {genStage}
                {generatingJobId && <span className="font-mono text-[10px] ml-1">({generatingJobId})</span>}
              </p>
            </div>
            <div className="space-y-1">
              <ProgressBar value={genProgress} size="sm" />
              <p className="text-xs text-text-muted">{Math.round(genProgress)}%</p>
            </div>
            <p className="text-xs text-text-muted">
              正在整合 {selectedJobIds.length} 个已完成分析的结果...
            </p>
          </DashboardCard>
        </div>
      </PageShell>
    );
  }

  // ===== Error =====
  if (pageState === 'error') {
    return (
      <PageShell>
        <div className="max-w-lg mx-auto py-16">
          <DashboardCard padding="lg" className="text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-red-50 flex items-center justify-center">
              <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            <h3 className="font-heading font-semibold text-text-primary">报告生成失败</h3>
            <p className="text-sm text-red-500">{error}</p>
            <div className="flex justify-center gap-2">
              <SecondaryButton onClick={() => setPageState('selecting')}>返回选择</SecondaryButton>
              <PrimaryButton onClick={handleGenerate}>重试</PrimaryButton>
            </div>
          </DashboardCard>
        </div>
      </PageShell>
    );
  }

  // ===== Selecting (default) or No Data =====
  const completedTasks = tasks.filter((t) => t.status === 'success');
  const allSelected = completedTasks.length > 0 && selectedJobIds.length === completedTasks.length;

  return (
    <PageShell>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-heading font-bold text-text-primary">科研报告生成</h2>
          <p className="text-sm text-text-muted mt-0.5">
            {currentProject?.name || `项目 ${pid}`} — 选择已完成的分析任务来生成报告
          </p>
        </div>
        <PrimaryButton onClick={handleGenerate} disabled={selectedJobIds.length === 0}>
          生成报告 ({selectedJobIds.length})
        </PrimaryButton>
      </div>

      {pageState === 'no_data' || completedTasks.length === 0 ? (
        <DashboardCard padding="lg" className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-surface-alt flex items-center justify-center">
            <svg className="w-8 h-8 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <p className="text-sm font-heading font-medium text-text-primary mb-1">暂无已完成的分析任务</p>
          <p className="text-xs text-text-muted mb-4">请先在项目工作区运行至少一个分析任务</p>
          <SecondaryButton onClick={() => nav(`/projects/${pid}`)}>前往工作区</SecondaryButton>
        </DashboardCard>
      ) : (
        <div className="space-y-4">
          {/* Select all */}
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={() => setSelectedJobIds(allSelected ? [] : completedTasks.map((t) => String(t.id)))}
                className="w-4 h-4 rounded border-border text-navy-600 focus:ring-navy-600"
              />
              全选已完成任务
            </label>
            <span className="text-xs text-text-muted">{completedTasks.length} 个可用</span>
          </div>

          {/* Job list */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {completedTasks.map((t) => {
              const checked = selectedJobIds.includes(String(t.id));
              return (
                <label
                  key={t.id}
                  className={`card-dashboard p-4 cursor-pointer transition-card ${
                    checked ? 'border-navy-600 bg-blue-50/30 shadow-card-selected' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleJob(String(t.id))}
                      className="w-4 h-4 mt-0.5 rounded border-border text-navy-600 focus:ring-navy-600"
                    />
                    <div className="min-w-0 text-xs">
                      <p className="font-heading font-semibold text-text-primary truncate">{TASK_TYPE_LABELS[t.task_type] || t.task_name || t.task_type}</p>
                      <p className="text-text-muted mt-0.5">ID: {t.id} · {t.task_type}</p>
                      <p className="text-[10px] text-text-muted mt-1">
                        {t.finished_at ? new Date(t.finished_at).toLocaleString() : '—'}
                      </p>
                    </div>
                    {checked && (
                      <svg className="w-4 h-4 text-navy-600 shrink-0 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    )}
                  </div>
                </label>
              );
            })}
          </div>

          {/* Bottom actions */}
          <div className="flex items-center justify-between pt-2 border-t border-border">
            <p className="text-xs text-text-muted">
              已选择 {selectedJobIds.length}/{completedTasks.length} 个任务
            </p>
            <div className="flex gap-2">
              <SecondaryButton onClick={() => nav(`/projects/${pid}`)}>
                返回工作区
              </SecondaryButton>
              <PrimaryButton onClick={handleGenerate} disabled={selectedJobIds.length === 0}>
                生成报告
              </PrimaryButton>
            </div>
          </div>
        </div>
      )}
    </PageShell>
  );
}
