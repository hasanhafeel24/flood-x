/**
 * Drainage Network — Node status, utilization, bottleneck detection
 */
import { useEffect, useState } from 'react'
import { floodxApi } from '@/api/client'
import { useFloodXStore } from '@/store'
import { Network, Info } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts'

export default function DrainageNetwork() {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const { rainfallIntensity } = useFloodXStore()

  useEffect(() => {
    const load = () => floodxApi.drainage.status().then(setStatus).finally(() => setLoading(false))
    load()
    const t = setInterval(load, 10000)
    return () => clearInterval(t)
  }, [rainfallIntensity])

  const chartData = status?.nodes
    ?.sort((a: any, b: any) => b.utilization_pct - a.utilization_pct)
    ?.slice(0, 15)
    ?.map((n: any) => ({ name: n.node_id, util: +n.utilization_pct.toFixed(1), type: n.node_type })) ?? []

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Network size={20} className="text-accent-cyan" /> Drainage Network
        </h1>
        <span className="data-badge"><Info size={10} />SYNTHETIC_PROTOTYPE</span>
      </div>

      {/* Summary */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total Nodes', value: status.total_nodes, color: 'text-white' },
            { label: 'Surcharging', value: status.surcharging_nodes, color: status.surcharging_nodes > 0 ? 'text-risk-critical' : 'text-risk-low' },
            { label: 'Avg Utilization', value: `${status.average_utilization_pct.toFixed(0)}%`, color: 'text-white' },
            { label: 'Overall Status', value: status.overall_status, color: status.overall_status === 'CRITICAL' ? 'text-risk-critical' : 'text-risk-low' },
          ].map(({ label, value, color }) => (
            <div key={label} className="card">
              <p className="section-header mb-1">{label}</p>
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Bar chart */}
      {!loading && chartData.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-3">Node Utilization (Top 15)</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#243350" />
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94A3B8' }} />
                <YAxis domain={[0, 200]} tick={{ fontSize: 10, fill: '#94A3B8' }} unit="%" />
                <Tooltip contentStyle={{ background: '#111927', border: '1px solid #243350', borderRadius: 8 }} />
                <ReferenceLine y={100} stroke="#EF4444" strokeDasharray="4 2" label={{ value: 'Capacity', position: 'right', fill: '#EF4444', fontSize: 10 }} />
                <Bar dataKey="util" fill="#3B82F6" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Node table */}
      {status && (
        <div className="card overflow-auto">
          <h2 className="text-sm font-semibold text-white mb-3">All Nodes</h2>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-500 border-b border-surface-500">
                <th className="text-left pb-2">ID</th><th className="text-left pb-2">Name</th><th className="text-left pb-2">Type</th>
                <th className="text-right pb-2">Utilization</th><th className="text-right pb-2">Flow m³/s</th>
                <th className="text-right pb-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-500/40">
              {status.nodes.map((n: any) => (
                <tr key={n.node_id} className={`hover:bg-surface-600 ${n.is_surcharging ? 'bg-risk-critical/5' : ''}`}>
                  <td className="py-1.5 font-mono text-slate-300">{n.node_id}</td>
                  <td className="py-1.5 text-slate-400 max-w-[120px] truncate"></td>
                  <td className="py-1.5 text-slate-400">{n.node_type}</td>
                  <td className={`py-1.5 text-right font-semibold ${n.utilization_pct > 100 ? 'text-risk-critical' : n.utilization_pct > 80 ? 'text-risk-high' : 'text-risk-low'}`}>
                    {n.utilization_pct.toFixed(0)}%
                  </td>
                  <td className="py-1.5 text-right text-white">{n.current_flow_m3_s.toFixed(3)}</td>
                  <td className="py-1.5 text-right">
                    {n.is_surcharging ? <span className="badge-critical">SURCHARGE</span> : <span className="badge-low">OK</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
