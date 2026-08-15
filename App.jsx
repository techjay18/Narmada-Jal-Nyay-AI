import React, { useState } from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { Droplets, LayoutDashboard, Waves, Users, AlertTriangle, MessageSquare, Activity, ChevronDown } from 'lucide-react'
import clsx from 'clsx'

import AuthorityDashboard from './pages/AuthorityDashboard.jsx'
import CanalMonitoring   from './pages/CanalMonitoring.jsx'
import WaterDistribution from './pages/WaterDistribution.jsx'
import FarmerPortal      from './pages/FarmerPortal.jsx'
import DisputeManagement from './pages/DisputeManagement.jsx'
import AIAssistant       from './pages/AIAssistant.jsx'

const NAV_ITEMS = [
  { to: '/dashboard',   label: 'Dashboard',      icon: LayoutDashboard },
  { to: '/canal',       label: 'Canal Monitor',  icon: Waves           },
  { to: '/schedule',    label: 'Distribution',   icon: Droplets        },
  { to: '/farmer',      label: 'Farmer Portal',  icon: Users           },
  { to: '/disputes',    label: 'Disputes',       icon: AlertTriangle   },
  { to: '/ai',          label: 'AI Assistant',   icon: MessageSquare   },
]

const SCENARIOS = ['normal', 'shortage', 'anomaly', 'recovery']

export default function App() {
  const [scenario, setScenario] = useState('normal')

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ── */}
      <header className="bg-gradient-to-r from-blue-900 to-blue-700 text-white sticky top-0 z-50 shadow-lg">
        <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">💧</div>
            <div>
              <h1 className="font-bold text-xl tracking-tight leading-none">Narmada Jal Nyay AI</h1>
              <p className="text-blue-200 text-xs">Fair Water for Every Farmer · Gujarat Canal System</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Scenario selector */}
            <div className="flex items-center gap-2 bg-blue-800 rounded-lg px-3 py-2">
              <Activity size={14} className="text-blue-300" />
              <span className="text-xs text-blue-200">Demo:</span>
              <select
                value={scenario}
                onChange={e => setScenario(e.target.value)}
                className="bg-transparent text-white text-xs font-medium outline-none cursor-pointer"
              >
                {SCENARIOS.map(s => (
                  <option key={s} value={s} className="bg-blue-900 text-white">
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div className="text-xs text-blue-200 hidden sm:block">
              IBM Granite · watsonx.ai
            </div>
          </div>
        </div>

        {/* ── Nav ── */}
        <nav className="max-w-screen-xl mx-auto px-4 flex gap-1 pb-0 overflow-x-auto">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-1.5 px-3 py-2 text-sm font-medium whitespace-nowrap rounded-t-lg transition-colors',
                  isActive
                    ? 'bg-white text-blue-900'
                    : 'text-blue-200 hover:text-white hover:bg-blue-800'
                )
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </nav>
      </header>

      {/* ── Main ── */}
      <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/"           element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard"  element={<AuthorityDashboard scenario={scenario} />} />
          <Route path="/canal"      element={<CanalMonitoring    scenario={scenario} />} />
          <Route path="/schedule"   element={<WaterDistribution  scenario={scenario} />} />
          <Route path="/farmer"     element={<FarmerPortal       scenario={scenario} />} />
          <Route path="/disputes"   element={<DisputeManagement  />} />
          <Route path="/ai"         element={<AIAssistant        scenario={scenario} />} />
        </Routes>
      </main>

      <footer className="bg-gray-100 border-t border-gray-200 text-center text-xs text-gray-500 py-3">
        Narmada Jal Nyay AI · Built with IBM Bob · Powered by IBM Granite &amp; IBM Cloud ·{' '}
        <span className="text-blue-600">Simulated Data – Prototype Only</span>
      </footer>
    </div>
  )
}
