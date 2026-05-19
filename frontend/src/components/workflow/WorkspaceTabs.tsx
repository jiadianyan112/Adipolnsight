import { type NormalizedJobStatus, STATUS_LABEL, normalizeJobStatus } from '../../utils/jobStatus';
import { TASK_TYPE_LABELS, PIPELINE_ORDER } from '../../types';
import type { AnalysisTask } from '../../types';

export interface TabDef {
  key: string;
  label: string;
  stepNumber: number;
}

export const WORKSPACE_TABS: TabDef[] = PIPELINE_ORDER.map((key, i) => ({
  key,
  label: TASK_TYPE_LABELS[key] || key,
  stepNumber: i + 1,
}));

interface Props {
  activeTab: string;
  onSelect: (key: string) => void;
  tasks: AnalysisTask[];
}

export default function WorkspaceTabs({ activeTab, onSelect, tasks }: Props) {
  const taskStatusMap: Record<string, NormalizedJobStatus> = {};
  for (const t of tasks) {
    const ns = normalizeJobStatus(t.status);
    const existing = taskStatusMap[t.task_type];
    if (!existing || ns === 'succeeded' || ns === 'failed') {
      taskStatusMap[t.task_type] = ns;
    }
  }

  return (
    <div className="flex items-center gap-0.5 overflow-x-auto border-b border-border mb-5 -mx-1 px-1">
      {WORKSPACE_TABS.map((tab) => {
        const isActive = activeTab === tab.key;
        const ns = taskStatusMap[tab.key];
        const isDone = ns === 'succeeded';
        const isRunning = ns === 'running';
        const isFailed = ns === 'failed';

        return (
          <button
            key={tab.key}
            onClick={() => onSelect(tab.key)}
            className={`
              shrink-0 flex items-center gap-1.5 px-3 py-2.5 text-xs font-heading font-medium
              rounded-t-lg border border-transparent transition-colors
              ${isActive
                ? 'bg-white border-border border-b-white text-navy-700 -mb-px'
                : 'text-text-muted hover:text-text-secondary hover:bg-surface-alt'}
            `}
          >
            <span className={`
              shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold
              ${isDone ? 'bg-green-100 text-green-600' :
                isRunning ? 'bg-navy-100 text-navy-600' :
                isFailed ? 'bg-red-100 text-red-600' :
                'bg-surface-alt text-text-muted'}
            `}>
              {isDone ? '✓' : isFailed ? '!' : tab.stepNumber}
            </span>
            <span className="whitespace-nowrap hidden sm:inline">{tab.label}</span>
            {ns && ns !== 'queued' && (
              <span className={`hidden md:inline text-[9px] ml-0.5 ${isActive ? '' : 'opacity-60'}`}>
                {STATUS_LABEL[ns]}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
