import React, { useEffect, useState } from 'react'
import { getSchedule, generateSchedule } from '../services/api'
import { LoadingSpinner, SectionHeader, Badge, StatCard, EquityBar } from '../components/ui'
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer, Cell } from 'recharts'
import { RefreshCw } from 'lucide-react'

const REACH_COLORS = { head: '#3b82f6', middle: '#8b5cf6', tail: '#f97316' }

export default function WaterDistribution({ scenario }) {
  const [schedule, setSchedule] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [generating, setGenerating] = useState(false)
  const [filter, setFilter]     = useState('all')

  const load = () => {
    setLoading(true)
    getSchedule()
      .then(r => setSchedule(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const r = await generateSchedule({ scenario })
      setSchedule(r.data)
    } catch (e) { console.error(e) }
    finally { setGenerating(false) }
  }

  if (loading) return <LoadingSpinner text="Loading schedule..." />

  const allocations = schedule?.allocations || []
  const report      = schedule?.fairness_report || {}

  const filtered = filter === 'all' ? allocations
    : allocations.filter(a => a.reach_type === filter)

  // Chart data – fairness by farmer
  const chartData = allocations.slice(0, 30).map(a => ({
    farmer: a.farmer_id,
    reach:  a.reach_type,
    expected:  parseFloat(a.expected_water?.toFixed(1) || 0),
    allocated: parseFloat(a.allocated_water?.toFixed(1) || a.allocated?.toFixed(1) || 0),
    fairness:  parseFloat(((a.fairness_score || 0) * 100).toFixed(1)),
  }))

  // Equity bar chart data
  const equityBarData = [
    { name: 'Head',   fairness: ((report.head_avg_fairness || 0) * 100).toFixed(1) },
    { name: 'Middle', fairness: ((report.middle_avg_fairness || 0) * 100).toFixed(1) },
    { name: 'Tail',   fairness: ((report.tail_avg_fairness || 0) * 100).toFixed(1) },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Water Distribution</h1>
          <p className="text-gray-500 text-sm">Fairness-aware irrigation schedule</p>
        </div>
        <button onClick={handleGenerate} disabled={generating} className="btn-primary flex items-center gap-2">
          <RefreshCw size={15} className={generating ? 'animate-spin' : ''} />
          {generating ? 'Generating...' : 'Generate New Schedule'}
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Shortage Level"  value={`${((schedule?.shortage_level||0)*100).toFixed(1)}%`} color={schedule?.shortage_level > 0.15 ? 'red' : 'green'} />
        <StatCard label="Overall Fairness" value={`${((schedule?.overall_fairness||0)*100).toFixed(1)}%`} color="blue" />
        <StatCard label="Head-Tail Gap"   value={`${((schedule?.head_tail_gap||0)*100).toFixed(1)}%`} color={schedule?.head_tail_gap > 0.15 ? 'orange' : 'green'} />
        <StatCard label="Below Threshold" value={report.below_threshold || 0} sub="farmers < 75%" color={report.below_threshold > 5 ? 'red' : 'green'} />
      </div>

      {/* Equity bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <SectionHeader title="Equity Breakdown" sub="Average fairness score by reach type" />
          <EquityBar
            head={schedule?.head_equity_score}
            middle={schedule?.middle_equity_score}
            tail={schedule?.tail_equity_score}
          />
          <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm">
            <p className="text-gray-600">{schedule?.summary}</p>
          </div>
          {schedule?.requires_human_approval && (
            <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm">
              <span className="badge-high mr-2">⚠ Human Approval Required</span>
              Schedule deviation exceeds threshold – canal authority must approve.
            </div>
          )}
        </div>

        <div className="card">
          <SectionHeader title="Avg Fairness by Reach" />
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={equityBarData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} unit="%" />
              <Tooltip formatter={v => [`${v}%`]} />
              <Bar dataKey="fairness" radius={[4,4,0,0]}>
                {equityBarData.map((_, i) => (
                  <Cell key={i} fill={['#3b82f6','#8b5cf6','#f97316'][i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI schedule summary */}
      {schedule?.ai_summary && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex gap-3">
            <span className="text-2xl">🤖</span>
            <div>
              <p className="font-semibold text-blue-900 text-sm">Granite AI – Schedule Analysis</p>
              <p className="text-sm text-blue-800 mt-1">{schedule.ai_summary}</p>
            </div>
          </div>
        </div>
      )}

      {/* Allocation table */}
      <div className="card">
        <SectionHeader title={`Farmer Allocations (${filtered.length})`}>
          <div className="flex gap-2">
            {['all','head','middle','tail'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                  filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </SectionHeader>

        <div className="table-container">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                {['Farmer', 'Village', 'Reach', 'Crop', 'Expected (m³)', 'Allocated (m³)', 'Fairness', 'Slot Start', 'Notes'].map(h => (
                  <th key={h} className="px-3 py-3 text-left font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((a, i) => {
                const fairness = a.fairness_score || 0
                const fairColor = fairness >= 0.90 ? 'text-green-700' : fairness >= 0.75 ? 'text-yellow-600' : 'text-red-600'
                return (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{a.farmer_id || a.farmer_name}</td>
                    <td className="px-3 py-2 text-gray-600">{a.village || '–'}</td>
                    <td className="px-3 py-2"><Badge type={a.reach_type}>{a.reach_type?.toUpperCase()}</Badge></td>
                    <td className="px-3 py-2 text-gray-600">{a.crop}</td>
                    <td className="px-3 py-2">{(a.expected_water || a.expected || 0).toFixed(1)}</td>
                    <td className="px-3 py-2 font-medium">{(a.allocated_water || a.allocated || 0).toFixed(1)}</td>
                    <td className={`px-3 py-2 font-bold ${fairColor}`}>{(fairness * 100).toFixed(1)}%</td>
                    <td className="px-3 py-2 text-xs text-gray-500">
                      {a.slot_start ? new Date(a.slot_start).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }) : a.slot?.start ? new Date(a.slot.start).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }) : '–'}
                    </td>
                    <td className="px-3 py-2 text-xs text-orange-700">{a.notes}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
