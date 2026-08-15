import React, { useEffect, useState } from 'react'
import { getComplaints, analyzeComplaint, resolveComplaint } from '../services/api'
import { LoadingSpinner, SectionHeader, Badge } from '../components/ui'
import { AlertTriangle, CheckCircle } from 'lucide-react'

export default function DisputeManagement() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [resolveNotes, setResolveNotes] = useState('')
  const [filter, setFilter]   = useState('all')

  const load = () => {
    setLoading(true)
    getComplaints({ limit: 50 })
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleAnalyze = async (complaintId) => {
    setAnalyzing(true)
    try {
      const r = await analyzeComplaint(complaintId)
      setSelected(prev => prev ? { ...prev, ...r.data } : prev)
      load()
    } catch (e) { console.error(e) }
    finally { setAnalyzing(false) }
  }

  const handleResolve = async (complaintId) => {
    if (!resolveNotes.trim()) return
    try {
      await resolveComplaint(complaintId, { resolution_notes: resolveNotes, resolved_by: 'Canal Authority' })
      setSelected(null)
      setResolveNotes('')
      load()
    } catch (e) { console.error(e) }
  }

  if (loading) return <LoadingSpinner text="Loading complaints..." />

  const complaints  = data?.complaints || []
  const systemic    = data?.systemic_issues || []
  const filtered    = filter === 'all' ? complaints
    : complaints.filter(c => c.severity === filter || c.status === filter)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dispute Management</h1>
        <p className="text-gray-500 text-sm">AI-powered complaint analysis and mediation</p>
      </div>

      {/* Systemic issues */}
      {systemic.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold text-sm text-gray-700">🔍 Systemic Issues Detected</h3>
          {systemic.map((issue, i) => (
            <div key={i} className="card bg-orange-50 border-orange-200 p-4 flex gap-3">
              <AlertTriangle className="text-orange-500 shrink-0 mt-0.5" size={18} />
              <div>
                <p className="text-sm font-semibold text-orange-900">{issue.description}</p>
                <p className="text-xs text-orange-700 mt-1">💡 {issue.recommendation}</p>
              </div>
              <Badge type={issue.severity} className="shrink-0">{issue.severity.toUpperCase()}</Badge>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Complaints list */}
        <div className="lg:col-span-2 card">
          <SectionHeader title={`Complaints (${filtered.length})`}>
            <select
              value={filter}
              onChange={e => setFilter(e.target.value)}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1 outline-none"
            >
              <option value="all">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="open">Open</option>
              <option value="resolved">Resolved</option>
            </select>
          </SectionHeader>

          <div className="space-y-2 max-h-[60vh] overflow-y-auto">
            {filtered.map((c, i) => (
              <button
                key={i}
                onClick={() => setSelected(c)}
                className={`w-full text-left p-3 rounded-lg border transition-all ${
                  selected?.complaint_id === c.complaint_id
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono text-gray-500">{c.complaint_id}</span>
                  <div className="flex gap-1">
                    <Badge type={c.severity}>{c.severity.toUpperCase()}</Badge>
                    <Badge type={c.status}>{c.status}</Badge>
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-900">{c.farmer_name}</p>
                <p className="text-xs text-gray-500">{c.village} · <Badge type={c.reach_type}>{c.reach_type}</Badge></p>
                <p className="text-xs text-gray-600 mt-1 line-clamp-2">{c.complaint_text}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Complaint detail */}
        <div className="lg:col-span-3 space-y-4">
          {!selected ? (
            <div className="card flex items-center justify-center h-48 text-gray-400">
              ← Select a complaint to view details and run AI analysis
            </div>
          ) : (
            <>
              <div className="card">
                <div className="flex items-start justify-between flex-wrap gap-2 mb-3">
                  <div>
                    <p className="font-mono text-xs text-gray-500">{selected.complaint_id}</p>
                    <h3 className="text-lg font-bold">{selected.farmer_name}</h3>
                    <p className="text-sm text-gray-500">{selected.village} · {new Date(selected.timestamp).toLocaleString()}</p>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <Badge type={selected.severity}>{selected.severity?.toUpperCase()}</Badge>
                    <Badge type={selected.status}>{selected.status}</Badge>
                    <Badge type={selected.reach_type}>{selected.reach_type?.toUpperCase()}</Badge>
                  </div>
                </div>

                <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 mb-3">
                  {selected.complaint_text}
                </div>

                {selected.ai_summary ? (
                  <div className="space-y-2">
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-xs font-semibold text-blue-800 mb-1">🤖 Granite AI Analysis</p>
                      <p className="text-sm text-blue-900"><strong>Summary:</strong> {selected.ai_summary}</p>
                      {selected.root_cause && <p className="text-sm text-blue-900 mt-1"><strong>Root Cause:</strong> {selected.root_cause}</p>}
                    </div>
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-xs font-semibold text-yellow-800 mb-1">💡 AI Recommendation (Requires Human Approval)</p>
                      <p className="text-sm text-yellow-900">{selected.ai_recommendation}</p>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => handleAnalyze(selected.complaint_id)}
                    disabled={analyzing}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {analyzing ? <><div className="spinner" /> Running Granite AI Analysis...</> : '🤖 Run AI Analysis with IBM Granite'}
                  </button>
                )}
              </div>

              {/* Resolution */}
              {selected.status !== 'resolved' && selected.ai_summary && (
                <div className="card">
                  <SectionHeader title="Resolve Complaint" sub="Human canal authority action required" />
                  <textarea
                    value={resolveNotes}
                    onChange={e => setResolveNotes(e.target.value)}
                    rows={2}
                    placeholder="Enter resolution notes / action taken..."
                    className="w-full border border-gray-200 rounded-lg p-3 text-sm outline-none focus:border-blue-400 resize-none mb-3"
                  />
                  <button
                    onClick={() => handleResolve(selected.complaint_id)}
                    disabled={!resolveNotes.trim()}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    <CheckCircle size={16} />
                    Mark as Resolved
                  </button>
                </div>
              )}

              {selected.status === 'resolved' && (
                <div className="card bg-green-50 border-green-200 p-4">
                  <p className="font-semibold text-green-800 flex items-center gap-2">
                    <CheckCircle size={16} /> Complaint Resolved
                  </p>
                  <p className="text-sm text-green-700 mt-1">Resolved by: {selected.resolved_by || 'Canal Authority'}</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
