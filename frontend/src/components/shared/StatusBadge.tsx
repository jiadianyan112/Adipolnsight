const variantMap: Record<string, string> = {
  pending: 'bg-surface text-text-muted',
  running: 'bg-blue-100 text-navy-700',
  success: 'bg-green-100 text-green-600',
  failed: 'bg-danger-100 text-danger-600',
  cancelled: 'bg-gold-100 text-gold-600',
};

const dotMap: Record<string, string> = {
  pending: 'bg-text-muted',
  running: 'bg-navy-600 animate-pulse',
  success: 'bg-green-500',
  failed: 'bg-danger-600',
  cancelled: 'bg-gold-500',
};

const labelMap: Record<string, string> = {
  pending: '待开始',
  running: '运行中',
  success: '已完成',
  failed: '失败',
  cancelled: '已取消',
  active: '进行中',
  draft: '草稿',
  completed: '已完成',
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium font-heading ${variantMap[status] || variantMap.pending}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotMap[status] || dotMap.pending}`} />
      {labelMap[status] || status}
    </span>
  );
}
