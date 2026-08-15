import React from 'react'
import clsx from 'clsx'

export function Badge({ type, children }) {
  const classes = {
    head: 'badge-head', middle: 'badge-middle', tail: 'badge-tail',
    critical: 'badge-critical', high: 'badge-high', medium: 'badge-medium',
    low: 'badge-low', normal: 'badge-normal',
    open: 'badge-high', resolved: 'badge-low', under_review: 'badge-medium',
  }
  return <span className={classes[type] || 'badge-normal'}>{children}</span>
}

export function StatCard({ label, value, sub, color = 'blue', icon: Icon }) {
  const colors = {
    blue:   'text-blue-600',
    green:  'text-green-600',
    orange: 'text-orange-600',
    red:    'text-red-600',
    purple: 'text-purple-600',
  }
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</span>
        {Icon && <Icon size={18} className="text-gray-400" />}
      </div>
      <div className={clsx('text-2xl font-bold', colors[color])}>{value}</div>
      {sub && <div className="text-xs text-gray-500">{sub}</div>}
    </div>
  )
}

export function EquityBar({ head, middle, tail }) {
  return (
    <div className="flex items-center gap-1 w-full">
      <div className="flex gap-2 text-xs w-full">
        {[
          { label: 'Head', value: head, color: 'bg-blue-500' },
          { label: 'Middle', value: middle, color: 'bg-purple-500' },
          { label: 'Tail', value: tail, color: 'bg-orange-500' },
        ].map(({ label, value, color }) => (
          <div key={label} className="flex-1">
            <div className="flex justify-between mb-1">
              <span className="text-gray-500">{label}</span>
              <span className="font-semibold">{value != null ? `${(value*100).toFixed(1)}%` : '–'}</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className={clsx('h-full rounded-full', color)} style={{ width: `${(value||0)*100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function AlertBanner({ alerts = [] }) {
  const critical = alerts.filter(a => a.severity === 'critical')
  if (!critical.length) return null
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
      <span className="text-red-500 text-xl">🚨</span>
      <div>
        <p className="font-semibold text-red-800">Critical Alert</p>
        {critical.slice(0,2).map((a, i) => (
          <p key={i} className="text-sm text-red-700">{a.message}</p>
        ))}
      </div>
    </div>
  )
}

export function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-gray-500 text-sm p-8 justify-center">
      <div className="spinner" />
      {text}
    </div>
  )
}

export function SectionHeader({ title, sub, children }) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        {sub && <p className="text-sm text-gray-500">{sub}</p>}
      </div>
      {children}
    </div>
  )
}
