import DashboardCard from '../shared/DashboardCard';

export type WorkflowKey = 'gwas' | 'mr' | 'mediation';

export interface WorkflowDef {
  key: WorkflowKey;
  title: string;
  subtitle: string;
  description: string;
  color: 'blue' | 'gold';
  letter: string;
}

export const WORKFLOWS: WorkflowDef[] = [
  {
    key: 'gwas',
    title: '全基因组关联分析（GWAS）',
    subtitle: 'GWAS',
    description: '通过大规模基因组扫描，识别与体脂表型相关联的遗传变异。',
    color: 'blue',
    letter: 'A',
  },
  {
    key: 'mr',
    title: '孟德尔随机化分析（MR）',
    subtitle: 'MR',
    description: '利用遗传工具变量，估计脂肪性状对疾病结局的因果效应。',
    color: 'blue',
    letter: 'B',
  },
  {
    key: 'mediation',
    title: '中介机制筛选',
    subtitle: '中介 MR',
    description: '通过多步 MR 发现连接脂肪性状与疾病结局的血浆蛋白中介因子。',
    color: 'gold',
    letter: 'C',
  },
];

function WorkflowIcon({ type, size }: { type: WorkflowKey; size?: number }) {
  const s = size || 32;
  switch (type) {
    case 'gwas':
      return (
        <svg width={s} height={s} viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="currentColor" fillOpacity="0.1" />
          <path d="M8 24V8l4 4 4-4 4 4 4-4v16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <circle cx="14" cy="17" r="1.5" fill="currentColor" />
          <circle cx="20" cy="13" r="1.5" fill="currentColor" />
          <circle cx="10" cy="20" r="1.5" fill="currentColor" />
        </svg>
      );
    case 'mr':
      return (
        <svg width={s} height={s} viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="currentColor" fillOpacity="0.1" />
          <line x1="6" y1="26" x2="6" y2="6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="6" y1="26" x2="26" y2="26" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="12" cy="18" r="2.5" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="1.2" />
          <circle cx="17" cy="14" r="2.5" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="1.2" />
          <circle cx="22" cy="10" r="2.5" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="1.2" />
          <line x1="14" y1="17" x2="15.5" y2="16" stroke="currentColor" strokeWidth="1" />
          <line x1="18.5" y1="13" x2="20.5" y2="11.5" stroke="currentColor" strokeWidth="1" />
        </svg>
      );
    case 'mediation':
      return (
        <svg width={s} height={s} viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="currentColor" fillOpacity="0.1" />
          <circle cx="10" cy="16" r="4.5" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="1.2" />
          <circle cx="22" cy="16" r="4.5" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="1.2" />
          <line x1="14.5" y1="16" x2="17.5" y2="16" stroke="currentColor" strokeWidth="1.5" />
          <path d="M17 13l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
      );
  }
}

interface CardProps {
  workflow: WorkflowDef;
  selected: boolean;
  onClick: () => void;
}

function WorkflowSelectionCard({ workflow, selected, onClick }: CardProps) {
  const isGold = workflow.color === 'gold';

  const baseBorder = selected
    ? 'border-gold-500 shadow-card-selected'
    : `border-border hover:border-${isGold ? 'gold-400' : 'blue-400'} hover:shadow-card-hover`;

  const bg = selected
    ? (isGold ? 'bg-gold-50' : 'bg-blue-50')
    : 'bg-white';

  const iconColor = isGold
    ? (selected ? 'var(--color-gold-500)' : 'var(--color-gold-400)')
    : (selected ? 'var(--color-navy-600)' : 'var(--color-blue-400)');

  return (
    <button
      onClick={onClick}
      className={`
        card-dashboard ${bg} ${baseBorder}
        flex flex-col items-center gap-2 p-3 text-center w-full
        transition-card cursor-pointer
        focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-600
      `}
    >
      {/* Letter badge */}
      <div className={`
        w-6 h-6 rounded-full flex items-center justify-center text-xs font-heading font-bold shrink-0
        ${selected
          ? (isGold ? 'bg-gold-500 text-white' : 'bg-navy-600 text-white')
          : 'bg-surface text-text-muted'}
      `}>
        {workflow.letter}
      </div>

      {/* Icon */}
      <div style={{ color: iconColor }}>
        <WorkflowIcon type={workflow.key} size={28} />
      </div>

      {/* Title + subtitle */}
      <div>
        <h4 className={`font-heading font-semibold text-xs leading-tight ${selected ? 'text-text-primary' : 'text-text-secondary'}`}>
          {workflow.title}
        </h4>
        <p className={`text-[11px] font-medium mt-0.5 ${selected && isGold ? 'text-gold-600' : 'text-text-muted'}`}>
          {workflow.subtitle}
        </p>
      </div>

      {/* Selected indicator */}
      {selected && (
        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${isGold ? 'bg-gold-500' : 'bg-navy-600'}`}>
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
      )}
    </button>
  );
}

interface Props {
  selected: WorkflowKey;
  onSelect: (key: WorkflowKey) => void;
}

export default function WorkflowSelectionPanel({ selected, onSelect }: Props) {
  return (
    <DashboardCard padding="lg">
      {/* Section header with numbered badge */}
      <div className="flex items-center gap-3 mb-4">
        <span className="shrink-0 w-7 h-7 rounded-lg bg-navy-700 text-white flex items-center justify-center text-xs font-heading font-bold">
          2
        </span>
        <div>
          <h3 className="section-title">分析流程选择</h3>
          <p className="text-xs text-text-muted mt-0.5">为您的研究选择合适的分析流程</p>
        </div>
      </div>

      {/* Three workflow cards — horizontal */}
      <div className="grid grid-cols-3 sm:grid-cols-3 gap-2 md:gap-2.5">
        {WORKFLOWS.map((wf) => (
          <WorkflowSelectionCard
            key={wf.key}
            workflow={wf}
            selected={selected === wf.key}
            onClick={() => onSelect(wf.key)}
          />
        ))}
      </div>

      {/* Compact descriptions */}
      <div className="mt-3 space-y-1.5">
        {WORKFLOWS.map((wf) => {
          const isSelected = selected === wf.key;
          return (
            <div
              key={`desc-${wf.key}`}
              className={`text-xs leading-relaxed px-1 transition-card ${
                isSelected ? 'text-text-secondary' : 'text-text-muted'
              }`}
            >
              <span className={`font-heading font-semibold mr-1 ${isSelected ? 'text-gold-600' : 'text-text-muted'}`}>
                {wf.letter}.
              </span>
              {wf.description}
            </div>
          );
        })}
      </div>
    </DashboardCard>
  );
}
