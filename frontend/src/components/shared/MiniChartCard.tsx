import type { ReactNode } from 'react';
import { LineChart, Line, BarChart, Bar, ResponsiveContainer } from 'recharts';
import DashboardCard from './DashboardCard';

interface SparklinePoint {
  v: number;
}

interface Props {
  title: string;
  value: string;
  unit?: string;
  chart?: ReactNode;
  sparkline?: SparklinePoint[];
  sparklineColor?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  className?: string;
}

const trendColors: Record<string, string> = {
  up: 'text-green-600',
  down: 'text-danger-600',
  stable: 'text-text-muted',
};

const trendIcons: Record<string, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

function Sparkline({ data, color = 'var(--color-navy-600)' }: { data: SparklinePoint[]; color?: string }) {
  return (
    <div className="h-10 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <Line
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function MiniBar({ data, color = 'var(--color-navy-600)' }: { data: SparklinePoint[]; color?: string }) {
  return (
    <div className="h-10 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <Bar dataKey="v" fill={color} radius={[2, 2, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function MiniChartCard({
  title, value, unit, chart, sparkline, sparklineColor, trend, trendValue, className = '',
}: Props) {
  return (
    <DashboardCard padding="sm" className={`flex flex-col gap-1.5 min-w-0 ${className}`}>
      <p className="text-xs text-text-muted font-medium truncate">{title}</p>
      <div className="flex items-baseline gap-1">
        <span className="metric-value text-lg">{value}</span>
        {unit && <span className="text-xs text-text-muted">{unit}</span>}
      </div>
      {chart && <div className="flex-1 min-h-0">{chart}</div>}
      {!chart && sparkline && <Sparkline data={sparkline} color={sparklineColor} />}
      {trend && (
        <div className={`flex items-center gap-1 text-xs ${trendColors[trend]}`}>
          <span>{trendIcons[trend]}</span>
          {trendValue && <span>{trendValue}</span>}
        </div>
      )}
    </DashboardCard>
  );
}

export { MiniBar, Sparkline };
