import { useToastStore, TYPE_ICONS, type ToastType } from '../../stores/toastStore';

const BG: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200',
  error: 'bg-red-50 border-red-200',
  warning: 'bg-gold-50 border-gold-200',
  info: 'bg-blue-50 border-blue-200',
};

const ICON_BG: Record<ToastType, string> = {
  success: 'bg-green-500',
  error: 'bg-red-500',
  warning: 'bg-gold-500',
  info: 'bg-blue-500',
};

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const removeToast = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div
      aria-label="通知列表"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)] pointer-events-none"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className={`
            pointer-events-auto flex items-start gap-3 p-3 rounded-xl border shadow-lg
            animate-slide-in-right ${BG[t.type]}
          `}
        >
          <span className={`shrink-0 w-5 h-5 rounded-full ${ICON_BG[t.type]} text-white flex items-center justify-center text-[11px] font-bold`}>
            {TYPE_ICONS[t.type]}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-heading font-semibold text-text-primary">{t.message}</p>
            {t.description && (
              <p className="text-[10px] text-text-secondary mt-0.5">{t.description}</p>
            )}
          </div>
          <button
            onClick={() => removeToast(t.id)}
            className="shrink-0 text-text-muted hover:text-text-primary transition-colors"
            aria-label="关闭通知"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}
