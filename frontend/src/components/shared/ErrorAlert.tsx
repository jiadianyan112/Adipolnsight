export default function ErrorAlert({ code, message }: { code: string; message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
      <span className="font-mono font-bold mr-2">[{code}]</span>
      {message}
    </div>
  );
}
