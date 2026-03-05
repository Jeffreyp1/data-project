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
  const [auditReport, setAuditReport] = useState("");

  const hasPreview = useMemo(() => previewRows.length > 0, [previewRows]);

  async function handleUpload(file) {
    // TODO:
    // - POST multipart/form-data to Flask `/api/upload`
    // - setUploadedPath(response.uploaded_path or file_id)
    // - optionally parse a client-side preview (or ask backend for preview rows)
    void file;
    setUploadedPath("TODO: uploaded_path");
    setPreviewRows([]);
  }

  async function handleAnalyze() {
    // TODO:
    // - POST JSON to Flask `/api/analyze` with uploadedPath/file_id
    // - Receive excel_output_path + audit_report
    // - Update auditReport + store excel download token/link
    if (!uploadedPath) return;
    setAuditReport("TODO: audit report from backend");
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
          </section>
        </div>
      </div>
    </div>
  );
}

