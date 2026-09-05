import { useEffect, useState } from 'react'
import { floodxApi } from '@/api/client'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts'
import { Info } from 'lucide-react'

export default function Nowcast() {
  const [nowcast, setNowcast] = useState<any[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    floodxApi.flood.nowcast()
      .then(d => { setNowcast(d); if (d.length) setSelected(d[0].location_id) })
      .finally(() => setLoading(false))
    const t = setInterval(() => floodxApi.flood.nowcast().then(setNowcast), 15000)
    return () => clearInterval(t)
  }, [])

  const nc = nowcast.find(n => n.location_id === selected)
  const chartData = nc?.horizons?.map((h: any) => ({
    t: `+${h.horizon_minutes}m`,
    prob: Math.round(h.flood_probability * 100),
    depth: +h.estimated_depth_cm.toFixed(1),
    conf: Math.round(h.confidence * 100)
  })) ?? []

  const riskBadge = (r: string) => {
    const cls: Record<string, string> = {
      LOW: 'badge-low', MODERATE: 'badge-moderate',
      HIGH: 'badge-high', CRITICAL: 'badge-critical'
    }
    return <span className={cls[r] ?? 'badge-low'}>{r}</span>
  }

  return (
    <div className="h-full flex min-h-0">
      <div className="w-56 bg-surface-800 border-r border-surface-500 flex flex-col">
        <div className="px-3 py-3 border-b border-surface-500">
          <p className="section-header mb-0">Locations</p>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {nowcast.map(item => (
            <button
              key={item.location_id}
              onClick={() => setSelected(item.location_id)}
              className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                selected === item.location_id
                  ? 'bg-accent-blue/20 text-white'
                  : 'text-slate-400 hover:bg-surface-600'
              }`}
            >
              <p className="font-medium truncate">{item.location_name}</p>
              <p className="text-slate-500">
                {item.current_depth_cm.toFixed(1)} cm · {item.current_risk}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-white">0–3 Hour Nowcast</h1>
          <span className="data-badge"><Info size={10} />MODELLED</span>
        </div>

        {loading ? (
          <p className="text-slate-500 text-sm">Loading…</p>
        ) : nc ? (
          <>
            <div className="card">
              <h2 className="text-sm font-semibold text-white mb-1">{nc.location_name}</h2>
              <p className="text-xs text-slate-500 mb-3">
                Flood probability and estimated depth — 9 forecast horizons
              </p>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#243350" />
                    <XAxis dataKey="t" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                    <YAxis yAxisId="p" domain={[0, 100]}
                      tick={{ fontSize: 10, fill: '#F97316' }} unit="%" />
                    <YAxis yAxisId="d" orientation="right" domain={[0, 100]}
                      tick={{ fontSize: 10, fill: '#3B82F6' }} unit="cm" />
                    <Tooltip
                      contentStyle={{
                        background: '#111927', border: '1px solid #243350', borderRadius: 8
                      }}
                    />
                    <ReferenceLine
                      yAxisId="p" y={50} stroke="#F59E0B" strokeDasharray="4 2"
                      label={{ value: 'Threshold', position: 'right', fill: '#F59E0B', fontSize: 10 }}
                    />
                    <Area yAxisId="p" dataKey="prob" stroke="#F97316" fill="#F97316"
                      fillOpacity={0.15} strokeWidth={2} name="Flood Prob %" />
                    <Area yAxisId="d" dataKey="depth" stroke="#3B82F6" fill="#3B82F6"
                      fillOpacity={0.15} strokeWidth={2} name="Depth cm" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card overflow-auto">
              <h3 className="text-sm font-semibold text-white mb-3">Prediction Detail</h3>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-500 border-b border-surface-500">
                    <th className="text-left pb-2">Horizon</th>
                    <th className="text-right pb-2">Probability</th>
                    <th className="text-right pb-2">Depth (cm)</th>
                    <th className="text-right pb-2">Risk</th>
                    <th className="text-right pb-2">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-500/40">
                  {nc.horizons.map((h: any) => (
                    <tr key={h.horizon_minutes} className="hover:bg-surface-600">
                      <td className="py-1.5 font-mono text-slate-300">T+{h.horizon_minutes}m</td>
                      <td className="py-1.5 text-right text-white">
                        {Math.round(h.flood_probability * 100)}%
                      </td>
                      <td className="py-1.5 text-right text-accent-blue">
                        {h.estimated_depth_cm.toFixed(1)}
                      </td>
                      <td className="py-1.5 text-right">{riskBadge(h.risk_level)}</td>
                      <td className="py-1.5 text-right text-slate-400">
                        {Math.round(h.confidence * 100)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {nc.provenance && (
              <div className="card text-xs space-y-1">
                <p className="section-header">Data Provenance</p>
                <p>
                  <span className="text-slate-500">Source: </span>
                  <span className="font-mono text-amber-400">{nc.provenance.source}</span>
                </p>
                <p>
                  <span className="text-slate-500">Provider: </span>
                  <span className="text-white">{nc.provenance.provider}</span>
                </p>
                <p>
                  <span className="text-slate-500">Method: </span>
                  <span className="text-white">{nc.provenance.model_method}</span>
                </p>
                <p>
                  <span className="text-slate-500">Confidence: </span>
                  <span className="text-white">
                    {Math.round(nc.provenance.confidence * 100)}%
                  </span>
                </p>
                {nc.provenance.assumptions?.map((a: string, i: number) => (
                  <p key={i} className="text-slate-500 italic">• {a}</p>
                ))}
              </div>
            )}
          </>
        ) : (
          <p className="text-slate-500 text-sm">No location selected</p>
        )}
      </div>
    </div>
  )
}
