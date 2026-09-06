/**
 * FLOOD-X — Data & Model Confidence
 * ====================================
 * Transparency panel — shows:
 *   1. Live XGBoost feature importance (bar chart from /explain/feature-importance)
 *   2. Per-data-source confidence bars
 *   3. Provider status from /system/status
 *   4. SYNTHETIC_PROTOTYPE label on every item
 */
import { useEffect, useState, useCallback } from 'react'
import { floodxApi } from '@/api/client'
import {
  Database, Info, AlertTriangle, RefreshCw, Activity,
  CheckCircle, BarChart2, Cpu, Cloud, Network, Map, Archive, Brain
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, CartesianGrid
} from 'recharts'

// ── Data source definitions ──────────────────────────────────────────────────
const SOURCES = [
  {
    icon: Cloud,
    name: 'Rainfall Data',
    type: 'SYNTHETIC_PROTOTYPE',
    note: 'IMD classification thresholds used. Real-time feed requires IMD API key + station subscription.',
    confidence: 100,
    realPath: 'IMD API → Live gauge data',
    color: 'text-blue-400',
  },
  {
    icon: Map,
    name: 'Terrain / DEM',
    type: 'SYNTHETIC_PROTOTYPE',
    note: 'SRTM 30m DEM available via USGS EarthExplorer — file provider implemented, using synthetic prototype here.',
    confidence: 85,
    realPath: 'SRTM 30m DEM → dem_provider.py',
    color: 'text-emerald-400',
  },
  {
    icon: Network,
    name: 'Drainage Network',
    type: 'SYNTHETIC_PROTOTYPE',
    note: '30-node prototype based on published urban drainage studies. Real CMWSSB SCADA data unavailable publicly.',
    confidence: 70,
    realPath: 'CMWSSB SCADA → drainage_provider.py',
    color: 'text-amber-400',
  },
  {
    icon: Map,
    name: 'Road Network',
    type: 'SYNTHETIC_PROTOTYPE',
    note: 'OpenStreetMap roads available via osmnx — prototype uses 22 simplified waypoints for demo clarity.',
    confidence: 75,
    realPath: 'osmnx.graph_from_place("Chennai") → 50k+ nodes',
    color: 'text-purple-400',
  },
  {
    icon: Archive,
    name: 'Flood History',
    type: 'SYNTHETIC_PROTOTYPE',
    note: 'No geolocated historical flood event dataset publicly available for Chennai. Labels derived from physics simulation.',
    confidence: 60,
    realPath: 'IMD historical + Chennai Corporation records',
    color: 'text-orange-400',
  },
  {
    icon: Brain,
    name: 'ML Predictions',
    type: 'MODELLED',
    note: 'XGBoost model (97.4% acc, R²=0.995) trained on 8000 synthetic samples. Real-event validation pending.',
    confidence: 70,
    realPath: 'Re-train on real flood event labels → production model',
    color: 'text-cyan-400',
  },
  {
    icon: Activity,
    name: 'Hydrology Model',
    type: 'MODELLED',
    note: 'SCS-CN + Rational Method — USDA-NRCS standard. Defensible for urban prototype. Not validated vs real Chennai events.',
    confidence: 75,
    realPath: 'Real storm data calibration → adjust CN, Tc parameters',
    color: 'text-teal-400',
  },
]

// ── Custom tooltip for recharts ──────────────────────────────────────────────
function ImportanceTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-surface-700 border border-surface-500 rounded-lg p-3 text-xs shadow-xl">
      <p className="font-semibold text-white mb-1">{d.label}</p>
      <p className="text-accent-cyan">Importance: <span className="font-bold">{d.importance_pct.toFixed(1)}%</span></p>
      <p className="text-slate-400 mt-0.5">Rank #{d.rank}</p>
    </div>
  )
}

export default function DataConfidence() {
  const [system, setSystem] = useState<any>(null)
  const [features, setFeatures] = useState<any[]>([])
  const [featureLoading, setFeatureLoading] = useState(true)
  const [featureError, setFeatureError] = useState(false)
  const [activeSource, setActiveSource] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setFeatureLoading(true)
    setFeatureError(false)
    try {
      const [sys, fi] = await Promise.all([
        floodxApi.system.status(),
        floodxApi.explain.featureImportance(),
      ])
      setSystem(sys)
      setFeatures(fi.features ?? [])
    } catch (e) {
      setFeatureError(true)
      // still try system status alone
      try { setSystem(await floodxApi.system.status()) } catch {}
    } finally {
      setFeatureLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // Top-10 for chart, sorted by importance descending
  const chartData = features.slice(0, 10).map(f => ({
    ...f,
    shortLabel: f.label.replace('Rainfall ', '').replace('Drainage ', '').replace('Terrain ', '').replace('Antecedent ', 'Ant. ').replace('Catchment ', ''),
  }))

  // Colour gradient: top features = cyan, lower = slate
  const barColor = (rank: number) => {
    if (rank <= 2) return '#06B6D4'  // cyan
    if (rank <= 4) return '#3B82F6'  // blue
    if (rank <= 6) return '#8B5CF6'  // purple
    return '#475569'                  // slate
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-5">

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Database size={20} className="text-accent-cyan" />
            Data &amp; Model Confidence
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">Full transparency — every data source, model, and confidence score</p>
        </div>
        <button
          onClick={fetchData}
          className="btn-ghost flex items-center gap-1.5 py-1.5 text-xs"
        >
          <RefreshCw size={12} />
          Refresh
        </button>
      </div>

      {/* ── Transparency pledge ──────────────────────────────────────────────── */}
      <div className="card bg-blue-500/5 border-blue-500/20 flex items-start gap-3">
        <Info size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-blue-300 leading-relaxed">
          <strong className="text-blue-200">FLOOD-X Transparency Commitment:</strong> Every API response exposes{' '}
          <code className="bg-blue-500/20 px-1 rounded">data_source</code>,{' '}
          <code className="bg-blue-500/20 px-1 rounded">model_version</code>, and{' '}
          <code className="bg-blue-500/20 px-1 rounded">confidence</code> fields.
          Synthetic data is never presented as real — it is labelled on every endpoint, every UI panel, and every prediction.
        </div>
      </div>

      {/* ── XGBoost Feature Importance ─────────────────────────────────────── */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu size={16} className="text-accent-cyan" />
            <h2 className="text-sm font-semibold text-white">XGBoost Feature Importance (Gain)</h2>
          </div>
          <span className="data-badge-simulated text-[10px]">MODELLED · SYNTHETIC DATA</span>
        </div>

        {featureLoading ? (
          <div className="flex items-center justify-center h-40 text-slate-500 text-sm gap-2">
            <Activity size={16} className="animate-pulse" />
            Loading feature importance from ML model…
          </div>
        ) : featureError ? (
          <div className="flex flex-col items-center justify-center h-40 text-slate-500 text-sm gap-2">
            <AlertTriangle size={20} className="text-amber-400" />
            <p>Backend not reachable — start the backend to load live ML data</p>
          </div>
        ) : (
          <>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 40, bottom: 0, left: 110 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2D3D" horizontal={false} />
                  <XAxis
                    type="number"
                    domain={[0, Math.max(...chartData.map(d => d.importance_pct)) * 1.15]}
                    tickFormatter={v => `${v.toFixed(0)}%`}
                    tick={{ fontSize: 10, fill: '#94A3B8' }}
                  />
                  <YAxis
                    type="category"
                    dataKey="shortLabel"
                    tick={{ fontSize: 10, fill: '#CBD5E1' }}
                    width={110}
                  />
                  <Tooltip content={<ImportanceTooltip />} cursor={{ fill: 'rgba(59,130,246,0.07)' }} />
                  <Bar dataKey="importance_pct" radius={[0, 4, 4, 0]} barSize={14}>
                    {chartData.map((entry) => (
                      <Cell key={entry.feature} fill={barColor(entry.rank)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Feature table */}
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-500 border-b border-surface-500">
                    <th className="text-left pb-1.5 font-medium w-6">#</th>
                    <th className="text-left pb-1.5 font-medium">Feature</th>
                    <th className="text-right pb-1.5 font-medium">Importance</th>
                    <th className="text-right pb-1.5 font-medium pr-2">Share</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-500/40">
                  {features.slice(0, 7).map(f => (
                    <tr key={f.feature} className="hover:bg-surface-600 transition-colors">
                      <td className="py-1.5 text-slate-500">{f.rank}</td>
                      <td className="py-1.5 text-slate-300 font-mono text-[10px]">{f.feature}</td>
                      <td className="py-1.5 text-right text-white">{f.importance.toFixed(4)}</td>
                      <td className="py-1.5 text-right pr-2">
                        <div className="flex items-center justify-end gap-1.5">
                          <div className="w-12 h-1.5 bg-surface-500 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-accent-blue to-accent-cyan"
                              style={{ width: `${Math.min(f.importance_pct * 3, 100)}%` }}
                            />
                          </div>
                          <span className="text-slate-400">{f.importance_pct.toFixed(1)}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[10px] text-slate-600 mt-2">
              XGBoost gain importance · Model trained on SYNTHETIC_PROTOTYPE data (8000 samples, seed=42)
            </p>
          </>
        )}
      </div>

      {/* ── Data Source Cards ─────────────────────────────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <BarChart2 size={14} className="text-accent-cyan" />
          Data Source Confidence
        </h2>
        <div className="space-y-2">
          {SOURCES.map(s => {
            const Icon = s.icon
            const isActive = activeSource === s.name
            return (
              <div
                key={s.name}
                className={`card cursor-pointer transition-all duration-200 ${isActive ? 'border-accent-blue/40 bg-surface-600' : 'hover:border-surface-400'}`}
                onClick={() => setActiveSource(isActive ? null : s.name)}
              >
                <div className="flex items-center gap-3">
                  <Icon size={15} className={`flex-shrink-0 ${s.color}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-white">{s.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                        s.type === 'MODELLED'
                          ? 'bg-purple-500/20 text-purple-400'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}>
                        {s.type}
                      </span>
                    </div>
                    {/* Confidence bar */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1 bg-surface-500 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-accent-blue to-accent-cyan transition-all duration-700"
                          style={{ width: `${s.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-white w-8 text-right">{s.confidence}%</span>
                    </div>
                  </div>
                </div>

                {/* Expanded detail */}
                {isActive && (
                  <div className="mt-3 pt-3 border-t border-surface-500/50 space-y-2">
                    <p className="text-xs text-slate-400 leading-relaxed">{s.note}</p>
                    <div className="flex items-start gap-1.5">
                      <CheckCircle size={11} className="text-accent-cyan mt-0.5 flex-shrink-0" />
                      <p className="text-[10px] text-accent-cyan font-mono">{s.realPath}</p>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
        <p className="text-[10px] text-slate-600 mt-2">Click any card to expand the real-data upgrade path.</p>
      </div>

      {/* ── Provider Status ──────────────────────────────────────────────────── */}
      {system && (
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Activity size={14} className="text-accent-cyan" />
            Live Provider Status
          </h2>
          <div className="space-y-1.5 text-xs">
            {[
              { label: 'Rainfall Provider', value: system.rainfall_provider },
              { label: 'Terrain Provider',  value: system.terrain_provider },
              { label: 'Drainage Provider', value: system.drainage_provider },
              { label: 'ML Model',          value: system.ml_model_loaded ? `Loaded (${system.ml_model_version})` : 'Not loaded' },
              { label: 'Data Mode',         value: system.data_mode },
            ].map(({ label, value }) => (
              <div key={label} className="metric-row">
                <span className="metric-label">{label}</span>
                <span className="metric-value font-mono text-[11px]">{value}</span>
              </div>
            ))}
          </div>

          {system.warnings?.length > 0 && (
            <div className="mt-3 space-y-1">
              {system.warnings.map((w: string, i: number) => (
                <p key={i} className="flex items-center gap-1.5 text-xs text-amber-400">
                  <AlertTriangle size={11} />{w}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Footer disclaimer ───────────────────────────────────────────────── */}
      <div className="text-center text-[10px] text-slate-600 pb-2">
        All predictions carry{' '}
        <code className="bg-surface-600 px-1 rounded">"data_source": "SYNTHETIC_PROTOTYPE"</code>{' '}
        in every API response. Not for operational deployment.
      </div>
    </div>
  )
}
