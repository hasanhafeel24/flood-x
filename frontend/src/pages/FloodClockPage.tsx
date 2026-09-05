/**
 * Flood Clock — Signature Feature
 * Shows time-to-critical for each location.
 */
import { useEffect, useState } from 'react'
import { floodxApi } from '@/api/client'
import { Timer, Info, AlertTriangle } from 'lucide-react'

const STATUS_STYLES: Record<string, { color: string; bg: string; label: string }> = {
  SAFE:     { color: 'text-risk-low',      bg: 'bg-risk-low/10 border-risk-low/30',      label: 'SAFE' },
  WATCH:    { color: 'text-risk-moderate', bg: 'bg-risk-moderate/10 border-risk-moderate/30', label: 'WATCH' },
  WARNING:  { color: 'text-risk-high',     bg: 'bg-risk-high/10 border-risk-high/30',    label: 'WARNING' },
  CRITICAL: { color: 'text-risk-critical', bg: 'bg-risk-critical/10 border-risk-critical/30 animate-pulse-slow', label: 'CRITICAL' },
}

function ClockCard({ clock }: { clock: any }) {
  const s = STATUS_STYLES[clock.current_status] || STATUS_STYLES.SAFE
  return (
    <div className={`card border ${s.bg}`}>
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="text-sm font-semibold text-white">{clock.location_name}</h3>
          <p className="text-xs text-slate-500">{clock.latitude.toFixed(4)}°N {clock.longitude.toFixed(4)}°E</p>
        </div>
        <span className={`text-lg font-black ${s.color}`}>{s.label}</span>
      </div>

      {/* Time indicators */}
      <div className="grid grid-cols-3 gap-2 my-3">
        {[
          { label: 'WATCH in', value: clock.time_to_watch_min, color: 'text-risk-moderate' },
          { label: 'WARNING in', value: clock.time_to_warning_min, color: 'text-risk-high' },
          { label: 'CRITICAL in', value: clock.time_to_critical_min, color: 'text-risk-critical' },
        ].map(({ label, value, color }) => (
          <div key={label} className="text-center bg-surface-800 rounded-lg py-2">
            <p className="text-xs text-slate-500">{label}</p>
            <p className={`text-lg font-bold ${color}`}>
              {value != null ? `${value}m` : '—'}
            </p>
          </div>
        ))}
      </div>

      <div className="panel-divider" />

      {/* Timeline strip */}
      <div className="flex gap-0.5">
        {clock.timeline?.map((entry: any, i: number) => {
          const st = STATUS_STYLES[entry.status]
          return (
            <div key={i} title={`T+${entry.minutes_from_now}m: ${entry.status} (${entry.estimated_depth_cm.toFixed(1)}cm)`}
              className={`flex-1 h-3 rounded-sm ${entry.status === 'SAFE' ? 'bg-risk-low/40' : entry.status === 'WATCH' ? 'bg-risk-moderate/60' : entry.status === 'WARNING' ? 'bg-risk-high/60' : 'bg-risk-critical/80'}`} />
          )
        })}
      </div>
      <div className="flex justify-between text-xs text-slate-600 mt-0.5">
        <span>Now</span><span>+3h</span>
      </div>

      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="text-slate-500">Peak depth: <span className="text-white">{clock.estimated_peak_depth_cm.toFixed(1)} cm</span></span>
        <span className="text-slate-500">Confidence: <span className="text-white">{Math.round(clock.confidence * 100)}%</span></span>
      </div>
    </div>
  )
}

export default function FloodClockPage() {
  const [clocks, setClocks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadClocks = async () => {
      try {
        const nowcast = await floodxApi.flood.nowcast()
        const clockData = await Promise.all(
          nowcast.slice(0, 12).map((nc: any) => floodxApi.flood.clock(nc.location_id).catch(() => null))
        )
        setClocks(clockData.filter(Boolean))
      } finally { setLoading(false) }
    }
    loadClocks()
    const t = setInterval(loadClocks, 20000)
    return () => clearInterval(t)
  }, [])

  const critical = clocks.filter(c => c.current_status === 'CRITICAL').length
  const warning  = clocks.filter(c => c.current_status === 'WARNING').length

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Timer size={20} className="text-accent-cyan" />Flood Clock
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Predicts when each location will become dangerous — powered by nowcast engine
          </p>
        </div>
        <div className="flex items-center gap-3">
          {critical > 0 && (
            <span className="flex items-center gap-1.5 text-xs text-risk-critical font-semibold">
              <AlertTriangle size={12} />{critical} CRITICAL
            </span>
          )}
          <span className="data-badge"><Info size={10} />MODELLED</span>
        </div>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Safe',     count: clocks.filter(c=>c.current_status==='SAFE').length,     color: 'text-risk-low' },
          { label: 'Watch',    count: clocks.filter(c=>c.current_status==='WATCH').length,    color: 'text-risk-moderate' },
          { label: 'Warning',  count: warning,  color: 'text-risk-high' },
          { label: 'Critical', count: critical, color: 'text-risk-critical' },
        ].map(({ label, count, color }) => (
          <div key={label} className="card text-center">
            <p className="section-header mb-0">{label}</p>
            <p className={`text-3xl font-black ${color} mt-1`}>{loading ? '—' : count}</p>
          </div>
        ))}
      </div>

      {/* Clock cards */}
      {loading ? (
        <div className="text-center text-slate-500 py-8">Loading Flood Clock data…</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {clocks
            .sort((a, b) => {
              const order = { CRITICAL: 0, WARNING: 1, WATCH: 2, SAFE: 3 }
              return (order[a.current_status as keyof typeof order] ?? 3) - (order[b.current_status as keyof typeof order] ?? 3)
            })
            .map(clock => <ClockCard key={clock.location_id} clock={clock} />)}
        </div>
      )}
    </div>
  )
}
