import { useEffect, useState } from 'react'
import { floodxApi } from '@/api/client'
import { Route, Info, Navigation } from 'lucide-react'

export default function SafeRouting() {
  const [normalRoute, setNormalRoute] = useState<any>(null)
  const [floodRoute, setFloodRoute] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const loadRoutes = async () => {
    setLoading(true)
    try {
      const [n, f] = await Promise.all([
        floodxApi.routes.safe({ flood_aware: false }),
        floodxApi.routes.safe({ flood_aware: true }),
      ])
      setNormalRoute(n); setFloodRoute(f)
    } finally { setLoading(false) }
  }

  useEffect(() => { loadRoutes() }, [])

  const riskColor = (r: string) => ({ LOW: 'text-risk-low', MODERATE: 'text-risk-moderate', HIGH: 'text-risk-high', CRITICAL: 'text-risk-critical' }[r] || 'text-white')

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Route size={20} className="text-accent-cyan" /> Safe Routing
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">Flood-aware route vs normal route comparison</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="data-badge"><Info size={10} />SYNTHETIC_PROTOTYPE</span>
          <button onClick={loadRoutes} className="btn-primary py-1.5" disabled={loading}>
            {loading ? 'Calculating…' : 'Recalculate'}
          </button>
        </div>
      </div>

      {/* Origin/Destination */}
      <div className="card">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="section-header">Origin</p>
            <p className="text-sm text-white">Chennai Central (Egmore)</p>
            <p className="text-xs text-slate-500">13.0827°N 80.2707°E</p>
          </div>
          <div>
            <p className="section-header">Destination</p>
            <p className="text-sm text-white">Chennai Airport (MAA)</p>
            <p className="text-xs text-slate-500">12.9930°N 80.1708°E</p>
          </div>
        </div>
      </div>

      {/* Route comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[{ route: normalRoute, label: 'Normal Route', accent: 'border-slate-500' },
          { route: floodRoute,  label: 'Flood-Aware Route', accent: 'border-accent-blue' }].map(({ route, label, accent }) => (
          <div key={label} className={`card border-l-4 ${accent}`}>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-white">{label}</h2>
              {route && <span className={`text-sm font-bold ${riskColor(route.max_risk_level)}`}>{route.max_risk_level}</span>}
            </div>
            {route ? (
              <div className="space-y-1.5 text-xs">
                <div className="metric-row"><span className="metric-label">Distance</span><span className="metric-value">{route.distance_km.toFixed(1)} km</span></div>
                <div className="metric-row"><span className="metric-label">Travel Time</span><span className="metric-value">{route.estimated_travel_min.toFixed(0)} min</span></div>
                <div className="metric-row"><span className="metric-label">Max Flood Depth</span><span className={`metric-value ${route.max_predicted_depth_cm > 20 ? 'text-risk-critical' : 'text-risk-low'}`}>{route.max_predicted_depth_cm.toFixed(1)} cm</span></div>
                <div className="metric-row"><span className="metric-label">Flood Zones Avoided</span><span className="metric-value text-accent-cyan">{route.flood_zones_avoided}</span></div>
                <div className="panel-divider" />
                <div className="p-2 rounded bg-surface-800 font-mono text-slate-400 italic">{route.note}</div>
              </div>
            ) : <p className="text-slate-500 text-xs">Loading…</p>}
          </div>
        ))}
      </div>

      {/* Waypoints */}
      {floodRoute && (
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Navigation size={14} className="text-accent-cyan" /> Flood-Aware Route Waypoints
          </h3>
          <div className="flex flex-wrap gap-2">
            {floodRoute.waypoints.map((wp: any, i: number) => (
              <span key={i} className="text-xs font-mono bg-surface-800 px-2 py-1 rounded text-slate-300">
                {wp.lat.toFixed(4)},{wp.lon.toFixed(4)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
