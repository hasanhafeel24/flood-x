/**
 * FLOOD-X Command Center — Main Dashboard
 * The operational hub: KPIs, live map, alerts, nowcast timeline.
 */
import { useEffect, useState, useCallback } from 'react'
import { useFloodXStore } from '@/store'
import { floodxApi } from '@/api/client'
import {
  CloudRain, AlertTriangle, Network, Activity,
  Route, Radio, RefreshCw, Info
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

interface KPICardProps {
  label: string
  value: string | number
  unit?: string
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'stable'
  color?: string
  subtitle?: string
}

function KPICard({ label, value, unit, icon, color = 'text-accent-blue', subtitle }: KPICardProps) {
  return (
    <div className="kpi-card">
      <div className="flex items-start justify-between">
        <span className="section-header mb-0">{label}</span>
        <span className={color}>{icon}</span>
      </div>
      <div className="mt-2">
        <span className={`text-2xl font-bold ${color}`}>{value}</span>
        {unit && <span className="text-sm text-slate-400 ml-1">{unit}</span>}
      </div>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  )
}

function RiskBadge({ level }: { level: string }) {
  const map: Record<string, string> = {
    LOW: 'badge-low', MODERATE: 'badge-moderate',
    HIGH: 'badge-high', CRITICAL: 'badge-critical',
  }
  return <span className={map[level] || 'badge-low'}>{level}</span>
}

function AlertCard({ alert }: { alert: any }) {
  const borderMap: Record<string, string> = {
    EMERGENCY: 'alert-emergency', WARNING: 'alert-warning',
    WATCH: 'alert-watch', INFO: 'alert-info',
  }
  return (
    <div className={`rounded-lg p-3 ${borderMap[alert.severity] || 'alert-info'}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white truncate">{alert.title}</p>
          <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{alert.description}</p>
          <p className="text-xs text-accent-cyan mt-1 italic">{alert.recommended_action}</p>
        </div>
        <span className="text-xs text-slate-500 whitespace-nowrap">
          {Math.round(alert.confidence * 100)}% conf
        </span>
      </div>
    </div>
  )
}

export default function CommandCenter() {
  const { rainfallIntensity, rainfallAccumulated, drainage, alerts, simulation, phase } = useFloodXStore()
  const [nowcast, setNowcast] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const fetchNowcast = useCallback(async () => {
    try {
      const data = await floodxApi.flood.nowcast()
      setNowcast(data)
    } catch (e) {
      console.error('Nowcast fetch failed', e)
    } finally {
      setLoading(false)
      setLastRefresh(new Date())
    }
  }, [])

  useEffect(() => {
    fetchNowcast()
    const interval = setInterval(fetchNowcast, 15000)
    return () => clearInterval(interval)
  }, [fetchNowcast])

  // Build timeline chart data from nowcast horizons
  const chartData = nowcast.length > 0
    ? nowcast[0].horizons.map((h: any) => ({
        t: `T+${h.horizon_minutes}`,
        prob: Math.round(h.flood_probability * 100),
        depth: h.estimated_depth_cm,
      }))
    : []

  const floodedZones = nowcast.filter((n: any) =>
    n.current_risk === 'HIGH' || n.current_risk === 'CRITICAL'
  ).length

  const criticalNodes = drainage?.bottleneck_nodes?.length ?? 0
  const avgUtil = drainage?.average_utilization_pct ?? 0
  const activeAlerts = alerts.length

  return (
    <div className="h-full flex flex-col overflow-hidden p-4 gap-4">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-white">Command Center</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {phase || 'System Normal'} · Updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="data-badge">
            <Info size={10} />
            SYNTHETIC SIMULATION
          </span>
          <button onClick={fetchNowcast} className="btn-ghost flex items-center gap-1.5 py-1.5">
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── KPI Row ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 flex-shrink-0">
        <KPICard
          label="Rainfall"
          value={rainfallIntensity.toFixed(1)}
          unit="mm/hr"
          icon={<CloudRain size={16} />}
          color="text-accent-blue"
          subtitle={`${rainfallAccumulated.toFixed(1)} mm accumulated`}
        />
        <KPICard
          label="Flooded Zones"
          value={floodedZones}
          unit={`/ ${nowcast.length}`}
          icon={<AlertTriangle size={16} />}
          color={floodedZones > 0 ? 'text-risk-high' : 'text-risk-low'}
          subtitle="HIGH or CRITICAL risk"
        />
        <KPICard
          label="Critical Nodes"
          value={criticalNodes}
          icon={<Network size={16} />}
          color={criticalNodes > 0 ? 'text-risk-critical' : 'text-risk-low'}
          subtitle="Drainage bottlenecks"
        />
        <KPICard
          label="Drainage Load"
          value={avgUtil.toFixed(0)}
          unit="%"
          icon={<Activity size={16} />}
          color={avgUtil > 100 ? 'text-risk-critical' : avgUtil > 80 ? 'text-risk-high' : 'text-accent-teal'}
          subtitle="Average utilization"
        />
        <KPICard
          label="Active Alerts"
          value={activeAlerts}
          icon={<Radio size={16} />}
          color={activeAlerts > 0 ? 'text-risk-high' : 'text-risk-low'}
          subtitle="Decision-support only"
        />
        <KPICard
          label="Safe Routes"
          value={floodedZones > 0 ? 'ACTIVE' : 'NORMAL'}
          icon={<Route size={16} />}
          color={floodedZones > 0 ? 'text-risk-moderate' : 'text-risk-low'}
          subtitle="Flood-aware routing"
        />
      </div>

      {/* ── Main Content ──────────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Nowcast Chart */}
        <div className="xl:col-span-2 card flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div>
              <h2 className="text-sm font-semibold text-white">0–3 Hour Nowcast Timeline</h2>
              <p className="text-xs text-slate-500">Flood probability & depth forecast (modelled)</p>
            </div>
            <span className="data-badge-simulated text-xs">MODELLED</span>
          </div>

          {loading ? (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
              Loading nowcast data…
            </div>
          ) : chartData.length > 0 ? (
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#243350" />
                  <XAxis dataKey="t" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <YAxis yAxisId="prob" domain={[0, 100]} tick={{ fontSize: 10, fill: '#94A3B8' }} unit="%" />
                  <YAxis yAxisId="depth" orientation="right" domain={[0, 100]} tick={{ fontSize: 10, fill: '#60A5FA' }} unit="cm" />
                  <Tooltip
                    contentStyle={{ background: '#111927', border: '1px solid #243350', borderRadius: 8 }}
                    labelStyle={{ color: '#94A3B8', fontSize: 11 }}
                  />
                  <Area yAxisId="prob" type="monotone" dataKey="prob" stroke="#F97316" fill="#F97316" fillOpacity={0.15} strokeWidth={2} name="Flood Prob %" />
                  <Area yAxisId="depth" type="monotone" dataKey="depth" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.15} strokeWidth={2} name="Depth (cm)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
              Start a simulation to generate nowcast data
            </div>
          )}

          {/* Location table */}
          {nowcast.length > 0 && (
            <div className="mt-3 flex-shrink-0 overflow-auto max-h-40">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-500 border-b border-surface-500">
                    <th className="text-left pb-1.5 font-medium">Location</th>
                    <th className="text-right pb-1.5 font-medium">Risk</th>
                    <th className="text-right pb-1.5 font-medium">Depth</th>
                    <th className="text-right pb-1.5 font-medium">T+60</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-500/40">
                  {nowcast.slice(0, 6).map((nc: any) => {
                    const h60 = nc.horizons?.find((h: any) => h.horizon_minutes === 60)
                    return (
                      <tr key={nc.location_id} className="hover:bg-surface-600 transition-colors">
                        <td className="py-1.5 text-slate-300 truncate max-w-[160px]">{nc.location_name}</td>
                        <td className="py-1.5 text-right"><RiskBadge level={nc.current_risk} /></td>
                        <td className="py-1.5 text-right text-white">{nc.current_depth_cm.toFixed(1)} cm</td>
                        <td className="py-1.5 text-right text-slate-400">{h60 ? `${Math.round(h60.flood_probability * 100)}%` : '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Alerts Panel */}
        <div className="card flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <h2 className="text-sm font-semibold text-white">Active Alerts</h2>
            {alerts.length > 0 && (
              <span className="text-xs bg-risk-critical/20 text-risk-critical px-2 py-0.5 rounded-full">
                {alerts.length}
              </span>
            )}
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto space-y-2">
            {alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500">
                <Activity size={32} className="mb-2 opacity-30" />
                <p className="text-sm">No active alerts</p>
                <p className="text-xs mt-1">Start a simulation to generate alerts</p>
              </div>
            ) : (
              alerts.map((alert) => (
                <AlertCard key={alert.alert_id} alert={alert} />
              ))
            )}
          </div>

          {/* Drainage summary */}
          {drainage && (
            <>
              <div className="panel-divider" />
              <div className="flex-shrink-0">
                <p className="section-header">Drainage Summary</p>
                <div className="space-y-1">
                  <div className="metric-row">
                    <span className="metric-label">Overall Status</span>
                    <RiskBadge level={drainage.overall_status} />
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">Avg Utilization</span>
                    <span className="metric-value">{drainage.average_utilization_pct.toFixed(0)}%</span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">Surcharging Nodes</span>
                    <span className={`metric-value ${drainage.surcharging_nodes > 0 ? 'text-risk-critical' : 'text-risk-low'}`}>
                      {drainage.surcharging_nodes}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
