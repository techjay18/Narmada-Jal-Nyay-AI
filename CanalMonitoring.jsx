import React, { useEffect, useState } from 'react'
import { getSensors, getFlowData, simulateSensors } from '../services/api'
import { LoadingSpinner, SectionHeader, StatCard, Badge } from '../components/ui'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { RefreshCw } from 'lucide-react'

const SENSOR_COLORS = {
  'SNS-H1': '#3b82f6', 'SNS-H2': '#60a5fa',
  'SNS-M1': '#8b5cf6', 'SNS-M2': '#a78bfa',
  'SNS-T1': '#f97316', 'SNS-T2': '#fb923c',
}

export default function CanalMonitoring({ scenario }) {
  const [sensors, setSensors]   = useState([])
  const [flowData, setFlowData] = useState([])
  const [live, setLive]         = useState([])
  const [loading, setLoading]   = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async () => {
    try {
      const [s, f] = await Promise.all([getSensors(), getFlowData(48)])
      setSensors(s.data.sensors || [])
      // Format flow series for chart
      const seriesMap = {}
      ;(f.data.raw || []).forEach(row => {
        const key = row.timestamp.slice(0, 16).replace('T', ' ')
        if (!seriesMap[key]) seriesMap[key] = { time: key }
        seriesMap[key][row.sensor_id] = row.flow_rate
      })
      setFlowData(Object.values(seriesMap).slice(-72))
    } catch (e) { console.error(e) }
  }

  const refreshLive = async () => {
    setRefreshing(true)
    try {
      const r = await simulateSensors(scenario)
      setLive(r.data.readings || [])
    } catch (e) { console.error(e) }
    finally { setRefreshing(false) }
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([loadData(), refreshLive()]).finally(() => setLoading(false))
  }, [scenario])

  if (loading) return <LoadingSpinner text="Loading sensor data..." />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Canal Monitoring</h1>
          <p className="text-gray-500 text-sm">Live sensor readings & flow analysis</p>
        </div>
        <button onClick={refreshLive} disabled={refreshing} className="btn-primary flex items-center gap-2">
          <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
          Refresh Live
        </button>
      </div>

      {/* Live sensor cards */}
      <div>
        <SectionHeader title="Live Sensor Readings" sub="Simulated real-time data" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {(live.length ? live : sensors.map(s => ({
            sensor_id: s.sensor_id,
            flow_rate: s.latest?.flow_rate,
            water_level: s.latest?.water_level,
            gate_open_percentage: s.latest?.gate_open_pct,
            reach: s.reach,
            is_anomaly: s.latest?.is_anomaly,
          }))).map((s, i) => (
            <div key={i} className={`card ${s.is_anomaly ? 'border-red-300 bg-red-50' : ''}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-bold text-gray-900">{s.sensor_id}</p>
                  <p className="text-xs text-gray-500">
                    {sensors.find(x => x.sensor_id === s.sensor_id)?.location || ''}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge type={s.reach || 'unknown'}>{(s.reach || '?').toUpperCase()}</Badge>
                  {s.is_anomaly && <span className="badge-critical">ANOMALY</span>}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                {[
                  { label: 'Flow', value: s.flow_rate != null ? `${s.flow_rate.toFixed(1)}` : '–', unit: 'cumecs' },
                  { label: 'Level', value: s.water_level != null ? `${s.water_level.toFixed(2)}` : '–', unit: 'm' },
                  { label: 'Gate', value: s.gate_open_percentage != null ? `${s.gate_open_percentage.toFixed(1)}` : '–', unit: '%' },
                ].map(({ label, value, unit }) => (
                  <div key={label} className="bg-gray-50 rounded-lg p-2">
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="text-sm font-bold">{value}<span className="text-xs font-normal text-gray-500"> {unit}</span></p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Flow chart */}
      <div className="card">
        <SectionHeader title="Canal Flow Rate – 48h History" sub="Head / Middle / Tail reach comparison" />
        {flowData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={flowData} margin={{ right: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={12} />
              <YAxis tick={{ fontSize: 11 }} label={{ value: 'cumecs', angle: -90, position: 'insideLeft', fontSize: 11 }} />
              <Tooltip formatter={(v) => [`${v?.toFixed(2)} cumecs`]} />
              <Legend />
              {Object.entries(SENSOR_COLORS).map(([sid, color]) => (
                <Line
                  key={sid}
                  type="monotone"
                  dataKey={sid}
                  stroke={color}
                  strokeWidth={2}
                  dot={false}
                  name={sid}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 text-sm text-center py-8">No historical data yet. Run simulation to generate readings.</p>
        )}
      </div>

      {/* Sensor table */}
      <div className="card">
        <SectionHeader title="Sensor Status Table" />
        <div className="table-container">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                {['Sensor ID', 'Location', 'Reach', 'Flow Rate', 'Water Level', 'Gate %', 'Status'].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sensors.map((s, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs font-medium">{s.sensor_id}</td>
                  <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{s.location}</td>
                  <td className="px-4 py-3"><Badge type={s.reach}>{s.reach?.toUpperCase()}</Badge></td>
                  <td className="px-4 py-3 font-medium">{s.latest?.flow_rate?.toFixed(2) || '–'}</td>
                  <td className="px-4 py-3">{s.latest?.water_level?.toFixed(3) || '–'} m</td>
                  <td className="px-4 py-3">{s.latest?.gate_open_pct?.toFixed(1) || '–'}%</td>
                  <td className="px-4 py-3">
                    {s.latest?.is_anomaly
                      ? <span className="badge-critical">⚠ Anomaly</span>
                      : <span className="badge-low">✓ Normal</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
