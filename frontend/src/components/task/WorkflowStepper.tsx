import { PIPELINE_ORDER, TASK_TYPE_LABELS } from '../../types';
import type { AnalysisTask } from '../../types';

interface Props { tasks: AnalysisTask[]; currentStep: number; }

export default function WorkflowStepper({ tasks, currentStep }: Props) {
  const statusMap: Record<string, string> = {};
  tasks.forEach((t) => { statusMap[t.task_type] = t.status; });

  return (
    <div className="flex items-center gap-2 mb-6 overflow-x-auto py-2">
      {PIPELINE_ORDER.map((tt, i) => {
        const status = statusMap[tt];
        const colors: Record<string, string> = {
          success: 'bg-green-500', running: 'bg-blue-500 animate-pulse',
          failed: 'bg-red-500', pending: 'bg-gray-300',
        };
        return (
          <div key={tt} className="flex items-center gap-1 shrink-0">
            <div className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded-full ${colors[status || 'pending']}`} />
              <span className={`text-xs ${status === 'running' ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                {i + 1}. {TASK_TYPE_LABELS[tt] || tt}
              </span>
            </div>
            {i < PIPELINE_ORDER.length - 1 && <div className="w-4 h-px bg-gray-300 mx-1" />}
          </div>
        );
      })}
    </div>
  );
}
