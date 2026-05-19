import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import { useTaskStore } from '../stores/taskStore';
import { useResultStore } from '../stores/resultStore';
import type { SegmentationResultData } from '../components/result/SegmentationResultView';
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
import RiskModelingModule from '../components/analysis/RiskModelingModule';
import ChatInput from '../components/agent/ChatInput';
import WorkspaceTabs, { WORKSPACE_TABS } from '../components/workflow/WorkspaceTabs';
import WorkflowStepper from '../components/task/WorkflowStepper';
import TaskCard from '../components/task/TaskCard';
import TaskLogViewer from '../components/task/TaskLogViewer';
import UnifiedResultView from '../components/result/UnifiedResultView';
import SegmentationResultView from '../components/result/SegmentationResultView';
import { PIPELINE_ORDER, TASK_TYPE_LABELS } from '../types';
import { computePipelineProgress } from '../utils/pipelineProgress';
import { isSuccessRaw } from '../utils/jobStatus';

export default function ProjectWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const nav = useNavigate();
  const { currentProject, fetchProject } = useProjectStore();
  const { tasks, fetchTasks, createTask, rerunTask, runFullPipeline, startPolling, stopPolling } = useTaskStore();
  const { currentResult, fetchResult, generateReport } = useResultStore();

  const [viewingTaskId, setViewingTaskId] = useState<number | null>(null);
  const [showLog, setShowLog] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState('image_segmentation');
  const [segmentationData, setSegmentationData] = useState<SegmentationResultData | null>(null);

  useEffect(() => {
    fetchProject(pid);
    fetchTasks(pid);
    startPolling(pid);
    return () => stopPolling();
  }, [pid]);

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

  const pipeline = computePipelineProgress(tasks, PIPELINE_ORDER);
  const hasAnySuccess = tasks.some((t) => isSuccessRaw(t.status));

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
    const result = await generateReport(pid);
    // Pass job_id so ReportPage can auto-poll
    nav(`/projects/${pid}/report`, { state: { reportJobId: result.job_id, reportStatus: result.status } });
  };

  const jumpToTab = (taskType: string) => {
    const exists = WORKSPACE_TABS.find((t) => t.key === taskType);
    if (exists) setActiveTab(taskType);
  };

  return (
    <PageShell>
      {/* ===== Project Info Bar ===== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 p-4 card-dashboard">
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
          <span className="font-medium">暴露：<span className="text-text-primary">{currentProject.exposure}</span></span>
          <span className="text-border">|</span>
          <span className="font-medium">结局：<span className="text-text-primary">{currentProject.outcome}</span></span>
          {currentProject.mediator_set && (
            <>
              <span className="text-border">|</span>
              <span className="font-medium">中介：<span className="text-text-primary">{currentProject.mediator_set}</span></span>
            </>
          )}
        </div>
      </div>

      {/* ===== AI Agent Chat Input ===== */}
      <div className="mb-4">
        <ChatInput
          projectId={pid}
          context={{
            exposure: currentProject?.exposure || 'Liver_PDFF',
            outcome: currentProject?.outcome || 'Osteoporosis',
          }}
        />
      </div>

      {/* ===== Pipeline Quick Bar ===== */}
      <div className="flex items-center gap-4 mb-4 p-3 bg-white rounded-xl border border-border">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-white border-2 border-green-200 flex items-center justify-center">
            <span className="text-sm font-heading font-bold text-green-600">{pipeline.percent}%</span>
          </div>
          <div>
            <p className="text-xs font-heading font-semibold text-text-primary">
              已完成 {pipeline.completed}/{pipeline.total}
            </p>
            <p className="text-[10px] text-text-muted">
              {pipeline.running > 0 && `${pipeline.running} 进行中 · `}
              {pipeline.failed > 0 && `${pipeline.failed} 失败 · `}
              {pipeline.completed === pipeline.total ? '全部完成' : '进行中'}
            </p>
          </div>
        </div>
        <div className="flex-1 h-2 bg-surface-alt rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${pipeline.failed > 0 ? 'bg-gold-500' : 'bg-green-500'}`}
            style={{ width: `${pipeline.percent}%` }}
          />
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <PrimaryButton onClick={handleRunAll} size="sm">运行全部</PrimaryButton>
          {hasAnySuccess && (
            <SecondaryButton onClick={handleGenerateReport} size="sm">生成报告</SecondaryButton>
          )}
        </div>
      </div>

      {/* ===== Workspace Tabs ===== */}
      <WorkspaceTabs activeTab={activeTab} onSelect={setActiveTab} tasks={tasks} />

      {/* ===== Tab Content ===== */}
      <div className="space-y-5 mb-6">
        {activeTab === 'image_segmentation' && (
          <ImageProcessingModule
            imageTask={taskMap['image_segmentation']}
            projectId={pid}
            onViewResult={handleViewResult}
            onSaveAndContinue={handleRunAll}
            onSegmentationComplete={(data) => {
              setSegmentationData(data);
              setViewingTaskId(0);
            }}
          />
        )}

        {activeTab === 'gwas_analysis' && (
          <GWASModule
            gwasTask={taskMap['gwas_analysis']}
            opengwasTask={taskMap['opengwas_fetch']}
            projectId={pid}
            phenotypeName={currentProject?.exposure || 'Liver_PDFF'}
            onViewResult={handleViewResult}
            onRunTask={(taskType) => { handleRun(taskType); jumpToTab(taskType); }}
            onGWASComplete={(_data) => setSegmentationData(null)}
          />
        )}

        {activeTab === 'opengwas_fetch' && (
          <DashboardCard padding="lg">
            <h3 className="font-heading font-semibold text-text-primary mb-3">OpenGWAS 数据获取</h3>
            <p className="text-sm text-text-secondary mb-4">
              从 OpenGWAS 公共数据库获取 GWAS 汇总统计数据，用于双样本孟德尔随机化分析。
            </p>
            {taskMap['opengwas_fetch'] && taskMap['opengwas_fetch'].status ? (
              <TaskCard
                task={taskMap['opengwas_fetch']}
                onRun={handleRun}
                onViewResult={handleViewResult}
                onRerun={rerunTask}
              />
            ) : (
              <div className="text-center py-8 text-text-muted">
                <p className="text-sm mb-2">尚无 OpenGWAS 数据任务</p>
                <p className="text-xs mb-3">运行 GWAS 分析或完整流水线将自动创建</p>
                <PrimaryButton onClick={() => handleRun('opengwas_fetch')} size="sm">
                  手动创建 OpenGWAS 任务
                </PrimaryButton>
              </div>
            )}
          </DashboardCard>
        )}

        {activeTab === 'mendelian_randomization' && (
          <MRModule
            mrTask={taskMap['mendelian_randomization']}
            projectId={pid}
            exposureName={currentProject?.exposure || 'Liver_PDFF'}
            outcomeName={currentProject?.outcome || 'Osteoporosis'}
            onViewResult={handleViewResult}
            onRunTask={(taskType) => { handleRun(taskType); jumpToTab(taskType); }}
          />
        )}

        {activeTab === 'mediation_mr' && (
          <MediationMRModule
            mediationTask={taskMap['mediation_mr']}
            projectId={pid}
            exposureName={currentProject?.exposure || 'Liver_PDFF'}
            outcomeName={currentProject?.outcome || 'Osteoporosis'}
            onViewResult={handleViewResult}
            onRunTask={(taskType) => { handleRun(taskType); jumpToTab(taskType); }}
          />
        )}

        {activeTab === 'risk_modeling' && (
          <RiskModelingModule
            riskTask={taskMap['risk_modeling']}
            projectId={pid}
            exposureName={currentProject?.exposure || 'Liver_PDFF'}
            outcomeName={currentProject?.outcome || 'Osteoporosis'}
            onViewResult={handleViewResult}
            onRunTask={(taskType) => { handleRun(taskType); jumpToTab(taskType); }}
          />
        )}

        {activeTab === 'report_generation' && (
          <DashboardCard padding="lg">
            <h3 className="font-heading font-semibold text-text-primary mb-3">科研报告</h3>
            <p className="text-sm text-text-secondary mb-4">
              整合所有已完成的分析结果，生成完整的科研分析报告。
            </p>
            {hasAnySuccess ? (
              <div className="space-y-3">
                <p className="text-xs text-text-muted">
                  已有 {pipeline.completed} 个分析步骤完成，可以基于当前结果生成报告。
                </p>
                <PrimaryButton onClick={handleGenerateReport}>
                  生成科研报告
                </PrimaryButton>
              </div>
            ) : (
              <div className="text-center py-8 text-text-muted">
                <p className="text-sm mb-2">暂无已完成的分析任务</p>
                <p className="text-xs">请先运行至少一个分析任务</p>
              </div>
            )}
          </DashboardCard>
        )}
      </div>

      {/* ===== Pipeline Overview — collapsed at bottom ===== */}
      <details className="mb-6 group" open={pipeline.completed === pipeline.total}>
        <summary className="flex items-center gap-2 cursor-pointer p-3 card-dashboard list-none">
          <svg className="w-4 h-4 text-text-muted group-open:rotate-90 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          <SectionTitle subtitle={`${pipeline.completed}/${pipeline.total} 步骤完成`}>
            流程总览
          </SectionTitle>
          {pipeline.failed > 0 && (
            <span className="text-xs text-red-500 font-heading ml-auto">{pipeline.failed} 失败</span>
          )}
        </summary>
        <div className="p-4 bg-white border border-t-0 border-border rounded-b-xl space-y-3">
          <WorkflowStepper tasks={tasks} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
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
        </div>
      </details>

      {/* ===== Result Detail — from ImageProcessingModule (segmentation) ===== */}
      {viewingTaskId === 0 && segmentationData && (
        <SegmentationResultView
          data={segmentationData}
          onClose={() => { setViewingTaskId(null); setSegmentationData(null); }}
        />
      )}

      {/* ===== Result Detail — from legacy AnalysisTask ===== */}
      {viewingTaskId && viewingTaskId !== 0 && currentResult && (
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
          <UnifiedResultView
            result={currentResult}
            segmentationData={currentResult.result_type === 'image_segmentation' ? segmentationData : null}
            onClose={() => { setViewingTaskId(null); setShowLog(null); }}
          />
          <button
            onClick={() => setShowLog(viewingTaskId!)}
            className="text-sm text-navy-600 hover:text-navy-800 mt-3 font-medium transition-card"
          >
            查看日志 →
          </button>
        </DashboardCard>
      )}

      {/* ===== Task Log Viewer ===== */}
      {showLog && (
        <DashboardCard padding="lg">
          <TaskLogViewer task={tasks.find((t) => t.id === showLog)!} />
        </DashboardCard>
      )}
    </PageShell>
  );
}
