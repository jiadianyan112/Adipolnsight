import DashboardCard from './DashboardCard';

interface Metric {
  label: string;
  value: string;
  unit?: string;
  highlight?: boolean;
}

interface Props {
  title?: string;
  metrics: Metric[];
  columns?: 2 | 3 | 4;
  className?: string;
}

const colMap: Record<number, string> = {
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
};

export default function MetricSummaryCard({ title, metrics, columns = 4, className = '' }: Props) {
  return (
    <DashboardCard className={className}>
      {title && <h4 className="section-title-sm mb-3">{title}</h4>}
      <div className={`grid ${colMap[columns]} gap-3`}>
        {metrics.map((m) => (
          <div
            key={m.label}
            className={`rounded-lg p-3 ${m.highlight ? 'bg-blue-50 border border-blue-100' : 'bg-surface'}`}
          >
            <p className="text-xs text-text-muted mb-1 truncate">{m.label}</p>
            <div className="flex items-baseline gap-1">
              <span className="text-sm font-bold text-text-primary font-heading">{m.value}</span>
              {m.unit && <span className="text-xs text-text-muted">{m.unit}</span>}
            </div>
          </div>
        ))}
      </div>
    </DashboardCard>
  );
}
