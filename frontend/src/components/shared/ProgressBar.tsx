interface Props {
  value: number;
  size?: 'sm' | 'md';
  showLabel?: boolean;
}

export default function ProgressBar({ value, size = 'md', showLabel }: Props) {
  const pct = Math.min(100, Math.max(0, value));
  const h = size === 'sm' ? 'h-1.5' : 'h-2';

  return (
    <div className="w-full">
      <div className={`w-full bg-surface-alt rounded-full ${h} overflow-hidden`}>
        <div
          className={`bg-navy-600 ${h} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <p className="text-xs text-text-muted mt-1 font-medium">{pct}%</p>
      )}
    </div>
  );
}
