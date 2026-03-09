// export default function AuditReport({ report }) {
//   /**
//    * Render the AI-generated audit report (stub).
//    *
//    * Intended behavior:
//    * - Display markdown (or structured sections) returned by backend
//    * - Provide a "copy" button
//    * - Show warnings/blockers prominently
//    */

//   if (!report) {
//     return (
//       <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-600">
//         No audit report yet.
//       </div>
//     );
//   }

//   return (
//     <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
//       <pre className="whitespace-pre-wrap text-sm text-slate-800">{report}</pre>
//     </div>
//   );
// }

export default function AuditReport({ report }) {
  if (!report) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-600">
        No audit report yet.
      </div>
    );
  }

  // Pick status color
  let statusColor = "bg-gray-100 text-gray-800"
  if (report.readiness.status === "READY")        statusColor = "bg-green-100 text-green-800"
  if (report.readiness.status === "NEEDS_REVIEW") statusColor = "bg-yellow-100 text-yellow-800"
  if (report.readiness.status === "BLOCKED")      statusColor = "bg-red-100 text-red-800"

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4 space-y-4">

      {/* Readiness status badge */}
      <div>
        <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${statusColor}`}>
          {report.readiness.status}
        </span>
        {report.readiness.reasons.map((reason, index) => (
          <p key={index} className="text-sm text-slate-600 mt-1">{reason}</p>
        ))}
      </div>

      {/* Plain English summary */}
      <p className="text-sm text-slate-800">{report.audit_report_text}</p>

      {/* Field mappings table */}
      <table className="w-full text-sm border border-slate-200">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2 border border-slate-200">Source Column</th>
            <th className="text-left p-2 border border-slate-200">SAP Field</th>
            <th className="text-left p-2 border border-slate-200">Cleaning Function</th>
            <th className="text-left p-2 border border-slate-200">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {report.field_mappings.map((mapping, index) => (
            <tr key={index} className={mapping.confidence < 0.80 ? "bg-yellow-50" : "bg-white"}>
              <td className="p-2 border border-slate-200">{mapping.source}</td>
              <td className="p-2 border border-slate-200">{mapping.target}</td>
              <td className="p-2 border border-slate-200">{mapping.cleaning_fn}</td>
              <td className="p-2 border border-slate-200">{mapping.confidence}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Unmapped columns warning */}
      {report.unmapped_columns.length > 0 && (
        <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3">
          <p className="text-sm font-semibold text-yellow-800">Unmapped Columns</p>
          <p className="text-sm text-yellow-700">{report.unmapped_columns.join(", ")}</p>
        </div>
      )}

    </div>
  );
}