import { type AnalysisResult } from '../../types';

function SummaryCards({ summary }: { summary: Record<string, any> }) {
  if (!summary || Object.keys(summary).length === 0) {
    return <p className="text-sm text-gray-400">No summary data available.</p>;
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
      <h4 className="text-sm font-medium text-gray-700 mb-2">Output Files</h4>
      <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        {files.map((f, i) => (
          <div key={i} className="px-3 py-2 text-xs text-gray-600 border-b last:border-0 font-mono">
            {f}
          </div>
        ))}
        {files.length === 0 && <div className="px-3 py-4 text-xs text-gray-400 text-center">No output files</div>}
      </div>
    </div>
  );
}

export default function UnifiedResultView({ result }: { result: AnalysisResult }) {
  let summary: Record<string, any> = {};
  let files: string[] = [];

  try { summary = JSON.parse(result.summary_json); } catch (_) {}
  try { files = JSON.parse(result.output_files_json); } catch (_) {}

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-800 mb-4">Analysis Result — {result.result_type}</h3>
      <SummaryCards summary={summary} />
      <DataTable files={files} />
    </div>
  );
}
