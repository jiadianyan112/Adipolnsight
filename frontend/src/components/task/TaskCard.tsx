import type { AnalysisTask } from '../../types';
import { TASK_TYPE_LABELS } from '../../types';
import { isSuccessRaw, isFailedRaw, isActiveRaw } from '../../utils/jobStatus';
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
  const hasResult = isSuccessRaw(task.status);
  const isRunning = isActiveRaw(task.status);
  const isFailed = isFailedRaw(task.status);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-medium text-sm text-gray-800">{TASK_TYPE_LABELS[task.task_type] || task.task_name}</h4>
        <StatusBadge status={task.status || 'pending'} />
      </div>
      {isRunning && <ProgressBar value={task.progress} />}
      {isFailed && <ErrorAlert code={task.error_code} message={task.error_message} />}
      <div className="flex gap-2 mt-3">
        {!task.id ? (
          <button onClick={() => onRun(task.task_type)}
            className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700">
            运行
          </button>
        ) : null}
        {hasResult && (
          <button onClick={() => onViewResult(task.id)}
            className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">
            查看结果
          </button>
        )}
        {isFailed && (
          <button onClick={() => onRerun(task.id)}
            className="bg-orange-500 text-white px-3 py-1 rounded text-xs hover:bg-orange-600">
            重新运行
          </button>
        )}
      </div>
    </div>
  );
}
