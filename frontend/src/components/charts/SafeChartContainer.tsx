import { useState, useRef, useEffect, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  minHeight?: number;
  className?: string;
  fallback?: ReactNode;
}

function DefaultPlaceholder({ height }: { height: number }) {
  return (
    <div
      className="flex items-center justify-center rounded-lg bg-surface-alt"
      style={{ height }}
    >
      <div className="flex flex-col items-center gap-2 text-text-muted">
        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-[10px]">加载图表...</span>
      </div>
    </div>
  );
}

/**
 * 安全的图表容器 — 仅在父容器拥有正宽高时才渲染子图表。
 *
 * 解决问题：Recharts 的 ResponsiveContainer 通过 ResizeObserver 测量父容器尺寸，
 * 若父容器在渲染时刻为 width=0 / height=0，Recharts 会在控制台反复输出：
 *   The width(-1) and height(-1) of chart should be greater than 0
 */
export default function SafeChartContainer({
  children,
  minHeight = 200,
  className = '',
  fallback,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const check = () => {
      if (!el) return;
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {
        setReady(true);
      }
    };

    requestAnimationFrame(check);

    const ro = new ResizeObserver(() => check());
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={className}
      style={{ width: '100%', minHeight }}
    >
      {ready ? children : fallback ? fallback : <DefaultPlaceholder height={minHeight} />}
    </div>
  );
}
