import { useEffect, useState } from 'react'
import { floodxApi } from '@/api/client'
import { Database, Info, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

export default function DataConfidence() {
  const [system, setSystem] = useState<any>(null)

  useEffect(() => {
    floodxApi.system.status().then(setSystem)
  }, [])

  const SOURCES = [
    { name: 'Rainfall Data', type: 'SYNTHETIC_PROTOTYPE', note: 'IMD classification used for intensity thresholds. Real-time feed requires IMD API key.', confidence: 100, tag: 'Synthetic' },
    { name: 'Terrain / DEM', type: 'SYNTHETIC_PROTOTYPE', note: 'SRTM 30m DEM available — using synthetic prototype for this demo. File provider ready.', confidence: 85, tag: 'Synthetic' },
    { name: 'Drainage Network', type: 'SYNTHETIC_PROTOTYPE', note: 'Real CMWSSB data unavailable. 30-node prototype network based on published urban drainage studies.', confidence: 70, tag: 'Synthetic' },
    { name: 'Road Network', type: 'SYNTHETIC_PROTOTYPE', note: 'OSM roads available for Chennai — prototype uses simplified waypoints.', confidence: 75, tag: 'Synthetic' },
    { name: 'Flood History', type: 'SYNTHETIC_PROTOTYPE', note: 'No geolocated historical flood events available publicly. Labels derived from simulation.', confidence: 60, tag: 'Synthetic' },
    { name: 'ML Predictions', type: 'MODELLED', note: 'XGBoost model trained on synthetic simulation outputs. Performance on real events unknown.', confidence: 70, tag: 'Modelled' },
    { name: 'Hydrology Model', type: 'MODELLED', note: 'SCS-CN + Rational Method. Defensible for urban prototype. Not validated vs real Chennai floods.', confidence: 75, tag: 'Modelled' },
  ]

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Database size={20} className="text-accent-cyan" /> Data & Model Confidence
        </h1>
        <span className="data-badge"><Info size={10} />TRANSPARENCY PANEL</span>
      </div>

      <div className="card bg-blue-500/5 border-blue-500/20 text-xs text-blue-300 flex items-start gap-2">
        <Info size={14} className="flex-shrink-0 mt-0.5" />
        <span>FLOOD-X is committed to data transparency. Every prediction exposes its data source, model, and confidence level. Synthetic data is clearly labelled and never presented as real.</span>
      </div>

      <div className="space-y-3">
        {SOURCES.map(s => (
          <div key={s.name} className="card">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-white">{s.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded font-mono ${s.type === 'MODELLED' ? 'bg-purple-500/20 text-purple-400' : 'bg-amber-500/20 text-amber-400'}`}>{s.type}</span>
                </div>
                <p className="text-xs text-slate-400">{s.note}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-lg font-bold text-white">{s.confidence}%</p>
                <p className="text-xs text-slate-500">Confidence</p>
              </div>
            </div>
            <div className="mt-2 w-full h-1.5 bg-surface-500 rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-accent-blue to-accent-cyan transition-all"
                style={{ width: `${s.confidence}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* System status */}
      {system && (
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-3">Provider Status</h2>
          <div className="space-y-1.5 text-xs">
            {[
              { label: 'Rainfall Provider', value: system.rainfall_provider },
              { label: 'Terrain Provider',  value: system.terrain_provider },
              { label: 'Drainage Provider', value: system.drainage_provider },
              { label: 'ML Model',          value: system.ml_model_loaded ? `Loaded (${system.ml_model_version})` : 'Not loaded (M8)' },
              { label: 'Data Mode',         value: system.data_mode },
            ].map(({ label, value }) => (
              <div key={label} className="metric-row">
                <span className="metric-label">{label}</span>
                <span className="metric-value font-mono text-xs">{value}</span>
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
    </div>
  )
}
