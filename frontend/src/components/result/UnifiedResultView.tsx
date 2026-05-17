import { type AnalysisResult, type SegmentationResult as SegResultType } from '../../types';
import SegmentationResultView, { type SegmentationResultData } from './SegmentationResultView';

function SummaryCards({ summary }: { summary: Record<string, unknown> }) {
  if (!summary || Object.keys(summary).length === 0) {
    return <p className="text-sm text-text-muted">No summary data available.</p>;
  }
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      {Object.entries(summary).map(([k, v]) => {
        const displayVal = typeof v === 'object' ? JSON.stringify(v).slice(0, 60) : String(v);
        return (
          <div key={k} className="bg-blue-50 rounded-lg p-3 border border-blue-100">
            <div className="text-xs text-blue-500 mb-1">{k}</div>
            <div className="text-sm font-semibold text-gray-800 truncate">{displayVal}</div>
          </div>
        );
      })}
    </div>
  );
}

function DataTable({ files }: { files: string[] }) {
  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium text-text-secondary mb-2">Output Files</h4>
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        {files.map((f, i) => (
          <div key={i} className="px-3 py-2 text-xs text-text-secondary border-b last:border-0 font-mono">
            {f}
          </div>
        ))}
        {files.length === 0 && <div className="px-3 py-4 text-xs text-text-muted text-center">No output files</div>}
      </div>
    </div>
  );
}

/** 尝试将 summary_json 解析为 SegmentationResultData */
function tryParseSegmentation(summaryJson: string): SegmentationResultData | null {
  try {
    const obj = JSON.parse(summaryJson);
    // 检查是否包含分割结果的特征字段
    if (obj && typeof obj === 'object' && 'dice_scores' in obj && 'volume_metrics' in obj && 'segmentation_id' in obj) {
      return obj as SegmentationResultData;
    }
  } catch {
    // not JSON or not segmentation format
  }
  return null;
}

interface Props {
  result: AnalysisResult;
  /** 可选：直接传入已解析的分割结果，跳过 summary_json 解析 */
  segmentationData?: SegmentationResultData | null;
  loading?: boolean;
  error?: string | null;
  onClose?: () => void;
}

export default function UnifiedResultView({ result, segmentationData, loading, error, onClose }: Props) {
  // --- 如果是 image_segmentation 类型，渲染专用组件 ---
  if (result.result_type === 'image_segmentation') {
    // 优先使用直接传入的 data，其次从 summary_json 解析
    const data = segmentationData || tryParseSegmentation(result.summary_json);
    return (
      <SegmentationResultView
        data={data}
        loading={loading}
        error={error}
        onClose={onClose}
      />
    );
  }

  // --- 通用结果展示（其他 result_type） ---
  let summary: Record<string, unknown> = {};
  let files: string[] = [];

  try { summary = JSON.parse(result.summary_json); } catch { /* keep empty */ }
  try { files = JSON.parse(result.output_files_json); } catch { /* keep empty */ }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-text-primary mb-4">Analysis Result — {result.result_type}</h3>
      <SummaryCards summary={summary} />
      <DataTable files={files} />
    </div>
  );
}
