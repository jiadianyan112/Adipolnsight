import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  selected?: boolean;
  className?: string;
  onClick?: () => void;
  padding?: 'sm' | 'md' | 'lg';
}

const padMap: Record<string, string> = {
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-5',
};

export default function DashboardCard({ children, selected, className = '', onClick, padding = 'md' }: Props) {
  return (
    <div
      onClick={onClick}
      className={`card-dashboard ${padMap[padding]} ${selected ? 'selected' : ''} ${onClick ? 'cursor-pointer' : ''} ${className}`}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); } : undefined}
    >
      {children}
    </div>
  );
}
