import { PIPELINE_ORDER, TASK_TYPE_LABELS } from '../../types';
import type { AnalysisTask } from '../../types';

interface Props { tasks: AnalysisTask[]; }

const statusConfig: Record<string, { dot: string; text: string; line: string }> = {
  success: {
    dot: 'bg-green-500',
    text: 'text-green-600',
    line: 'bg-green-300',
  },
  running: {
    dot: 'bg-navy-600 animate-pulse',
    text: 'text-navy-700 font-semibold',
    line: 'bg-navy-300',
  },
  failed: {
    dot: 'bg-danger-600',
    text: 'text-danger-600',
    line: 'bg-danger-200',
  },
  pending: {
    dot: 'bg-text-muted',
    text: 'text-text-muted',
    line: 'bg-border',
  },
  cancelled: {
    dot: 'bg-gold-400',
    text: 'text-gold-600',
    line: 'bg-gold-200',
  },
};

const statusLabels: Record<string, string> = {
  success: '已完成',
  running: '运行中',
  failed: '失败',
  pending: '待开始',
  cancelled: '已取消',
};

export default function WorkflowStepper({ tasks }: Props) {
  const statusMap: Record<string, string> = {};
  tasks.forEach((t) => { statusMap[t.task_type] = t.status; });

  return (
    <div className="flex items-center gap-0 overflow-x-auto py-3">
      {PIPELINE_ORDER.map((tt, i) => {
        const status = statusMap[tt] || 'pending';
        const cfg = statusConfig[status] || statusConfig.pending;
        const label = TASK_TYPE_LABELS[tt] || tt;
        const isLast = i === PIPELINE_ORDER.length - 1;

        return (
          <div key={tt} className="flex items-center shrink-0">
            {/* Step node */}
            <div className="flex flex-col items-center gap-1">
              <div className={`w-3 h-3 rounded-full ${cfg.dot} ring-2 ring-offset-1 ${status === 'running' ? 'ring-navy-200 ring-offset-white' : 'ring-transparent'}`} />
              <div className="flex flex-col items-center">
                <span className={`text-[10px] font-heading font-semibold leading-tight ${cfg.text}`}>
                  {i + 1}
                </span>
                <span className={`text-[9px] font-medium leading-tight whitespace-nowrap ${cfg.text} opacity-80`}>
                  {label}
                </span>
                <span className={`text-[8px] leading-tight ${cfg.text} opacity-60`}>
                  {statusLabels[status]}
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
