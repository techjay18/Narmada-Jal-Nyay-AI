import React, { useEffect, useState } from 'react'
import { getFarmers, getFarmerStatus, submitComplaint } from '../services/api'
import { LoadingSpinner, SectionHeader, Badge } from '../components/ui'
import { Search } from 'lucide-react'

export default function FarmerPortal({ scenario }) {
  const [farmers, setFarmers]     = useState([])
  const [selected, setSelected]   = useState(null)
  const [status, setStatus]       = useState(null)
  const [loading, setLoading]     = useState(true)
  const [statusLoading, setStatusLoading] = useState(false)
  const [search, setSearch]       = useState('')
  const [complaint, setComplaint] = useState('')
  const [submitting, setSubmitting]   = useState(false)
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    getFarmers({ limit: 90 })
      .then(r => setFarmers(r.data.farmers || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = async (farmer) => {
    setSelected(farmer)
    setStatus(null)
    setSubmitted(false)
    setStatusLoading(true)
    try {
      const r = await getFarmerStatus(farmer.farmer_id, scenario)
      setStatus(r.data)
    } catch (e) { console.error(e) }
    finally { setStatusLoading(false) }
  }

  const handleSubmitComplaint = async () => {
    if (!complaint.trim() || !selected) return
    setSubmitting(true)
    try {
      await submitComplaint({ farmer_id: selected.farmer_id, complaint_text: complaint })
      setSubmitted(true)
      setComplaint('')
    } catch (e) { console.error(e) }
    finally { setSubmitting(false) }
  }

  const filtered = farmers.filter(f =>
    f.farmer_name.toLowerCase().includes(search.toLowerCase()) ||
    f.village.toLowerCase().includes(search.toLowerCase()) ||
    f.farmer_id.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) return <LoadingSpinner text="Loading farmers..." />

  const fairness = status?.fairness_score || 0
  const fairColor = fairness >= 0.90 ? 'green' : fairness >= 0.75 ? 'yellow' : 'red'
  const fairBg    = { green: 'bg-green-50 border-green-200', yellow: 'bg-yellow-50 border-yellow-200', red: 'bg-red-50 border-red-200' }[fairColor]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Farmer Portal</h1>
        <p className="text-gray-500 text-sm">Check your water allocation and irrigation schedule</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Farmer list */}
        <div className="card lg:col-span-1">
          <SectionHeader title="Select Farmer" sub={`${filtered.length} farmers`} />
          <div className="relative mb-3">
            <Search size={14} className="absolute left-3 top-2.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, village, or ID..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-blue-400"
            />
          </div>
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {filtered.slice(0, 50).map((f, i) => (
              <button
                key={i}
                onClick={() => handleSelect(f)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selected?.farmer_id === f.farmer_id ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{f.farmer_name}</span>
                  <Badge type={f.reach_type}>{f.reach_type.toUpperCase()}</Badge>
                </div>
                <div className="text-xs text-gray-500">{f.village} · {f.crop} · {f.land_area} ha</div>
              </button>
            ))}
          </div>
        </div>

        {/* Farmer status */}
        <div className="lg:col-span-2 space-y-4">
          {!selected ? (
            <div className="card flex items-center justify-center h-48 text-gray-400">
              ← Select a farmer to view their water status
            </div>
          ) : statusLoading ? (
            <LoadingSpinner text="Loading water status..." />
          ) : (
            <>
              {/* Profile */}
              <div className="card">
                <div className="flex items-start justify-between flex-wrap gap-2">
                  <div>
                    <h2 className="text-xl font-bold">{selected.farmer_name}</h2>
                    <p className="text-gray-500 text-sm">{selected.village} · {selected.canal_section}</p>
                  </div>
                  <Badge type={selected.reach_type}>{selected.reach_type.toUpperCase()} REACH</Badge>
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 mt-4 text-center">
                  {[
                    { label: 'ID',       val: selected.farmer_id },
                    { label: 'Crop',     val: selected.crop },
                    { label: 'Land',     val: `${selected.land_area} ha` },
                    { label: 'CWR',      val: `${selected.crop_water_requirement} mm/day` },
                    { label: 'Language', val: selected.language_preference === 'gu' ? 'ગુજરાતી' : 'English' },
                  ].map(({ label, val }) => (
                    <div key={label} className="bg-gray-50 rounded-lg p-2">
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className="text-sm font-medium">{val}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Water status */}
              {status && (
                <div className={`card border ${fairBg}`}>
                  <p className="font-semibold text-gray-900 mb-3">{status.status_message}</p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                      { label: 'Expected Water',  val: `${status.expected_water_m3?.toFixed(1)} m³` },
                      { label: 'Allocated Water', val: `${status.allocated_water_m3?.toFixed(1)} m³`, highlight: true },
                      { label: 'Fairness Score',  val: `${((status.fairness_score||0)*100).toFixed(1)}%` },
                      { label: 'Canal Status',    val: status.canal_status?.toUpperCase() },
                    ].map(({ label, val, highlight }) => (
                      <div key={label} className="bg-white rounded-lg p-3 shadow-sm">
                        <p className="text-xs text-gray-500">{label}</p>
                        <p className={`text-sm font-bold ${highlight ? 'text-blue-700' : ''}`}>{val}</p>
                      </div>
                    ))}
                  </div>

                  {status.irrigation_slot_start && (
                    <div className="mt-3 p-3 bg-white rounded-lg border border-gray-200">
                      <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">Irrigation Slot</p>
                      <p className="text-sm font-bold text-blue-800">
                        {new Date(status.irrigation_slot_start).toLocaleString()} –{' '}
                        {new Date(status.irrigation_slot_end).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' })}
                      </p>
                      {status.irrigation_duration_min > 0 && (
                        <p className="text-xs text-gray-500">Duration: {status.irrigation_duration_min} minutes</p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Complaint form */}
              <div className="card">
                <SectionHeader title="Submit Complaint / Feedback" sub="Your complaint will be analyzed by AI and reviewed by canal authority" />
                {submitted ? (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800 font-medium">
                    ✓ Complaint submitted successfully. AI analysis is in progress.
                  </div>
                ) : (
                  <div className="space-y-3">
                    <textarea
                      value={complaint}
                      onChange={e => setComplaint(e.target.value)}
                      rows={3}
                      placeholder="Describe your water distribution issue... (English or Gujarati)"
                      className="w-full border border-gray-200 rounded-lg p-3 text-sm outline-none focus:border-blue-400 resize-none"
                    />
                    <div className="flex gap-3">
                      <button
                        onClick={handleSubmitComplaint}
                        disabled={submitting || !complaint.trim()}
                        className="btn-primary"
                      >
                        {submitting ? 'Submitting...' : 'Submit Complaint'}
                      </button>
                      <p className="text-xs text-gray-500 self-center">
                        AI will classify severity and recommend resolution
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
