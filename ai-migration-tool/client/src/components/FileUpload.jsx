import { useRef, useState } from "react";

export default function FileUpload({ onUpload, onAnalyze }) {
  /**
   * Upload control + analyze trigger.
   *
   * Intended behavior:
   * - Let user pick a CSV file
   * - Call `onUpload(file)` to send to backend
   * - Enable an "Analyze" button after upload finishes
   */
  const inputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);

  function handlePickClick() {
    // TODO: open the file picker
    inputRef.current?.click();
  }

  function handleFileChange(e) {
    // TODO: store selected file + validate CSV extension/type
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
  }

  async function handleUploadClick() {
    // TODO: call props.onUpload(file) and handle UI states (loading, error)
    if (!selectedFile) return;
    await onUpload?.(selectedFile);
  }

  async function handleAnalyzeClick() {
    // TODO: call props.onAnalyze() and handle UI states (loading, error)
    await onAnalyze?.();
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div className="text-sm font-medium">Upload legacy CSV</div>
        <div className="mt-1 text-xs text-slate-600">
          Select a file to upload, then run analysis.
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={handleFileChange}
        />
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handlePickClick}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-50"
          >
            Choose file
          </button>
          <div className="text-xs text-slate-600">
            {selectedFile ? (
              <span className="font-mono">{selectedFile.name}</span>
            ) : (
              <span>No file selected</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleUploadClick}
          className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-50"
          disabled={!selectedFile}
        >
          Upload
        </button>
        <button
          type="button"
          onClick={handleAnalyzeClick}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-50"
        >
          Analyze
        </button>
      </div>
    </div>
  );
}

