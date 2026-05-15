import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useResultStore } from '../stores/resultStore';
import ReportViewer from '../components/report/ReportViewer';
import PageShell from '../components/shared/PageShell';

export default function ReportPage() {
  const { currentReport, fetchReport } = useResultStore();
  const loc = useLocation();

  useEffect(() => {
    if (loc.state?.report?.id) {
      fetchReport(loc.state.report.id);
    }
  }, []);

  if (!currentReport?.content_markdown) {
    return (
      <PageShell>
        <div className="flex items-center justify-center py-16">
          <div className="flex items-center gap-3 text-text-muted">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="font-heading">报告生成中或暂不可用...</span>
          </div>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <h2 className="text-2xl font-heading font-bold text-text-primary mb-4">{currentReport.title}</h2>
      <ReportViewer content={currentReport.content_markdown} />
    </PageShell>
  );
}
