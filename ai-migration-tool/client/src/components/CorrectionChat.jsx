import { useState, useRef, useEffect } from 'react'

export default function CorrectionChat({ uploadedPath, onCorrectionApplied }) {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const bottomRef = useRef(null)

  // scroll to latest message whenever history updates
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  async function handleSend() {
    if (!message.trim() || loading) return

    const userMessage = message.trim()
    setMessage('')
    setHistory(prev => [...prev, { role: 'user', text: userMessage }])
    setLoading(true)

    try {
      const response = await fetch('http://localhost:5001/api/correct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uploaded_path: uploadedPath, message: userMessage })
      })

      const data = await response.json()

      if (!response.ok) {
        setHistory(prev => [...prev, { role: 'claude', text: data.error, isError: true }])
        return
      }

      // echo Claude's confirmation back in the chat
      setHistory(prev => [...prev, { role: 'claude', text: data.confirmation }])

      // notify parent to update table and mappings
      onCorrectionApplied(data)

    } catch (err) {
      setHistory(prev => [...prev, { role: 'claude', text: 'Something went wrong. Please try again.', isError: true }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-3">

      {/* message history */}
      <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
        {history.length === 0 && (
          <p className="text-sm text-slate-400 italic">
            Ask Claude to remap a column, update a cleaning rule, or provide context about your data.
          </p>
        )}
        {history.map((msg, i) => (
          <div
            key={i}
            className={`text-sm px-3 py-2 rounded-md max-w-prose ${
              msg.role === 'user'
                ? 'bg-slate-100 text-slate-700 ml-auto text-right'
                : msg.isError
                  ? 'bg-red-50 text-red-700'
                  : 'bg-blue-50 text-blue-800'
            }`}
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="text-sm px-3 py-2 rounded-md bg-blue-50 text-blue-400 italic">
            Applying correction...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* input row */}
      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder='e.g. "Map telefono to TELF1" or "Revenue is in thousands"'
          value={message}
          onChange={e => setMessage(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !message.trim()}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>

    </div>
  )
}
