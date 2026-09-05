/**
 * FLOOD-X Safe Routing Page
 * ==========================
 * Shows flood-aware vs normal route comparison.
 * Uses NetworkX Dijkstra with flood-risk-weighted edges.
 *
 * DATA SOURCE: SYNTHETIC_PROTOTYPE road network
 * ALGORITHM: Dijkstra with flood-risk multipliers (1x / 2x / 5x / 20x)
 */
import { useEffect, useState } from 'react'
import { floodxApi } from '@/api/client'
import { useFloodXStore } from '@/store'
import {
  Route, Info, Navigation, Shield, AlertTriangle,
  RefreshCw, Network, Clock, MapPin, Zap
} from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  LOW: 'text-emerald-400', MODERATE: 'text-amber-400',
  HIGH: 'text-orange-400', CRITICAL: 'text-red-400',
}

const RISK_BADGE: Record<string, string> = {
  LOW:      'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  MODERATE: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  HIGH:     'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  CRITICAL: 'bg-red-500/20 text-red-400 border border-red-500/30',
}

interface Route {
  route_id: string
  distance_km: number
  estimated_travel_min: number
  max_predicted_depth_cm: number
  max_risk_level: string
  flood_zones_avoided: number
  waypoints: { lat: number; lon: number }[]
  note: string
  geometry_geojson?: any
}

export default function SafeRouting() {
  const [normalRoute, setNormalRoute] = useState<Route | null>(null)
  const [floodRoute, setFloodRoute] = useState<Route | null>(null)
  const [graphInfo, setGraphInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const { rainfallIntensity, drainage } = useFloodXStore()

  const loadRoutes = async () => {
    setLoading(true)
    try {
      const [n, f, g] = await Promise.all([
        floodxApi.routes.safe({ flood_aware: false }),
        floodxApi.routes.safe({ flood_aware: true }),
        floodxApi.graph.info(),
      ])
      setNormalRoute(n)
      setFloodRoute(f)
      setGraphInfo(g)
    } catch (e) {
      console.error('[FLOOD-X Routing] Load failed', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadRoutes() }, [])

  // Re-fetch when simulation state changes meaningfully
  useEffect(() => {
    const timeout = setTimeout(loadRoutes, 500)
    return () => clearTimeout(timeout)
  }, [Math.round(rainfallIntensity / 10)])  // re-fetch on 10mm/hr intensity change

  const timeDiff = (normalRoute && floodRoute)
    ? floodRoute.estimated_travel_min - normalRoute.estimated_travel_min
    : null

  const depthSaved = (normalRoute && floodRoute)
    ? normalRoute.max_predicted_depth_cm - floodRoute.max_predicted_depth_cm
    : null

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Route size={20} className="text-accent-cyan" />
            Flood-Aware Safe Routing
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Dijkstra algorithm with flood-risk edge weights — SYNTHETIC_PROTOTYPE road network
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="data-badge"><Info size={10} />SYNTHETIC</span>
          <button id="btn-recalculate-routes" onClick={loadRoutes} disabled={loading}
            className="btn-primary py-1.5 flex items-center gap-1.5">
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Routing…' : 'Recalculate'}
          </button>
        </div>
      </div>

      {/* ── Live conditions strip ─────────────────────────────────────── */}
      <div className="card bg-surface-600 flex items-center gap-4 py-2.5">
        <div className="flex items-center gap-2 text-xs">
          <Zap size={12} className="text-accent-blue" />
          <span className="text-slate-400">Live Conditions:</span>
          <span className="text-white font-semibold">{rainfallIntensity.toFixed(1)} mm/hr</span>
        </div>
        {drainage && (
          <>
            <div className="w-px h-4 bg-surface-500" />
            <div className="flex items-center gap-2 text-xs">
              <Shield size={12} className="text-accent-blue" />
              <span className="text-slate-400">Network Risk:</span>
              <span className={`font-bold ${RISK_COLORS[drainage.overall_status]}`}>
                {drainage.overall_status}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Surcharging:</span>
              <span className={drainage.surcharging_nodes > 0 ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                {drainage.surcharging_nodes} nodes
              </span>
            </div>
          </>
        )}
        <p className="ml-auto text-[10px] text-slate-600">Routes update automatically with conditions</p>
      </div>

      {/* ── Route endpoints ───────────────────────────────────────────── */}
      <div className="card">
        <div className="grid grid-cols-2 gap-6">
          <div className="flex items-start gap-2">
            <MapPin size={16} className="text-emerald-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="section-header mb-1">Origin</p>
              <p className="text-sm text-white font-medium">Chennai Central (Egmore)</p>
              <p className="text-xs text-slate-500 font-mono">13.0827°N 80.2707°E</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <MapPin size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="section-header mb-1">Destination</p>
              <p className="text-sm text-white font-medium">Chennai Airport (MAA)</p>
              <p className="text-xs text-slate-500 font-mono">12.9930°N 80.1708°E</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Comparison summary ────────────────────────────────────────── */}
      {normalRoute && floodRoute && (
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              label: 'Extra Travel Time',
              value: timeDiff !== null ? `+${timeDiff.toFixed(0)} min` : '—',
              sub: 'flood-aware vs normal',
              color: timeDiff && timeDiff > 5 ? 'text-amber-400' : 'text-emerald-400',
              icon: Clock,
            },
            {
              label: 'Depth Avoided',
              value: depthSaved !== null ? `${Math.abs(depthSaved).toFixed(0)} cm` : '—',
              sub: 'max depth reduction',
              color: 'text-accent-cyan',
              icon: Shield,
            },
            {
              label: 'Zones Avoided',
              value: floodRoute.flood_zones_avoided.toString(),
              sub: 'HIGH/CRITICAL avoided',
              color: 'text-accent-blue',
              icon: Route,
            },
          ].map(({ label, value, sub, color, icon: Icon }) => (
            <div key={label} className="card text-center py-3">
              <Icon size={16} className={`${color} mx-auto mb-1.5`} />
              <p className={`text-xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-white mt-0.5">{label}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">{sub}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── Route detail cards ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { route: normalRoute, label: 'Normal Route', accent: 'border-slate-600', tag: 'Shortest Distance' },
          { route: floodRoute,  label: 'Flood-Aware Route', accent: 'border-accent-blue', tag: 'Recommended' },
        ].map(({ route, label, accent, tag }) => (
          <div key={label} className={`card border-l-4 ${accent}`}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm font-semibold text-white">{label}</p>
                <span className="text-[10px] text-slate-500">{tag}</span>
              </div>
              {route && (
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_BADGE[route.max_risk_level] || RISK_BADGE.LOW}`}>
                  {route.max_risk_level}
                </span>
              )}
            </div>

            {route ? (
              <div className="space-y-2 text-xs">
                <div className="metric-row">
                  <span className="metric-label">Distance</span>
                  <span className="metric-value">{route.distance_km.toFixed(1)} km</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Travel Time</span>
                  <span className="metric-value">{route.estimated_travel_min.toFixed(0)} min</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Max Flood Depth</span>
                  <span className={`metric-value ${route.max_predicted_depth_cm > 20 ? 'text-risk-critical' : 'text-risk-low'}`}>
                    {route.max_predicted_depth_cm.toFixed(1)} cm
                  </span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">HIGH/CRIT Zones</span>
                  <span className="metric-value text-accent-cyan">{route.flood_zones_avoided} avoided</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Waypoints</span>
                  <span className="metric-value">{route.waypoints.length} nodes</span>
                </div>
                <div className="panel-divider" />
                <p className="font-mono text-slate-500 italic text-[10px] leading-relaxed">{route.note}</p>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <RefreshCw size={12} className="animate-spin" />
                Calculating route…
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ── Flood-aware route waypoints ───────────────────────────────── */}
      {floodRoute && (
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Navigation size={14} className="text-accent-cyan" />
            Flood-Aware Route Path
            <span className="text-xs text-slate-500 font-normal ml-1">({floodRoute.waypoints.length} waypoints)</span>
          </h3>
          <div className="flex flex-wrap gap-2">
            {floodRoute.waypoints.map((wp, i) => (
              <div key={i} className="flex items-center gap-1">
                {i > 0 && <span className="text-slate-600 text-xs">→</span>}
                <span className="text-xs font-mono bg-surface-800 px-2 py-1 rounded text-accent-blue">
                  {wp.lat.toFixed(4)},{wp.lon.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Graph Info ───────────────────────────────────────────────── */}
      {graphInfo && (
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Network size={14} className="text-accent-blue" />
            Road Graph Details
          </h3>
          <div className="grid grid-cols-2 gap-4 text-xs mb-3">
            <div className="metric-row"><span className="metric-label">Nodes</span><span className="metric-value">{graphInfo.nodes}</span></div>
            <div className="metric-row"><span className="metric-label">Edges</span><span className="metric-value">{graphInfo.edges}</span></div>
            <div className="metric-row"><span className="metric-label">Algorithm</span><span className="metric-value text-accent-cyan">Dijkstra (NetworkX)</span></div>
            <div className="metric-row"><span className="metric-label">Source</span><span className="font-mono text-amber-400 text-[10px]">{graphInfo.data_source}</span></div>
          </div>
          <div className="bg-surface-800 rounded-lg p-3">
            <p className="text-[10px] text-slate-400 mb-2 uppercase tracking-wider font-semibold">Flood Weight Multipliers</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              {graphInfo.flood_weight_multipliers && Object.entries(graphInfo.flood_weight_multipliers).map(([risk, mult]) => (
                <div key={risk} className="flex justify-between">
                  <span className={`font-semibold ${RISK_COLORS[risk] || 'text-slate-400'}`}>{risk}</span>
                  <span className="text-slate-400 font-mono">{String(mult)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Warning ──────────────────────────────────────────────────── */}
      <div className="card bg-amber-500/5 border-amber-500/20">
        <div className="flex items-start gap-2 text-xs text-amber-400">
          <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
          <span>Routes use a <strong>synthetic road network</strong> (22 nodes, approximate Chennai topology). Real deployment uses <code>osmnx.graph_from_place("Chennai")</code> with 50,000+ real nodes.</span>
        </div>
      </div>
    </div>
  )
}
