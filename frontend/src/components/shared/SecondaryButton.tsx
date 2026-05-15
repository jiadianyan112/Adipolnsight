import type { ReactNode, ButtonHTMLAttributes } from 'react';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: 'sm' | 'md';
}

const sizeMap: Record<string, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
};

export default function SecondaryButton({
  children,
  size = 'md',
  className = '',
  disabled,
  ...rest
}: Props) {
  return (
    <button
      disabled={disabled}
      className={`
        inline-flex items-center justify-center gap-2 rounded-button
        font-heading font-medium
        border border-border bg-white text-text-secondary
        hover:bg-surface hover:text-text-primary hover:border-navy-600
        ${sizeMap[size]}
        transition-card
        disabled:opacity-50 disabled:cursor-not-allowed
        focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-600
        ${className}
      `}
      {...rest}
    >
      {children}
    </button>
  );
}
