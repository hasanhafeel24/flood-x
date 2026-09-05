/**
 * FLOOD-X Alerts & Decision Support Page
 * ========================================
 * Two tabs:
 *   1. Active Alerts — threshold-based operational alerts
 *   2. Decision Recommendations — ranked, context-aware response actions
 *
 * ALL content is decision-support only. Not official emergency orders.
 * DATA SOURCE: SYNTHETIC_PROTOTYPE
 */
import { useEffect, useState } from 'react'
import { useFloodXStore } from '@/store'
import { floodxApi } from '@/api/client'
import {
  Bell, AlertTriangle, Info, Zap, Droplets,
  Navigation, Users, Radio, Shield, Eye, RefreshCw, ChevronDown, ChevronUp
} from 'lucide-react'

const SEV_STYLES: Record<string, string> = {
  EMERGENCY: 'alert-emergency', WARNING: 'alert-warning',
  WATCH: 'alert-watch', INFO: 'alert-info',
}

const URGENCY_STYLES: Record<string, string> = {
  IMMEDIATE: 'border-l-4 border-red-500 bg-red-500/10',
  HIGH:      'border-l-4 border-orange-500 bg-orange-500/10',
  MODERATE:  'border-l-4 border-amber-500 bg-amber-500/10',
  LOW:       'border-l-4 border-slate-500 bg-slate-500/10',
}

const URGENCY_BADGE: Record<string, string> = {
  IMMEDIATE: 'bg-red-500/20 text-red-400 border border-red-500/40',
  HIGH:      'bg-orange-500/20 text-orange-400 border border-orange-500/40',
  MODERATE:  'bg-amber-500/20 text-amber-400 border border-amber-500/40',
  LOW:       'bg-slate-500/20 text-slate-400 border border-slate-500/40',
}

const CATEGORY_ICON: Record<string, any> = {
  drainage_operations: Droplets,
  road_closure:        Navigation,
  evacuation:          Users,
  pump_deployment:     Zap,
  emergency_services:  Shield,
  public_alert:        Radio,
  monitoring:          Eye,
  recovery:            RefreshCw,
}

function RecommendationCard({ rec }: { rec: any }) {
  const [expanded, setExpanded] = useState(false)
  const Icon = CATEGORY_ICON[rec.category] || Shield

  return (
    <div className={`rounded-lg p-4 ${URGENCY_STYLES[rec.urgency] || URGENCY_STYLES.LOW}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-white/80
            ${rec.urgency === 'IMMEDIATE' ? 'bg-red-500/30' :
              rec.urgency === 'HIGH' ? 'bg-orange-500/30' : 'bg-amber-500/30'}`}>
            <Icon size={14} />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${URGENCY_BADGE[rec.urgency] || URGENCY_BADGE.LOW}`}>
              {rec.urgency}
            </span>
            <span className="text-[10px] text-slate-500 font-mono capitalize">
              {rec.category.replace(/_/g, ' ')}
            </span>
            <span className="ml-auto text-[10px] text-slate-500">
              {Math.round(rec.confidence * 100)}% confidence
            </span>
          </div>

          <p className="text-sm font-semibold text-white">{rec.title}</p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">{rec.rationale}</p>

          {rec.deadline_minutes && (
            <p className="text-xs text-red-400 mt-1.5 font-medium">
              ⏱ Act within {rec.deadline_minutes} minutes
            </p>
          )}

          <button
            id={`rec-expand-${rec.rec_id}`}
            onClick={() => setExpanded(e => !e)}
            className="flex items-center gap-1 text-xs text-accent-blue mt-2 hover:text-blue-300 transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded ? 'Hide' : 'Show'} action steps
          </button>

          {expanded && (
            <div className="mt-3 space-y-2">
              <div className="bg-surface-800 rounded-lg p-3">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Action Steps</p>
                <ol className="space-y-1">
                  {rec.action_steps.map((step: string, i: number) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2">
                      <span className="text-accent-blue flex-shrink-0 font-mono">{i+1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-surface-800 rounded-lg p-2.5">
                  <p className="text-[10px] text-slate-500 mb-1">Target Locations</p>
                  <p className="text-xs text-slate-300">{rec.target_locations.slice(0,2).join(', ')}</p>
                </div>
                <div className="bg-surface-800 rounded-lg p-2.5">
                  <p className="text-[10px] text-slate-500 mb-1">Estimated Impact</p>
                  <p className="text-xs text-slate-300">{rec.estimated_impact.slice(0, 80)}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AlertsPage() {
  const { alerts } = useFloodXStore()
  const [tab, setTab] = useState<'alerts' | 'decisions'>('alerts')
  const [decisions, setDecisions] = useState<any>(null)
  const [loadingDec, setLoadingDec] = useState(false)

  const fetchDecisions = async () => {
    setLoadingDec(true)
    try {
      const data = await floodxApi.decisions.current()
      setDecisions(data)
    } catch (e) {
      console.error('Decisions fetch failed', e)
    } finally {
      setLoadingDec(false)
    }
  }

  useEffect(() => {
    fetchDecisions()
    const interval = setInterval(fetchDecisions, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-500 flex-shrink-0">
        <div>
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            <Bell size={16} className="text-accent-cyan" />
            Alerts & Decision Support
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">Decision-support only — not official orders</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="data-badge"><Info size={10} />SYNTHETIC</span>
          <button onClick={fetchDecisions} disabled={loadingDec}
            className="btn-ghost py-1.5 px-2.5 flex items-center gap-1.5">
            <RefreshCw size={12} className={loadingDec ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* ── Disclaimer ─────────────────────────────────────────────────── */}
      <div className="px-4 py-2 bg-amber-500/5 border-b border-amber-500/20 flex-shrink-0">
        <div className="flex items-center gap-2 text-xs text-amber-400">
          <AlertTriangle size={12} className="flex-shrink-0" />
          <span>All alerts and recommendations are <strong>AI-generated decision support</strong>. Consult official NDMA/SDMA protocols before taking emergency action.</span>
        </div>
      </div>

      {/* ── Tabs ───────────────────────────────────────────────────────── */}
      <div className="flex gap-1 px-4 pt-3 flex-shrink-0">
        {([['alerts', `Alerts (${alerts.length})`, Bell], ['decisions', `Decisions (${decisions?.total_recommendations ?? '…'})`, Shield]] as const).map(([key, label, Icon]) => (
          <button key={key} id={`tab-${key}`}
            onClick={() => setTab(key as any)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === key
                ? 'bg-accent-blue/20 text-accent-blue border border-accent-blue/40'
                : 'text-slate-400 hover:text-white'
            }`}>
            <Icon size={11} />{label}
          </button>
        ))}

        {decisions && tab === 'decisions' && (
          <div className="ml-auto flex items-center gap-3 text-xs">
            <span className={`font-bold ${decisions.immediate_actions > 0 ? 'text-red-400 animate-pulse' : 'text-slate-400'}`}>
              {decisions.immediate_actions} IMMEDIATE
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border
              ${decisions.overall_risk === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border-red-500/40' :
                decisions.overall_risk === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border-orange-500/40' :
                decisions.overall_risk === 'MODERATE' ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' :
                'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'}`}>
              {decisions.overall_risk}
            </span>
          </div>
        )}
      </div>

      {/* ── Content ────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 mt-3">

        {/* Alerts tab */}
        {tab === 'alerts' && (
          alerts.length === 0 ? (
            <div className="card flex flex-col items-center justify-center py-16">
              <Bell size={40} className="text-slate-600 mb-3" />
              <p className="text-slate-500 text-sm">No active alerts</p>
              <p className="text-slate-600 text-xs mt-1">Start a simulation with heavy rainfall to generate alerts</p>
            </div>
          ) : (
            <div className="space-y-4">
              {(['EMERGENCY', 'WARNING', 'WATCH', 'INFO'] as const).map(sev => {
                const sAlerts = alerts.filter(a => a.severity === sev)
                if (!sAlerts.length) return null
                return (
                  <div key={sev}>
                    <p className="section-header">{sev} ({sAlerts.length})</p>
                    <div className="space-y-2">
                      {sAlerts.map(alert => (
                        <div key={alert.alert_id} className={`rounded-lg p-4 ${SEV_STYLES[sev]}`}>
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <p className="text-sm font-bold text-white">{alert.title}</p>
                              <p className="text-xs text-slate-300 mt-1">{alert.description}</p>
                              <div className="mt-2 p-2 rounded bg-surface-800 text-xs text-accent-cyan">
                                → {alert.recommended_action}
                              </div>
                            </div>
                            <div className="text-right text-xs text-slate-400 whitespace-nowrap">
                              <p>{Math.round(alert.confidence * 100)}% conf</p>
                              <p className="mt-1 font-mono text-slate-600 text-[10px]">{alert.alert_id}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )
        )}

        {/* Decisions tab */}
        {tab === 'decisions' && (
          loadingDec && !decisions ? (
            <div className="card flex flex-col items-center justify-center py-16">
              <RefreshCw size={28} className="animate-spin text-accent-blue mb-3" />
              <p className="text-slate-500 text-sm">Generating decision package…</p>
            </div>
          ) : decisions ? (
            <div className="space-y-4">
              {/* Situation summary */}
              <div className="card bg-surface-600">
                <p className="section-header">Situation Summary</p>
                <p className="text-sm text-slate-300 leading-relaxed">{decisions.situation_summary}</p>
                <p className="text-[10px] text-slate-600 mt-2 font-mono">{decisions.package_id}</p>
              </div>

              {/* Recommendations */}
              <div>
                <p className="section-header">Ranked Recommendations</p>
                <div className="space-y-3">
                  {decisions.recommendations.map((rec: any) => (
                    <RecommendationCard key={rec.rec_id} rec={rec} />
                  ))}
                </div>
              </div>

              <div className="card bg-surface-600 text-xs text-slate-500">
                <p>{decisions.disclaimer}</p>
              </div>
            </div>
          ) : (
            <div className="card flex flex-col items-center justify-center py-16">
              <Shield size={40} className="text-slate-600 mb-3" />
              <p className="text-slate-500 text-sm">No decisions available</p>
            </div>
          )
        )}
      </div>
    </div>
  )
}
