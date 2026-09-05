/**
 * FLOOD-X Global State — Zustand Store
 * Manages simulation state, real-time data, and UI state.
 */

import { create } from 'zustand'

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
export type AlertSeverity = 'INFO' | 'WATCH' | 'WARNING' | 'EMERGENCY'
export type SimulationScenario =
  | 'normal_rainfall' | 'heavy_rainfall' | 'extreme_rainfall'
  | 'short_intense_storm' | 'prolonged_rainfall' | 'drainage_blockage'
  | 'pump_failure' | 'combined_extreme'

export interface Alert {
  alert_id: string
  severity: AlertSeverity
  title: string
  description: string
  location_name: string
  latitude: number
  longitude: number
  issued_at: string
  recommended_action: string
  confidence: number
}

export interface SimulationState {
  run_id: string
  scenario: SimulationScenario
  is_running: boolean
  is_paused: boolean
  elapsed_seconds: number
  rainfall_intensity_mm_hr: number
  step: number
  total_steps: number
  phase_label: string
}

export interface DrainageSummary {
  overall_status: RiskLevel
  average_utilization_pct: number
  surcharging_nodes: number
  bottleneck_nodes: string[]
}

interface FloodXState {
  // Connection
  wsConnected: boolean
  dataMode: string

  // Rainfall
  rainfallIntensity: number
  rainfallAccumulated: number

  // Simulation
  simulation: SimulationState | null
  phase: string

  // Drainage
  drainage: DrainageSummary | null

  // Alerts
  alerts: Alert[]

  // UI
  selectedLocationId: string | null
  activeLayer: string

  // Actions
  setWsConnected: (v: boolean) => void
  setRainfall: (intensity: number, accumulated: number) => void
  setSimulation: (s: SimulationState) => void
  setDrainage: (d: DrainageSummary) => void
  setAlerts: (a: Alert[]) => void
  setPhase: (p: string) => void
  setSelectedLocation: (id: string | null) => void
  setActiveLayer: (layer: string) => void
  handleWsMessage: (msg: any) => void
}

export const useFloodXStore = create<FloodXState>((set) => ({
  wsConnected: false,
  dataMode: 'SYNTHETIC_SIMULATION',
  rainfallIntensity: 0,
  rainfallAccumulated: 0,
  simulation: null,
  phase: 'System Initialising',
  drainage: null,
  alerts: [],
  selectedLocationId: null,
  activeLayer: 'flood_risk',

  setWsConnected: (v) => set({ wsConnected: v }),
  setRainfall: (intensity, accumulated) =>
    set({ rainfallIntensity: intensity, rainfallAccumulated: accumulated }),
  setSimulation: (s) => set({ simulation: s }),
  setDrainage: (d) => set({ drainage: d }),
  setAlerts: (a) => set({ alerts: a }),
  setPhase: (p) => set({ phase: p }),
  setSelectedLocation: (id) => set({ selectedLocationId: id }),
  setActiveLayer: (layer) => set({ activeLayer: layer }),

  handleWsMessage: (msg) => {
    if (msg.type === 'simulation_tick') {
      set({
        rainfallIntensity: msg.rainfall?.intensity_mm_hr ?? 0,
        rainfallAccumulated: msg.rainfall?.accumulated_mm ?? 0,
        simulation: msg.simulation,
        drainage: msg.drainage,
        alerts: msg.alerts ?? [],
        phase: msg.phase ?? '',
        dataMode: msg.data_mode ?? 'SYNTHETIC_SIMULATION',
      })
    } else if (msg.type === 'simulation_reset') {
      set({ simulation: null, rainfallIntensity: 0, alerts: [], phase: 'System Normal' })
    }
  },
}))
