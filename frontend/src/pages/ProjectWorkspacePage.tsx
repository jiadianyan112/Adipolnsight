import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import { useTaskStore } from '../stores/taskStore';
import { useResultStore } from '../stores/resultStore';
import PageShell from '../components/shared/PageShell';
import SectionTitle from '../components/shared/SectionTitle';
import DashboardCard from '../components/shared/DashboardCard';
import PrimaryButton from '../components/shared/PrimaryButton';
import SecondaryButton from '../components/shared/SecondaryButton';
import StatusBadge from '../components/shared/StatusBadge';
import ImageProcessingModule from '../components/analysis/ImageProcessingModule';
import GWASModule from '../components/analysis/GWASModule';
import MRModule from '../components/analysis/MRModule';
import MediationMRModule from '../components/analysis/MediationMRModule';
import WorkflowSelectionPanel, { type WorkflowKey } from '../components/workflow/WorkflowSelectionPanel';
import WorkflowStepper from '../components/task/WorkflowStepper';
import TaskCard from '../components/task/TaskCard';
import TaskLogViewer from '../components/task/TaskLogViewer';
import UnifiedResultView from '../components/result/UnifiedResultView';
import { PIPELINE_ORDER, TASK_TYPE_LABELS } from '../types';

export default function ProjectWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const nav = useNavigate();
  const { currentProject, fetchProject } = useProjectStore();
  const { tasks, fetchTasks, createTask, rerunTask, runFullPipeline, startPolling, stopPolling } = useTaskStore();
  const { currentResult, fetchResult, generateReport } = useResultStore();

  const [viewingTaskId, setViewingTaskId] = useState<number | null>(null);
  const [showLog, setShowLog] = useState<number | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowKey>('mediation');

  useEffect(() => {
    fetchProject(pid);
    fetchTasks(pid);
    return () => stopPolling();
  }, [pid]);

  useEffect(() => {
    startPolling(pid);
  }, []);

  if (!currentProject) {
    return (
      <PageShell>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center gap-3 text-text-muted">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="font-heading">加载项目中...</span>
          </div>
        </div>
      </PageShell>
    );
  }

  const taskMap: Record<string, any> = {};
  tasks.forEach((t) => { taskMap[t.task_type] = t; });

  const handleRun = async (taskType: string) => {
    await createTask(pid, taskType);
    startPolling(pid);
  };

  const handleViewResult = async (taskId: number) => {
    setViewingTaskId(taskId);
    await fetchResult(taskId);
  };

  const handleRunAll = async () => {
    await runFullPipeline(pid);
  };

  const handleGenerateReport = async () => {
    const report = await generateReport(pid);
    nav(`/projects/${pid}/report`, { state: { report } });
  };

  const hasAnySuccess = tasks.some((t) => t.status === 'success');

  return (
    <PageShell>
      {/* ===== Project Info Bar ===== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 p-4 card-dashboard">
        <div className="flex items-center gap-4 min-w-0">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-heading font-semibold text-text-primary truncate">
                {currentProject.name}
              </h2>
              <StatusBadge status={currentProject.status} />
            </div>
            <p className="text-sm text-text-secondary mt-0.5 truncate">{currentProject.research_goal}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 md:gap-3 text-xs text-text-secondary shrink-0 flex-wrap">
          <span className="font-medium">暴露因素：<span className="text-text-primary">{currentProject.exposure}</span></span>
          <span className="text-border">|</span>
          <span className="font-medium">结局变量：<span className="text-text-primary">{currentProject.outcome}</span></span>
          {currentProject.mediator_set && (
            <>
              <span className="text-border">|</span>
              <span className="font-medium">中介变量：<span className="text-text-primary">{currentProject.mediator_set}</span></span>
            </>
          )}
        </div>
      </div>

      {/* ===== Main Dashboard Grid ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-6">
        {/* ===== LEFT: Image Processing Module ===== */}
        <div className="lg:col-span-3">
          <ImageProcessingModule
            imageTask={taskMap['image_segmentation']}
            onViewResult={handleViewResult}
            onSaveAndContinue={handleRunAll}
          />
        </div>

        {/* ===== RIGHT: Workflow Selection + Actions ===== */}
        <div className="lg:col-span-2 space-y-4">
          <WorkflowSelectionPanel
            selected={selectedWorkflow}
            onSelect={setSelectedWorkflow}
          />

          {/* Pipeline Actions */}
          <DashboardCard padding="md">
            <div className="space-y-2">
              <PrimaryButton onClick={handleRunAll} className="w-full" size="lg">
                运行完整分析流程
              </PrimaryButton>
              {hasAnySuccess && (
                <SecondaryButton onClick={handleGenerateReport} className="w-full">
                  生成分析报告
                </SecondaryButton>
              )}
              {!hasAnySuccess && (
                <p className="text-xs text-text-muted text-center">
                  请先运行任务以启用报告生成
                </p>
              )}
            </div>
          </DashboardCard>
        </div>
      </div>

      {/* ===== Analysis Modules — Contextual View ===== */}
      <div className="space-y-5">
        {/* Contextual module based on selected workflow */}
        {selectedWorkflow === 'gwas' && (
          <GWASModule
            gwasTask={taskMap['gwas_analysis']}
            opengwasTask={taskMap['opengwas_fetch']}
            onViewResult={handleViewResult}
            onRunTask={handleRun}
          />
        )}
        {selectedWorkflow === 'mr' && (
          <MRModule
            mrTask={taskMap['mendelian_randomization']}
            onViewResult={handleViewResult}
            onRunTask={handleRun}
          />
        )}
        {selectedWorkflow === 'mediation' && (
          <MediationMRModule
            mediationTask={taskMap['mediation_mr']}
            onViewResult={handleViewResult}
            onRunTask={handleRun}
          />
        )}

        {/* Pipeline Overview — all tasks */}
        <DashboardCard padding="lg">
          <div className="flex items-center gap-3 mb-4">
            <span className="shrink-0 w-7 h-7 rounded-lg bg-surface text-text-muted flex items-center justify-center text-xs font-heading font-bold border border-border">
              4
            </span>
            <SectionTitle subtitle="完整分析流程状态与进度">
              流程总览
            </SectionTitle>
          </div>
          {/* Pipeline completion summary */}
          {(() => {
            const completed = tasks.filter((t) => t.status === 'success').length;
            const running = tasks.filter((t) => t.status === 'running').length;
            const failed = tasks.filter((t) => t.status === 'failed').length;
            const total = PIPELINE_ORDER.length;
            const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
            return (
              <div className="flex items-center gap-4 mb-4 p-3 bg-surface rounded-xl">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-full bg-white border-2 border-green-200 flex items-center justify-center">
                    <span className="text-sm font-heading font-bold text-green-600">{pct}%</span>
                  </div>
                  <div>
                    <p className="text-xs font-heading font-semibold text-text-primary">已完成 {completed}/{total}</p>
                    <p className="text-[10px] text-text-muted">
                      {running > 0 && `${running} 个运行中 · `}
                      {failed > 0 && `${failed} 个失败 · `}
                      {completed === total ? '流程完成' : '进行中'}
                    </p>
                  </div>
                </div>
                <div className="flex-1 h-2 bg-white rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${failed > 0 ? 'bg-gold-500' : 'bg-green-500'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })()}

          <WorkflowStepper tasks={tasks} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 mt-4">
            {PIPELINE_ORDER.map((tt) => (
              <TaskCard
                key={tt}
                task={taskMap[tt] || {
                  task_type: tt, task_name: '', status: '', progress: 0,
                  error_code: '', error_message: '', id: 0, project_id: pid,
                  input_json: '', output_json: '', created_at: '', updated_at: '',
                  started_at: null, finished_at: null,
                }}
                onRun={handleRun}
                onViewResult={handleViewResult}
                onRerun={rerunTask}
              />
            ))}
          </div>
        </DashboardCard>

        {/* Result Detail */}
        {viewingTaskId && currentResult && (
          <DashboardCard padding="lg">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-heading font-semibold text-text-primary">
                结果详情
                <span className="text-sm font-normal text-text-muted ml-2">
                  — {TASK_TYPE_LABELS[tasks.find((t) => t.id === viewingTaskId)?.task_type || ''] || '分析'}
                </span>
              </h3>
              <SecondaryButton
                size="sm"
                onClick={() => { setViewingTaskId(null); setShowLog(null); }}
              >
                关闭
              </SecondaryButton>
            </div>
            <UnifiedResultView result={currentResult} />
            <button
              onClick={() => setShowLog(viewingTaskId)}
              className="text-sm text-navy-600 hover:text-navy-800 mt-3 font-medium transition-card"
            >
              查看日志 →
            </button>
          </DashboardCard>
        )}

        {/* Task Log Viewer */}
        {showLog && (
          <DashboardCard padding="lg">
            <TaskLogViewer task={tasks.find((t) => t.id === showLog)!} />
          </DashboardCard>
        )}
      </div>
    </PageShell>
  );
}
