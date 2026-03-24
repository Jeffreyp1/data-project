export default function AuditReport({ report }) {
  if (!report) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-600">
        No audit report yet.
      </div>
    )
  }

  const statusColor =
    report.readiness.status === 'READY'        ? 'bg-green-100 text-green-800' :
    report.readiness.status === 'NEEDS_REVIEW' ? 'bg-yellow-100 text-yellow-800' :
    report.readiness.status === 'BLOCKED'      ? 'bg-red-100 text-red-800' :
                                                  'bg-gray-100 text-gray-800'

  const requiredFields = new Set(report.required_fields || [])
  const highConfidence  = report.field_mappings.filter(m => m.confidence >= 0.90)
  const medConfidence   = report.field_mappings.filter(m => m.confidence >= 0.80 && m.confidence < 0.90)
  const lowConfidence   = report.field_mappings.filter(m => m.confidence < 0.80)

  const confidenceBadge = (confidence) => {
    const pct = (confidence * 100).toFixed(0) + '%'
    if (confidence >= 0.90) return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800">{pct}</span>
    if (confidence >= 0.80) return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-yellow-100 text-yellow-800">{pct}</span>
    return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800">{pct}</span>
  }

  return (
    <div className="space-y-5">

      {/* ── Header: Schema + Readiness ── */}
      <div className="flex items-center gap-3 flex-wrap">
        {report.object_label && (
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
            {report.object_label}
          </span>
        )}
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColor}`}>
          {report.readiness.status}
        </span>
        {report.readiness.reasons?.map((r, i) => (
          <span key={i} className="text-xs text-slate-500">{r}</span>
        ))}
      </div>

      {/*summary*/}
      <div className="rounded-md bg-slate-50 border border-slate-200 p-4">
    <p className="text-sm font-medium text-slate-700 mb-2">Summary</p>
      <div className="text-sm text-slate-600 space-y-1">
          {report.audit_report_text.split('\n').map((line, i) => (
              line.trim() ? <p key={i}>{line.trim()}</p> : null
          ))}
      </div>
    </div>

      {/* Consultant action items */}
      {(lowConfidence.length > 0 || report.unmapped_columns?.length > 0) && (
        <div className="rounded-md bg-yellow-50 border border-yellow-200 p-4">
          <p className="text-sm font-semibold text-yellow-900 mb-2">
            Action Required
          </p>
          <ul className="space-y-1">
            {lowConfidence.map((m, i) => (
              <li key={i} className="text-sm text-yellow-800 flex items-start gap-2">
                <span className="mt-0.5">•</span>
                <span>
                  <span className="font-medium">{m.source} → {m.target}</span>
                  {' '}({(m.confidence * 100).toFixed(0)}% confidence) — review mapping before proceeding
                </span>
              </li>
            ))}
            {report.unmapped_columns?.map((col, i) => (
              <li key={i} className="text-sm text-yellow-800 flex items-start gap-2">
                <span className="mt-0.5">•</span>
                <span>
                  <span className="font-medium">{col}</span>
                  {' '}— no SAP field match found, manual mapping required
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/*field mappings table */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">
          Field Mappings
          <span className="ml-2 text-xs font-normal text-slate-400">
            {report.field_mappings.length} mapped
            {report.unmapped_columns?.length > 0 && ` · ${report.unmapped_columns.length} unmapped`}
          </span>
        </p>
        <div className="overflow-auto rounded-md border border-slate-200">
          <table className="min-w-full text-sm border-collapse">
            <thead className="bg-slate-100">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-slate-600 border border-slate-200">Source Column</th>
                <th className="px-3 py-2 text-left font-medium text-slate-600 border border-slate-200">SAP Field</th>
                <th className="px-3 py-2 text-left font-medium text-slate-600 border border-slate-200">Cleaning Function</th>
                <th className="px-3 py-2 text-left font-medium text-slate-600 border border-slate-200">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {report.field_mappings.map((m, i) => (
                <tr key={i} className={m.confidence < 0.80 ? 'bg-yellow-50' : 'bg-white'}>
                  <td className="px-3 py-2 border border-slate-200 font-mono text-xs">{m.source}</td>
                  <td className="px-3 py-2 border border-slate-200 font-mono text-xs font-semibold">
                    {m.target}
                    {requiredFields.has(m.target) && (
                      <span className="ml-2 px-1.5 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-700">
                        required
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 border border-slate-200 text-slate-500 text-xs">{m.cleaning_fn}</td>
                  <td className="px-3 py-2 border border-slate-200">{confidenceBadge(m.confidence)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}