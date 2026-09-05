/**
 * Simulation Center — Scenario control and real-time event log
 */
import { useState } from 'react'
import { floodxApi } from '@/api/client'
import { useFloodXStore } from '@/store'
import { PlayCircle, PauseCircle, RotateCcw, Info, Zap } from 'lucide-react'

const SCENARIOS = [
  { id: 'normal_rainfall',   label: 'Normal Rainfall',     intensity: '8 mm/hr',  risk: 'LOW',      color: 'text-risk-low' },
  { id: 'heavy_rainfall',    label: 'Heavy Rainfall',      intensity: '35 mm/hr', risk: 'MODERATE', color: 'text-risk-moderate' },
  { id: 'extreme_rainfall',  label: 'Extreme Rainfall',    intensity: '85 mm/hr', risk: 'HIGH',     color: 'text-risk-high' },
  { id: 'short_intense_storm',label:'Short Intense Storm', intensity: '120 mm/hr',risk: 'CRITICAL', color: 'text-risk-critical' },
  { id: 'prolonged_rainfall',label: 'Prolonged Rainfall',  intensity: '20 mm/hr', risk: 'MODERATE', color: 'text-risk-moderate' },
  { id: 'drainage_blockage', label: 'Drainage Blockage',   intensity: '30 mm/hr', risk: 'HIGH',     color: 'text-risk-high' },
  { id: 'pump_failure',      label: 'Pump Failure',        intensity: '40 mm/hr', risk: 'HIGH',     color: 'text-risk-high' },
  { id: 'combined_extreme',  label: 'Combined Extreme',    intensity: '95 mm/hr', risk: 'CRITICAL', color: 'text-risk-critical' },
]

const DEMO_SCENARIO = {
  id: 'extreme_rainfall',
  label: 'SIH Demo — Extreme Rainfall Event',
  steps: [
    { time: '0:00',  event: 'System Normal — All clear' },
    { time: '0:20',  event: 'Rainfall intensifying — IMD Extreme category' },
    { time: '0:40',  event: 'Drainage utilization rising across Chennai' },
    { time: '1:00',  event: 'Critical bottleneck detected — Adyar Basin' },
    { time: '1:20',  event: 'FLOOD-X predicts flooding in 3 locations' },
    { time: '1:40',  event: 'Flood Clock activated — T+25 min to WARNING' },
    { time: '2:00',  event: 'Road risk elevated — Kotturpuram–Adyar corridor' },
    { time: '2:20',  event: 'Safe routes recalculated — 2 flood zones avoided' },
    { time: '2:40',  event: 'Emergency recommendations issued to authorities' },
  ]
}

export default function SimulationCenter() {
  const { simulation, rainfallIntensity, drainage, phase } = useFloodXStore()
  const [selectedScenario, setSelectedScenario] = useState('extreme_rainfall')
  const [speed, setSpeed] = useState(1.0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    setLoading(true); setError(null)
    try {
      await floodxApi.simulation.start(selectedScenario, speed)
    } catch (e: any) {
      setError(e.message || 'Failed to start simulation')
    } finally {
      setLoading(false)
    }
  }

  const handlePause = async () => {
    try { await floodxApi.simulation.pause() } catch (e) {}
  }
  const handleResume = async () => {
    try { await floodxApi.simulation.resume() } catch (e) {}
  }
  const handleReset = async () => {
    setLoading(true)
    try { await floodxApi.simulation.reset() } finally { setLoading(false) }
  }

  const progress = simulation ? (simulation.step / simulation.total_steps) * 100 : 0

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Simulation Center</h1>
          <p className="text-xs text-slate-500 mt-0.5">Control rainfall scenarios and observe system response</p>
        </div>
        <span className="data-badge"><Info size={10} />SYNTHETIC SIMULATION</span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Scenario selector */}
        <div className="card xl:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold text-white">Scenario Selection</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {SCENARIOS.map(s => (
              <button
                key={s.id}
                onClick={() => setSelectedScenario(s.id)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  selectedScenario === s.id
                    ? 'border-accent-blue bg-accent-blue/10'
                    : 'border-surface-500 bg-surface-700 hover:border-surface-400'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">{s.label}</span>
                  <span className={`text-xs font-semibold ${s.color}`}>{s.risk}</span>
                </div>
                <span className="text-xs text-slate-400">Peak: {s.intensity}</span>
              </button>
            ))}
          </div>

          {/* Speed control */}
          <div className="flex items-center gap-4">
            <label className="text-xs text-slate-400 whitespace-nowrap">Speed: {speed}×</label>
            <input
              type="range" min={0.5} max={5} step={0.5}
              value={speed}
              onChange={e => setSpeed(Number(e.target.value))}
              className="flex-1 h-1 accent-accent-blue"
            />
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3 flex-wrap">
            {!simulation?.is_running ? (
              <button onClick={handleStart} disabled={loading} className="btn-primary flex items-center gap-2">
                <PlayCircle size={16} />
                {loading ? 'Starting…' : 'Start Simulation'}
              </button>
            ) : (
              <>
                {!simulation.is_paused ? (
                  <button onClick={handlePause} className="btn-primary flex items-center gap-2">
                    <PauseCircle size={16} /> Pause
                  </button>
                ) : (
                  <button onClick={handleResume} className="btn-primary flex items-center gap-2">
                    <PlayCircle size={16} /> Resume
                  </button>
                )}
              </>
            )}
            <button onClick={handleReset} className="btn-ghost flex items-center gap-2">
              <RotateCcw size={16} /> Reset
            </button>

            {/* Demo shortcut */}
            <button
              onClick={() => { setSelectedScenario('extreme_rainfall'); setSpeed(2.0) }}
              className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-lg border border-accent-cyan/40 text-accent-cyan text-xs font-semibold hover:bg-accent-cyan/10 transition-colors"
            >
              <Zap size={13} /> SIH Demo Mode
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-risk-critical/10 border border-risk-critical/30 text-xs text-risk-critical">
              Error: {error}
            </div>
          )}

          {/* Progress bar */}
          {simulation?.is_running && (
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>{phase}</span>
                <span>{simulation.step}/{simulation.total_steps} steps</span>
              </div>
              <div className="w-full h-2 bg-surface-500 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-accent-blue to-accent-cyan transition-all duration-1000"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Live State + Demo Steps */}
        <div className="space-y-4">
          {/* Live Readings */}
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-3">Live Readings</h3>
            <div className="space-y-2">
              <div className="metric-row">
                <span className="metric-label">Rainfall Intensity</span>
                <span className="metric-value text-accent-blue">{rainfallIntensity.toFixed(1)} mm/hr</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Drainage Load</span>
                <span className={`metric-value ${(drainage?.average_utilization_pct ?? 0) > 100 ? 'text-risk-critical' : 'text-white'}`}>
                  {drainage?.average_utilization_pct?.toFixed(0) ?? '—'}%
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Surcharging Nodes</span>
                <span className={`metric-value ${(drainage?.surcharging_nodes ?? 0) > 0 ? 'text-risk-critical' : 'text-risk-low'}`}>
                  {drainage?.surcharging_nodes ?? 0}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Scenario</span>
                <span className="metric-value text-xs">{simulation?.scenario ?? 'none'}</span>
              </div>
            </div>
          </div>

          {/* Demo Script */}
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-3">
              <Zap size={13} className="inline mr-1 text-accent-cyan" />
              Demo Timeline
            </h3>
            <div className="space-y-2">
              {DEMO_SCENARIO.steps.map((step, i) => {
                const stepProgress = simulation ? (simulation.step / simulation.total_steps) * DEMO_SCENARIO.steps.length : -1
                const isActive = Math.floor(stepProgress) === i
                const isPast = Math.floor(stepProgress) > i
                return (
                  <div key={i} className={`flex gap-2.5 ${isPast ? 'opacity-50' : ''}`}>
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${isActive ? 'bg-accent-cyan animate-pulse' : isPast ? 'bg-surface-400' : 'bg-surface-500'}`} />
                    <div>
                      <span className="text-xs font-mono text-slate-500">{step.time} </span>
                      <span className={`text-xs ${isActive ? 'text-white font-semibold' : 'text-slate-400'}`}>{step.event}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
