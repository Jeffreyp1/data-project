export default function DataTable({ rows, columns, showRaw }) {
  if (!rows || rows.length === 0) {
      return (
          <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-600">
              No data yet. Upload a CSV to see results.
          </div>
      )
  }

  const orderedColumns = columns && columns.length > 0
        ? columns
        : Object.keys(rows[0] ?? {})

  return (
      <div className="overflow-auto rounded-md border border-slate-200">
          <table className="min-w-full border-collapse text-left text-sm">
              <thead>
                  <tr>
                      {orderedColumns.map(col => {
                          const isReview = col.startsWith('REVIEW__')
                          const isUnmapped = col.startsWith('UNMAPPED__')
                          const displayName = isReview
                              ? `⚠ ${col.replace(/^REVIEW__+/, '')}`
                              : isUnmapped
                              ? `— ${col.replace('UNMAPPED__', '')}`
                              : col

                          const headerClass = isReview
                              ? 'bg-yellow-100 text-yellow-800'
                              : isUnmapped
                              ? 'bg-slate-100 text-slate-400 italic'
                              : 'bg-slate-100 text-slate-700'

                          return (
                              <th key={col} className={`px-3 py-2 font-medium border border-slate-200 whitespace-nowrap ${headerClass}`}>
                                  {displayName}
                              </th>
                          )
                      })}
                  </tr>
              </thead>
              <tbody>
                  {rows.map((row, idx) => {
                      let rowBg = ''
                      if (!showRaw) {
                          if (row.Migration_Status === 'READY')        rowBg = 'bg-green-50'
                          if (row.Migration_Status === 'NEEDS_REVIEW') rowBg = 'bg-yellow-50'
                          if (row.Migration_Status === 'FLAGGED')      rowBg = 'bg-orange-50'
                          if (row.Migration_Status === 'BLOCKED')      rowBg = 'bg-red-50'
                      }

                      return (
                          <tr key={idx} className={rowBg}>
                              {orderedColumns.map(col => {
                                  const isReview = col.startsWith('REVIEW__')
                                  const isUnmapped = col.startsWith('UNMAPPED__')
                                  const cellClass = isReview
                                      ? 'bg-yellow-50 text-yellow-800'
                                      : isUnmapped
                                      ? 'text-slate-400'
                                      : ''

                                  return (
                                      <td
                                          key={col}
                                          className={`px-3 py-2 border border-slate-200 whitespace-nowrap ${cellClass}`}
                                      >
                                          {String(row?.[col] ?? '')}
                                      </td>
                                  )
                              })}
                          </tr>
                      )
                  })}
              </tbody>
          </table>
      </div>
  )
}