/**
 * FLOOD-X Typed API Client
 * All responses are labelled with data source type.
 */

import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${BASE}/api/v1`,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor — log errors, never silently ignore
api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('[FLOOD-X API Error]', err.response?.status, err.config?.url, err.message)
    return Promise.reject(err)
  }
)

// ── API Methods ───────────────────────────────────────────────────────────────

export const floodxApi = {
  health: () => api.get('/health').then(r => r.data),

  rainfall: {
    current: () => api.get('/rainfall/current').then(r => r.data),
    forecast: (hours = 3) => api.get('/rainfall/forecast', { params: { hours } }).then(r => r.data),
  },

  flood: {
    nowcast: () => api.get('/flood/nowcast').then(r => r.data),
    zones: () => api.get('/flood/zones').then(r => r.data),
    location: (id: string) => api.get(`/flood/location/${id}`).then(r => r.data),
    clock: (id: string) => api.get(`/flood/clock/${id}`).then(r => r.data),
  },

  drainage: {
    status: () => api.get('/drainage/status').then(r => r.data),
    nodes: () => api.get('/drainage/nodes').then(r => r.data),
  },

  routes: {
    safe: (params?: { orig_lat?: number; orig_lon?: number; dest_lat?: number; dest_lon?: number; flood_aware?: boolean }) =>
      api.get('/routes/safe', { params }).then(r => r.data),
  },

  alerts: {
    list: () => api.get('/alerts').then(r => r.data),
  },

  simulation: {
    start: (scenario: string, speed = 1.0) =>
      api.post('/simulation/start', { scenario, speed }).then(r => r.data),
    pause: () => api.post('/simulation/pause').then(r => r.data),
    resume: () => api.post('/simulation/resume').then(r => r.data),
    reset: () => api.post('/simulation/reset').then(r => r.data),
    state: () => api.get('/simulation/state').then(r => r.data),
    scenarios: () => api.get('/simulation/scenarios').then(r => r.data),
  },

  system: {
    status: () => api.get('/system/status').then(r => r.data),
  },

  decisions: {
    current: () => api.get('/decisions/current').then(r => r.data),
  },

  demo: {
    start:  () => api.post('/demo/start').then(r => r.data),
    status: () => api.get('/demo/status').then(r => r.data),
    reset:  () => api.post('/demo/reset').then(r => r.data),
    phases: () => api.get('/demo/phases').then(r => r.data),
  },

  graph: {
    info: () => api.get('/routes/graph-info').then(r => r.data),
  },
}
