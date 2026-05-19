import { PIPELINE_ORDER, TASK_TYPE_LABELS } from '../../types';
import type { AnalysisTask } from '../../types';
import {
  normalizeJobStatus,
  STATUS_LABEL,
  STATUS_UI,
} from '../../utils/jobStatus';

interface Props { tasks: AnalysisTask[]; }

export default function WorkflowStepper({ tasks }: Props) {
  const statusMap: Record<string, string> = {};
  tasks.forEach((t) => { statusMap[t.task_type] = t.status; });

  return (
    <div className="flex items-center gap-0 overflow-x-auto py-3">
      {PIPELINE_ORDER.map((tt, i) => {
        const raw = statusMap[tt] || '';
        const ns = normalizeJobStatus(raw);
        const cfg = STATUS_UI[ns];
        const label = TASK_TYPE_LABELS[tt] || tt;
        const isLast = i === PIPELINE_ORDER.length - 1;

        return (
          <div key={tt} className="flex items-center shrink-0">
            {/* Step node */}
            <div className="flex flex-col items-center gap-1">
              <div className={`w-3 h-3 rounded-full ${cfg.dot} ring-2 ring-offset-1 ${ns === 'running' ? 'ring-navy-200 ring-offset-white' : 'ring-transparent'}`} />
              <div className="flex flex-col items-center">
                <span className={`text-[10px] font-heading font-semibold leading-tight ${cfg.text}`}>
                  {i + 1}
                </span>
                <span className={`text-[9px] font-medium leading-tight whitespace-nowrap ${cfg.text} opacity-80`}>
                  {label}
                </span>
                <span className={`text-[8px] leading-tight ${cfg.text} opacity-60`}>
                  {STATUS_LABEL[ns]}
                </span>
              </div>
            </div>

            {/* Connector line */}
            {!isLast && (
              <div className="flex items-center px-1.5 -mt-3">
                <div className={`h-0.5 w-6 rounded-full ${cfg.line}`} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
