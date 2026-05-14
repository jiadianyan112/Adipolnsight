import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useResultStore } from '../stores/resultStore';
import ReportViewer from '../components/report/ReportViewer';

export default function ReportPage() {
  const { currentReport, fetchReport } = useResultStore();
  const loc = useLocation();

  useEffect(() => {
    if (loc.state?.report?.id) {
      fetchReport(loc.state.report.id);
    }
  }, []);

  if (!currentReport?.content_markdown) {
    return <p className="text-gray-400">Report is being generated or not available...</p>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-4">{currentReport.title}</h2>
      <ReportViewer content={currentReport.content_markdown} />
    </div>
  );
}
