import ReactMarkdown from 'react-markdown';
import type { ReportGenerationResult, ReportSection, ReportFigure, ReportReference, ExportFormat } from '../../types';
import DashboardCard from '../shared/DashboardCard';
import StatusBadge from '../shared/StatusBadge';

interface Props {
  report: ReportGenerationResult;
  onExport?: (format: string) => void;
}

function SectionCard({ section }: { section: ReportSection }) {
  return (
    <div id={`section-${section.number}`} className="card-dashboard p-5 space-y-3">
      <div className="flex items-center gap-2">
        <span className="shrink-0 w-6 h-6 rounded-lg bg-navy-700 text-white flex items-center justify-center text-[11px] font-heading font-bold">
          {section.number}
        </span>
        <h3 className="font-heading font-semibold text-base text-text-primary">{section.title}</h3>
        <StatusBadge status={section.status === 'complete' ? 'success' : section.status === 'pending' ? 'pending' : 'cancelled'} />
      </div>

      {section.summary && (
        <p className="text-xs text-text-secondary bg-surface rounded-lg px-3 py-2">{section.summary}</p>
      )}

      <div className="prose prose-sm max-w-none text-text-secondary">
        <ReactMarkdown>{section.content}</ReactMarkdown>
      </div>

      {/* Evidence jobs */}
      {section.evidence_job_ids && section.evidence_job_ids.length > 0 && (
        <div className="flex items-center gap-2 text-[10px] text-text-muted pt-2 border-t border-border-light">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          <span>证据来源：</span>
          {section.evidence_job_ids.map((jid) => (
            <span key={jid} className="px-1.5 py-0.5 rounded bg-surface font-mono text-navy-600">{jid}</span>
          ))}
        </div>
      )}

      {/* Related figures */}
      {section.related_figures && section.related_figures.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {section.related_figures.map((f, i) => (
            <div key={i} className="flex items-center gap-1.5 px-2 py-1 rounded bg-blue-50 border border-blue-100 text-[10px]">
              <svg className="w-3 h-3 text-navy-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909" />
              </svg>
              <span className="text-navy-700 font-medium">{f.caption}</span>
            </div>
          ))}
        </div>
      )}

      {/* Related tables */}
      {section.related_tables && section.related_tables.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {section.related_tables.map((t, i) => (
            <div key={i} className="flex items-center gap-1.5 px-2 py-1 rounded bg-surface border border-border text-[10px]">
              <svg className="w-3 h-3 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
              <span className="text-text-secondary font-medium">{t.caption}</span>
              <span className="text-text-muted">({t.columns?.join(', ')})</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FigureList({ figures }: { figures: ReportFigure[] }) {
  if (!figures.length) return null;
  return (
    <DashboardCard padding="md">
      <h4 className="section-title-sm mb-3">图表清单</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {figures.map((f) => (
          <div key={f.figure_id} className="flex items-center gap-2 p-2 bg-surface rounded-lg text-xs">
            <span className="shrink-0 w-8 h-8 rounded bg-white border border-border flex items-center justify-center text-[10px] font-heading font-bold text-text-muted">
              {f.number}
            </span>
            <div className="min-w-0">
              <p className="font-medium text-text-secondary truncate">{f.caption}</p>
              <p className="text-[10px] text-text-muted">{f.type} · §{f.section_number}</p>
            </div>
          </div>
        ))}
      </div>
    </DashboardCard>
  );
}

function ReferenceList({ references }: { references: ReportReference[] }) {
  if (!references.length) return null;
  return (
    <DashboardCard padding="md">
      <h4 className="section-title-sm mb-3">参考文献</h4>
      <ol className="space-y-1.5 text-xs text-text-secondary">
        {references.map((ref) => (
          <li key={ref.ref_id} value={ref.number} className="pl-1">
            {ref.text}
            {ref.doi && <span className="text-text-muted ml-1">DOI: {ref.doi}</span>}
          </li>
        ))}
      </ol>
    </DashboardCard>
  );
}

function ExportBar({ formats, onExport }: { formats: ExportFormat[]; onExport?: (f: string) => void }) {
  return (
    <DashboardCard padding="md">
      <h4 className="section-title-sm mb-3">导出</h4>
      <div className="flex flex-wrap gap-2">
        {formats.map((f) => (
          <button
            key={f.format}
            disabled={!f.available}
            onClick={() => onExport?.(f.format)}
            className={`px-3 py-1.5 rounded text-xs font-medium border transition-card ${
              f.available
                ? 'bg-white border-border text-text-secondary hover:border-navy-600 hover:text-text-primary cursor-pointer'
                : 'bg-surface text-text-muted border-border-light cursor-not-allowed'
            }`}
          >
            {f.label}
            {!f.available && <span className="ml-1 text-[9px]">(暂未开放)</span>}
          </button>
        ))}
      </div>
    </DashboardCard>
  );
}

export default function ReportViewer({ report, onExport }: Props) {
  const sections = report.sections || [];

  return (
    <div className="space-y-5">
      {/* Title */}
      <div className="card-dashboard p-6 bg-navy-700 text-white">
        <h1 className="text-xl font-heading font-bold">{report.title}</h1>
        {report.subtitle && <p className="text-navy-200 text-sm mt-1">{report.subtitle}</p>}
        <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-navy-300">
          <span>报告类型：{report.report_type}</span>
          <span className="text-navy-500">|</span>
          <span>语言：{report.language}</span>
          <span className="text-navy-500">|</span>
          <span>章节：{report.completed_sections}/{report.total_sections}</span>
          {report.metadata && (
            <>
              <span className="text-navy-500">|</span>
              <span>版本：{report.metadata.version}</span>
            </>
          )}
        </div>
      </div>

      {/* Table of Contents */}
      {sections.length > 0 && (
        <DashboardCard padding="md">
          <h4 className="section-title-sm mb-3">目录</h4>
          <nav className="space-y-1">
            {sections.map((sec) => (
              <a
                key={sec.number}
                href={`#section-${sec.number}`}
                className="flex items-center gap-2 px-2 py-1 rounded text-xs text-text-secondary hover:text-navy-600 hover:bg-surface transition-card"
              >
                <span className="w-5 text-right font-heading font-bold text-text-muted">{sec.number}.</span>
                <span className="flex-1">{sec.title}</span>
                <span className={`w-2 h-2 rounded-full ${sec.status === 'complete' ? 'bg-green-400' : sec.status === 'pending' ? 'bg-text-muted' : 'bg-border'}`} />
              </a>
            ))}
          </nav>
        </DashboardCard>
      )}

      {/* AI Interpretation */}
      {report.ai_interpretation && (
        <DashboardCard padding="md" className="bg-blue-50/30 border-blue-100">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-navy-600 shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{report.ai_interpretation}</ReactMarkdown>
            </div>
          </div>
        </DashboardCard>
      )}

      {/* Sections */}
      {sections.map((section) => (
        <SectionCard key={section.number} section={section} />
      ))}

      {/* Figures */}
      <FigureList figures={report.figures || []} />

      {/* References */}
      <ReferenceList references={report.references || []} />

      {/* Export */}
      <ExportBar formats={report.export_formats || []} onExport={onExport} />
    </div>
  );
}
