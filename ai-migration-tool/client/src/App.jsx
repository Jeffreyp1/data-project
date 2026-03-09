import { useMemo, useState } from "react";

import FileUpload from "./components/FileUpload.jsx";
import DataTable from "./components/DataTable.jsx";
import AuditReport from "./components/AuditReport.jsx";

export default function App() {
  /**
   * Top-level UI orchestration.
   *
   * Intended behavior:
   * - Let user upload CSV
   * - Show parsed/previewed data in a table
   * - Trigger backend analysis pipeline
   * - Display Claude-generated audit report + provide Excel download link
   */
  const [uploadedPath, setUploadedPath] = useState(null);
  const [previewRows, setPreviewRows] = useState([]);
  const [auditReport, setAuditReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [excelPath, setExcelPath] = useState(null)
  const [error, setError] = useState(null);

  const hasPreview = useMemo(() => previewRows.length > 0, [previewRows]);

  async function handleUpload(file) {
    setIsLoading(true);
    setError(null);
    try{
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("http://localhost:5001/api/upload",{
        method: "POST",
        body: formData,
      })
      const data = await response.json();
      setUploadedPath(data.uploaded_path);
      await handleAnalyze(data.uploaded_path)
    }catch(err){
      setError(err.message);
    }finally{
      setIsLoading(false);
    }
  }

  async function handleAnalyze(path) {
    // TODO:
    // - POST JSON to Flask `/api/analyze` with uploadedPath/file_id
    // - Receive excel_output_path + audit_report
    // - Update auditReport + store excel download token/link
    const activePath = path || uploadedPath;
    if (!activePath) return;
    console.log("UploadedPath:", uploadedPath)
    const response = await fetch("http://localhost:5001/api/analyze",{
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uploaded_path: activePath }),
    })
    const data = await response.json()
    setAuditReport(data.audit_report);
    setPreviewRows(data.cleaned_rows || [])
    setExcelPath(data.excel_output_path)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <header className="mb-8">
          <h1 className="text-2xl font-semibold">AI Data Migration Tool</h1>
          <p className="mt-2 text-sm text-slate-600">
            Upload legacy CSV → clean/transform → AI mapping + readiness → export Excel + audit report.
          </p>
        </header>
        {isLoading && <p className="text-sm text-slate-500">Uploading...</p>}
        {error && <p className="text-sm text-red-500">{error}</p>}
        <div className="grid gap-6">
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <FileUpload onUpload={handleUpload} onAnalyze={handleAnalyze} />
            <div className="mt-3 text-xs text-slate-500">
              Uploaded reference: <span className="font-mono">{uploadedPath ?? "—"}</span>
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-medium">Data Preview</h2>
            <p className="mt-1 text-sm text-slate-600">
              Preview of cleaned data will appear here (stub).
            </p>
            <div className="mt-4">
              <DataTable rows={hasPreview ? previewRows : []} />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-medium">AI Audit Report</h2>
            <p className="mt-1 text-sm text-slate-600">
              Claude-generated mapping and readiness analysis will appear here (stub).
            </p>
            <div className="mt-4">
              <AuditReport report={auditReport} />
            </div>
              {/* Download button — only shows after analysis completes */}
            {excelPath && (
              <a
                href={`http://localhost:5001/api/download?filename=${excelPath}`}
                target="_blank"
                rel="noreferrer"
                className="inline-block mt-3 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Download Clean Excel
              </a>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

