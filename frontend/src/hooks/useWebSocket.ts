/**
 * useWebSocket — connects to FLOOD-X real-time stream.
 *
 * Features:
 *   - Auto-reconnect with 3s back-off
 *   - Heartbeat ping every 10s (keeps proxy connections alive)
 *   - Stale detection: marks data STALE if no message received for 15s
 *   - Connection states: LIVE | SIMULATION | STALE | DISCONNECTED
 */
import { useEffect, useRef } from 'react'
import { useFloodXStore } from '@/store'

const WS_URL = import.meta.env.VITE_WS_URL
  ?? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`

const RECONNECT_DELAY_MS  = 3000    // 3s initial reconnect
const RECONNECT_MAX_MS    = 30_000  // 30s cap (handles Render cold-start ~30-60s)
const HEARTBEAT_INTERVAL  = 10_000  // 10s ping to keep proxy alive
const STALE_THRESHOLD_MS  = 15_000  // mark STALE if silent for 15s

export function useWebSocket() {
  const wsRef           = useRef<WebSocket | null>(null)
  const reconnectTimer  = useRef<ReturnType<typeof setTimeout> | null>(null)
  const heartbeatTimer  = useRef<ReturnType<typeof setInterval> | null>(null)
  const staleTimer      = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelay  = useRef(RECONNECT_DELAY_MS)  // starts at 3s, backs off

  const { setWsConnected, setWsStale, handleWsMessage } = useFloodXStore()

  // ── Reset stale timer on every received message ─────────────────────────────
  const resetStaleTimer = () => {
    staleTimer.current && clearTimeout(staleTimer.current)
    setWsStale(false)
    staleTimer.current = setTimeout(() => {
      setWsStale(true)
      console.warn('[FLOOD-X WS] No message for 15s — marking STALE')
    }, STALE_THRESHOLD_MS)
  }

  const stopHeartbeat = () => {
    heartbeatTimer.current && clearInterval(heartbeatTimer.current)
  }

  const startHeartbeat = (ws: WebSocket) => {
    stopHeartbeat()
    heartbeatTimer.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, HEARTBEAT_INTERVAL)
  }

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      reconnectDelay.current = RECONNECT_DELAY_MS  // reset back-off on success
      setWsConnected(true)
      setWsStale(false)
      startHeartbeat(ws)
      resetStaleTimer()
      console.info('[FLOOD-X WS] Connected to', WS_URL)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'pong') return  // ignore heartbeat replies
        resetStaleTimer()
        handleWsMessage(msg)
      } catch (e) {
        console.warn('[FLOOD-X WS] Could not parse message', e)
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
      stopHeartbeat()
      staleTimer.current && clearTimeout(staleTimer.current)
      // Exponential back-off: 3s → 6s → 12s → 24s → 30s (cap)
      // Handles Render free-tier cold-start which takes 30-60s to wake
      const delay = reconnectDelay.current
      reconnectDelay.current = Math.min(delay * 2, RECONNECT_MAX_MS)
      console.warn(`[FLOOD-X WS] Disconnected — reconnecting in ${delay / 1000}s`)
      reconnectTimer.current = setTimeout(connect, delay)
    }

    ws.onerror = (e) => {
      console.error('[FLOOD-X WS] Error', e)
      ws.close()
    }
  }

  useEffect(() => {
    connect()
    return () => {
      reconnectTimer.current && clearTimeout(reconnectTimer.current)
      heartbeatTimer.current && clearInterval(heartbeatTimer.current)
      staleTimer.current     && clearTimeout(staleTimer.current)
      wsRef.current?.close()
    }
  }, [])

  /** Send an arbitrary command to the backend via WS. */
  const send = (msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }

  return { send }
}

