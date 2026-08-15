import React, { useEffect, useState } from 'react'
import { getDashboard, runDemoScenario } from '../services/api'
import { StatCard, EquityBar, AlertBanner, LoadingSpinner, SectionHeader, Badge } from '../components/ui'
import { Droplets, AlertTriangle, Users, TrendingDown, CheckCircle, Zap } from 'lucide-react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import CanalMap from '../components/CanalMap.jsx'

export default function AuthorityDashboard({ scenario }) {
  const [data, setData]     = useState(null)
  const [loading, setLoading]   = useState(true)
  const [demo, setDemo]     = useState(null)
  const [demoLoading, setDemoLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    getDashboard(scenario)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [scenario])

  const handleDemo = async () => {
    setDemoLoading(true)
    try {
      const r = await runDemoScenario()
      setDemo(r.data)
    } catch (e) { console.error(e) }
    finally { setDemoLoading(false) }
  }

  if (loading) return <LoadingSpinner text="Loading dashboard data..." />

  const dash       = data?.dashboard || {}
  const water      = dash.water      || {}
  const equity     = dash.equity     || {}
  const alertsSum  = dash.alerts_summary || {}
  const compSum    = dash.complaints_summary || {}
  const kpis       = dash.kpis      || {}
  const allAlerts  = data?.canal_status?.all_alerts || []
  const recs       = dash.recommendations || []

  const statusColor = {
    NORMAL: 'text-green-700 bg-green-50 border-green-200',
    WARNING: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    HIGH_ALERT: 'text-orange-700 bg-orange-50 border-orange-200',
    CRITICAL: 'text-red-700 bg-red-50 border-red-200',
  }[dash.overall_system_status] || ''

  const radarData = [
    { metric: 'Head Equity',   value: (equity.head_score   || 0) * 100 },
    { metric: 'Mid Equity',    value: (equity.middle_score || 0) * 100 },
    { metric: 'Tail Equity',   value: (equity.tail_score   || 0) * 100 },
    { metric: 'Distribution',  value: (kpis.distribution_efficiency || 0) * 100 },
    { metric: 'No Shortage',   value: (1 - (water.shortage_pct || 0) / 100) * 100 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Authority Dashboard</h1>
          <p className="text-gray-500 text-sm">Narmada Canal – Real-time Monitoring & Equity Control</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-sm font-bold border ${statusColor}`}>
            ● {dash.overall_system_status || 'LOADING'}
          </span>
          <button onClick={handleDemo} disabled={demoLoading} className="btn-primary flex items-center gap-2">
            <Zap size={16} />
            {demoLoading ? 'Running...' : 'Run Demo Scenario'}
          </button>
        </div>
      </div>

      {/* Critical alerts */}
      <AlertBanner alerts={allAlerts} />

      {/* KPI Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="Available Water"  value={water.total_available_m3 ? `${(water.total_available_m3/1e6).toFixed(1)}M m³` : '–'} color="blue"   icon={Droplets} />
        <StatCard label="Shortage"         value={`${water.shortage_pct || 0}%`}   color={water.shortage_pct > 15 ? 'red' : 'green'} icon={TrendingDown} />
        <StatCard label="Head Flow"        value={`${water.head_flow_cumecs || 0} cumecs`} color="blue"   />
        <StatCard label="Tail Flow"        value={`${water.tail_flow_cumecs || 0} cumecs`} color={equity.tail_score < 0.80 ? 'orange' : 'green'} />
        <StatCard label="Active Alerts"    value={alertsSum.active || 0}  color={alertsSum.critical > 0 ? 'red' : 'orange'} icon={AlertTriangle} />
        <StatCard label="Open Disputes"    value={compSum.open || 0}      color={compSum.open > 5 ? 'red' : 'purple'} icon={Users} />
      </div>

      {/* Equity section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card lg:col-span-2 space-y-4">
          <SectionHeader title="Water Equity Metrics" sub="Head / Middle / Tail reach comparison" />
          <EquityBar
            head={equity.head_score}
            middle={equity.middle_score}
            tail={equity.tail_score}
          />
          <div className="grid grid-cols-3 gap-3 mt-2">
            {[
              { label: 'Overall Fairness', val: equity.overall_fairness, good: 0.90 },
              { label: 'Head-Tail Gap',    val: equity.head_tail_gap,    good: 0.10, inverse: true },
              { label: 'Equity Status',    text: equity.equity_status },
            ].map(({ label, val, good, inverse, text }, i) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">{label}</p>
                {text ? (
                  <p className={`text-sm font-bold ${text === 'FAIR' ? 'text-green-700' : 'text-orange-700'}`}>{text}</p>
                ) : (
                  <p className={`text-lg font-bold ${
                    (inverse ? val < good : val >= good) ? 'text-green-700' : 'text-orange-700'
                  }`}>{val != null ? `${(val*100).toFixed(1)}%` : '–'}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Radar */}
        <div className="card">
          <SectionHeader title="System Health" sub="Radar view" />
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
              <Radar name="Score" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Insight */}
      {dash.ai_insight && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-start gap-3">
            <div className="text-2xl">🤖</div>
            <div>
              <p className="font-semibold text-blue-900 text-sm">IBM Granite AI Insight</p>
              <p className="text-blue-800 text-sm mt-1">{dash.ai_insight}</p>
            </div>
          </div>
        </div>
      )}

      {/* Canal Map */}
      <div className="card">
        <SectionHeader title="Canal Network Map" sub="Reservoir → Main Canal → Head / Middle / Tail Reach" />
        <CanalMap scenario={scenario} />
      </div>

      {/* Recommendations */}
      {recs.length > 0 && (
        <div className="card">
          <SectionHeader title="AI Recommendations" sub="Requires human authority approval for starred items" />
          <div className="space-y-3">
            {recs.map((r, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="text-lg">{r.requires_approval ? '⚠️' : '💡'}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{r.recommendation}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-500">Type: {r.type}</span>
                    <span className="text-xs text-gray-500">Confidence: {r.confidence ? `${(r.confidence*100).toFixed(0)}%` : '–'}</span>
                    {r.requires_approval && (
                      <span className="badge-high">Human Approval Required</span>
                    )}
                  </div>
                </div>
                {r.requires_approval && (
                  <div className="flex gap-2 shrink-0">
                    <button className="text-xs px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 font-medium">Approve</button>
                    <button className="text-xs px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 font-medium">Reject</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Demo result */}
      {demo && (
        <div className="card bg-green-50 border-green-200">
          <SectionHeader title={`🎯 ${demo.demo_title}`} sub="Full agent orchestration cycle result" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-2">Before (Normal)</h4>
              <div className="space-y-1 text-sm">
                <p>Head equity: <strong>{demo.before?.head_equity_score?.toFixed(2)}</strong></p>
                <p>Tail equity: <strong>{demo.before?.tail_equity_score?.toFixed(2)}</strong></p>
                <p>Head-tail gap: <strong>{demo.before?.head_tail_gap?.toFixed(2)}</strong></p>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-2">After (20% Shortage)</h4>
              <div className="space-y-1 text-sm">
                <p>Head equity: <strong>{demo.after?.head_equity_score?.toFixed(2)}</strong></p>
                <p>Tail equity: <strong className="text-green-700">{demo.after?.tail_equity_score?.toFixed(2)}</strong></p>
                <p>Head-tail gap: <strong className="text-green-700">{demo.after?.head_tail_gap?.toFixed(2)}</strong></p>
              </div>
            </div>
          </div>
          {demo.ai_explanation && (
            <div className="mt-4 p-3 bg-white rounded-lg border border-green-200">
              <p className="text-xs font-semibold text-blue-800">🤖 Granite AI Explanation</p>
              <p className="text-sm text-gray-700 mt-1">{demo.ai_explanation}</p>
            </div>
          )}
          <div className="mt-3 p-3 bg-white rounded-lg border border-green-200">
            <p className="text-xs font-semibold text-gray-600 mb-1">Gap Reduction</p>
            <p className="text-sm">
              Head-tail gap: {demo.equity_improvement?.head_tail_gap_before} →{' '}
              <strong className="text-green-700">{demo.equity_improvement?.head_tail_gap_after}</strong>
              {' '}({demo.equity_improvement?.gap_reduction} improvement)
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
