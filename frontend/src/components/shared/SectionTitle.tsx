import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  subtitle?: string;
  className?: string;
  as?: 'h2' | 'h3' | 'h4';
}

export default function SectionTitle({ children, subtitle, className = '', as: Tag = 'h3' }: Props) {
  return (
    <div className={`mb-3 ${className}`}>
      <Tag className="section-title">{children}</Tag>
      {subtitle && (
        <p className="text-xs text-text-muted mt-1 font-body">{subtitle}</p>
      )}
    </div>
  );
}
