import type { AnalysisTask } from '../../types';
import { TASK_TYPE_LABELS } from '../../types';
import StatusBadge from '../shared/StatusBadge';
import ProgressBar from '../shared/ProgressBar';
import ErrorAlert from '../shared/ErrorAlert';

interface Props {
  task: AnalysisTask;
  onRun: (taskType: string) => void;
  onViewResult: (taskId: number) => void;
  onRerun: (taskId: number) => void;
}

export default function TaskCard({ task, onRun, onViewResult, onRerun }: Props) {
  const hasResult = task.status === 'success';
  const isRunning = task.status === 'running' || task.status === 'pending';
  const isFailed = task.status === 'failed';

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-medium text-sm text-gray-800">{task.task_name || TASK_TYPE_LABELS[task.task_type]}</h4>
        <StatusBadge status={task.status || 'pending'} />
      </div>
      {isRunning && <ProgressBar value={task.progress} />}
      {isFailed && <ErrorAlert code={task.error_code} message={task.error_message} />}
      <div className="flex gap-2 mt-3">
        {!task.id ? (
          <button onClick={() => onRun(task.task_type)}
            className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700">
            Run
          </button>
        ) : null}
        {hasResult && (
          <button onClick={() => onViewResult(task.id)}
            className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">
            View Result
          </button>
        )}
        {isFailed && (
          <button onClick={() => onRerun(task.id)}
            className="bg-orange-500 text-white px-3 py-1 rounded text-xs hover:bg-orange-600">
            Rerun
          </button>
        )}
      </div>
    </div>
  );
}
