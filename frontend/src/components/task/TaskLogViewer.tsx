import type { AnalysisTask } from '../../types';

export default function TaskLogViewer({ task }: { task: AnalysisTask }) {
  return (
    <div className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs font-mono space-y-1 overflow-auto max-h-64">
      <div><span className="text-gray-500">[task_id]</span> {task.id}</div>
      <div><span className="text-gray-500">[status]</span> {task.status}</div>
      <div><span className="text-gray-500">[progress]</span> {task.progress}%</div>
      <div><span className="text-gray-500">[started]</span> {task.started_at || 'N/A'}</div>
      <div><span className="text-gray-500">[finished]</span> {task.finished_at || 'N/A'}</div>
      {task.error_code && <div className="text-red-400"><span className="text-gray-500">[error]</span> [{task.error_code}] {task.error_message}</div>}
      <div className="text-gray-500 mt-2">--- stdout preview ---</div>
      <div>{task.output_json || '(empty)'}</div>
    </div>
  );
}
