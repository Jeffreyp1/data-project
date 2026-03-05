export default function AuditReport({ report }) {
  /**
   * Render the AI-generated audit report (stub).
   *
   * Intended behavior:
   * - Display markdown (or structured sections) returned by backend
   * - Provide a "copy" button
   * - Show warnings/blockers prominently
   */

  if (!report) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-600">
        No audit report yet.
      </div>
    );
  }

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <pre className="whitespace-pre-wrap text-sm text-slate-800">{report}</pre>
    </div>
  );
}

