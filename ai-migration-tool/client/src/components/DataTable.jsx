export default function DataTable({ rows }) {
  /**
   * Lightweight table preview of data (stub).
   *
   * Intended behavior:
   * - Accept an array of objects (rows)
   * - Render column headers dynamically from keys
   * - Render a small preview (e.g., first 25 rows)
   * - Support basic empty/error states
   */

  if (!rows || rows.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-600">
        No preview available yet.
      </div>
    );
  }

  const columns = Object.keys(rows[0] ?? {});

  return (
    <div className="overflow-auto rounded-md border border-slate-200">
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((col) => (
              <th key={col} className="whitespace-nowrap border-b border-slate-200 px-3 py-2 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx} className="odd:bg-white even:bg-slate-50">
              {columns.map((col) => (
                <td key={col} className="whitespace-nowrap border-b border-slate-100 px-3 py-2 text-slate-700">
                  {String(row?.[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

