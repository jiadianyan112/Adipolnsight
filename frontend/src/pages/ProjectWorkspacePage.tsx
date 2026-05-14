import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import { useTaskStore } from '../stores/taskStore';
import { useResultStore } from '../stores/resultStore';
import ProjectHeader from '../components/project/ProjectHeader';
import WorkflowStepper from '../components/task/WorkflowStepper';
import TaskCard from '../components/task/TaskCard';
import TaskLogViewer from '../components/task/TaskLogViewer';
import UnifiedResultView from '../components/result/UnifiedResultView';
import { PIPELINE_ORDER } from '../types';

export default function ProjectWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const pid = Number(id);
  const nav = useNavigate();
  const { currentProject, fetchProject } = useProjectStore();
  const { tasks, fetchTasks, createTask, rerunTask, runFullPipeline, startPolling, stopPolling } = useTaskStore();
  const { currentResult, fetchResult, generateReport, currentReport } = useResultStore();

  const [viewingTaskId, setViewingTaskId] = useState<number | null>(null);
  const [showLog, setShowLog] = useState<number | null>(null);

  useEffect(() => {
    fetchProject(pid);
    fetchTasks(pid);
    return () => stopPolling();
  }, [pid]);

  useEffect(() => {
    startPolling(pid);
  }, []);

  if (!currentProject) return <p className="text-gray-400">Loading project...</p>;

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
    <div>
      <ProjectHeader project={currentProject} />

      <div className="flex gap-2 mb-4">
        <button onClick={handleRunAll}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">
          Run Full Pipeline
        </button>
        {hasAnySuccess && (
          <button onClick={handleGenerateReport}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700">
            Generate Report
          </button>
        )}
      </div>

      <WorkflowStepper tasks={tasks} currentStep={0} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {PIPELINE_ORDER.map((tt) => (
          <TaskCard
            key={tt}
            task={taskMap[tt] || { task_type: tt, task_name: '', status: '', progress: 0, error_code: '', error_message: '', id: 0, project_id: pid, input_json: '', output_json: '', created_at: '', updated_at: '', started_at: null, finished_at: null }}
            onRun={handleRun}
            onViewResult={handleViewResult}
            onRerun={rerunTask}
          />
        ))}
      </div>

      {viewingTaskId && currentResult && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold text-gray-800">Result Detail</h3>
            <button onClick={() => { setViewingTaskId(null); setShowLog(null); }}
              className="text-xs text-gray-400 hover:text-gray-600">Close</button>
          </div>
          <UnifiedResultView result={currentResult} />
          <button onClick={() => setShowLog(viewingTaskId)}
            className="text-sm text-blue-500 mt-2 hover:underline">View Logs</button>
        </div>
      )}

      {showLog && (
        <div className="mb-6">
          <TaskLogViewer task={tasks.find((t) => t.id === showLog)!} />
        </div>
      )}
    </div>
  );
}
