import ReactMarkdown from 'react-markdown';

export default function ReportViewer({ content }: { content: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 prose prose-sm max-w-none">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
