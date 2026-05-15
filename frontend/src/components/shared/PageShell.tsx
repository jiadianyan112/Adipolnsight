import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  className?: string;
}

export default function PageShell({ children, className = '' }: Props) {
  return (
    <div className={`w-full max-w-[1440px] 2xl:max-w-[1600px] mx-auto px-4 md:px-6 py-4 md:py-5 ${className}`}>
      {children}
    </div>
  );
}
