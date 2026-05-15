import { useState, type DragEvent, type ChangeEvent, type ReactNode } from 'react';
import ProgressBar from './ProgressBar';

interface Props {
  onFileSelect?: (file: File) => void;
  progress?: number;
  uploading?: boolean;
  acceptedFormats?: string[];
  children?: ReactNode;
  className?: string;
}

export default function UploadDropzone({
  onFileSelect,
  progress,
  uploading,
  acceptedFormats = ['DICOM', 'NIfTI', 'JPG/PNG'],
  children,
  className = '',
}: Props) {
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = (e: DragEvent) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);
  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && onFileSelect) onFileSelect(file);
  };
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onFileSelect) onFileSelect(file);
  };

  return (
    <div className={`${className}`}>
      <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          upload-dropzone flex flex-col items-center justify-center gap-2 p-6 text-center
          ${dragOver ? 'border-blue-400 bg-blue-50' : ''}
        `}
      >
        {children || (
          <>
            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
              <svg className="w-5 h-5 text-navy-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m0 0l6.75-6.75M12 19.5l-6.75-6.75" />
              </svg>
            </div>
            <div>
              <span className="text-sm font-medium text-navy-700">Upload File</span>
              <span className="text-sm text-text-muted"> or drag and drop</span>
            </div>
            <p className="text-xs text-text-muted">
              {acceptedFormats.join(' / ')}
            </p>
          </>
        )}
        <input type="file" className="hidden" onChange={handleChange} />
      </label>
      {uploading && typeof progress === 'number' && (
        <div className="mt-3">
          <ProgressBar value={progress} />
          <p className="text-xs text-text-muted mt-1">Uploading... {progress}%</p>
        </div>
      )}
    </div>
  );
}
