import { useEffect, useState } from 'react'
import { floodxApi } from '@/api/client'
import { Activity, CheckCircle, AlertTriangle } from 'lucide-react'

export default function SystemHealth() {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = () => floodxApi.system.status().then(setStatus).finally(() => setLoading(false))
    load(); const t = setInterval(load, 10000); return () => clearInterval(t)
  }, [])

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <h1 className="text-xl font-bold text-white flex items-center gap-2">
        <Activity size={20} className="text-accent-cyan" /> System Health
      </h1>
      {loading ? <p className="text-slate-500">Loading…</p> : status && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card space-y-2">
            <h2 className="text-sm font-semibold text-white mb-3">Services</h2>
            {[
              { label: 'API', value: status.api_status === 'ok', text: status.api_status },
              { label: 'Database', value: status.database_status === 'ok', text: status.database_status },
              { label: 'ML Model', value: status.ml_model_loaded, text: status.ml_model_loaded ? status.ml_model_version : 'Not loaded' },
              { label: 'Simulation', value: true, text: status.simulation_active ? 'Running' : 'Idle' },
            ].map(({ label, value, text }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-xs text-slate-400">{label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-white font-mono">{text}</span>
                  {value ? <CheckCircle size={12} className="text-risk-low" /> : <AlertTriangle size={12} className="text-risk-moderate" />}
                </div>
              </div>
            ))}
          </div>
          <div className="card">
            <h2 className="text-sm font-semibold text-white mb-3">Configuration</h2>
            {[
              { label: 'Uptime', value: `${status.uptime_seconds.toFixed(0)}s` },
              { label: 'Data Mode', value: status.data_mode },
              { label: 'Rainfall Provider', value: status.rainfall_provider },
              { label: 'Terrain Provider', value: status.terrain_provider },
              { label: 'Version', value: '0.1.0' },
            ].map(({ label, value }) => (
              <div key={label} className="metric-row">
                <span className="metric-label">{label}</span>
                <span className="metric-value font-mono text-xs">{value}</span>
              </div>
            ))}
          </div>
          {status.warnings?.length > 0 && (
            <div className="card md:col-span-2">
              <h2 className="text-sm font-semibold text-white mb-2">Warnings</h2>
              {status.warnings.map((w: string, i: number) => (
                <p key={i} className="flex items-center gap-2 text-xs text-amber-400 py-1">
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
