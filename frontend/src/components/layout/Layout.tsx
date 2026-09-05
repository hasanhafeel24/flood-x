import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useFloodXStore } from '@/store'
import {
  LayoutDashboard, Map, Clock, Network, Timer,
  Route, Bell, PlayCircle, Database, Activity,
  BookOpen, Wifi, WifiOff, AlertTriangle
} from 'lucide-react'

const NAV_ITEMS = [
  { path: '/',           icon: LayoutDashboard, label: 'Command Center' },
  { path: '/map',        icon: Map,             label: 'Live Flood Map' },
  { path: '/nowcast',    icon: Clock,           label: 'Nowcast 0–3h' },
  { path: '/drainage',   icon: Network,         label: 'Drainage Network' },
  { path: '/flood-clock',icon: Timer,           label: 'Flood Clock' },
  { path: '/routing',    icon: Route,           label: 'Safe Routing' },
  { path: '/alerts',     icon: Bell,            label: 'Alerts' },
  { path: '/simulation', icon: PlayCircle,      label: 'Simulation' },
  { path: '/data',       icon: Database,        label: 'Data & Confidence' },
  { path: '/health',     icon: Activity,        label: 'System Health' },
  { path: '/methodology',icon: BookOpen,        label: 'Methodology' },
]

export default function Layout() {
  useWebSocket()
  const { wsConnected, rainfallIntensity, simulation, alerts, dataMode } = useFloodXStore()
  const location = useLocation()

  const criticalAlerts = alerts.filter(a => a.severity === 'EMERGENCY' || a.severity === 'WARNING')

  return (
    <div className="flex h-screen bg-surface-900 overflow-hidden">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="w-56 flex-shrink-0 bg-surface-800 border-r border-surface-500 flex flex-col">
        {/* Logo */}
        <div className="px-4 py-4 border-b border-surface-500">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-blue to-accent-cyan flex items-center justify-center">
              <span className="text-white font-bold text-xs">FX</span>
            </div>
            <div>
              <div className="font-bold text-white text-sm tracking-wide">FLOOD-X</div>
              <div className="text-xs text-slate-500 font-mono">SIH26085</div>
            </div>
          </div>
        </div>

        {/* Status bar */}
        <div className="px-3 py-2 border-b border-surface-500 flex items-center gap-2">
          {wsConnected
            ? <Wifi size={12} className="text-risk-low" />
            : <WifiOff size={12} className="text-risk-critical animate-pulse" />
          }
          <span className="text-xs text-slate-400">
            {wsConnected ? 'Live' : 'Disconnected'}
          </span>
          <span className="ml-auto text-xs font-mono text-amber-400">SIM</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                isActive ? 'nav-item-active' : 'nav-item'
              }
            >
              <Icon size={15} />
              <span className="truncate">{label}</span>
              {path === '/alerts' && criticalAlerts.length > 0 && (
                <span className="ml-auto text-xs bg-risk-critical text-white rounded-full w-4 h-4 flex items-center justify-center font-bold">
                  {criticalAlerts.length}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-surface-500">
          <div className="data-badge w-full justify-center">
            <AlertTriangle size={10} />
            {dataMode}
          </div>
          <div className="text-xs text-slate-600 text-center mt-1.5">
            Chennai Pilot · v0.1.0
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-11 bg-surface-800 border-b border-surface-500 px-4 flex items-center gap-4 flex-shrink-0">
          <span className="text-xs text-slate-500 font-mono">
            {new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })} IST
          </span>
          <span className="text-xs text-slate-500">Chennai Metropolitan Area</span>
          {simulation?.is_running && (
            <span className="ml-2 flex items-center gap-1.5 text-xs text-accent-cyan">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan animate-pulse" />
              {simulation.phase_label}
            </span>
          )}
          <div className="ml-auto flex items-center gap-3">
            <span className="text-xs text-slate-400">
              Rainfall: <span className="text-white font-semibold">{rainfallIntensity.toFixed(1)} mm/hr</span>
            </span>
            {criticalAlerts.length > 0 && (
              <span className="flex items-center gap-1 text-xs text-risk-critical">
                <AlertTriangle size={12} />
                {criticalAlerts.length} active alert{criticalAlerts.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-hidden">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
