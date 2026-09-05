/**
 * useWebSocket — connects to FLOOD-X real-time stream.
 * Auto-reconnects on disconnect. Feeds Zustand store.
 */
import { useEffect, useRef } from 'react'
import { useFloodXStore } from '@/store'

const WS_URL = import.meta.env.VITE_WS_URL
  || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`
const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { setWsConnected, handleWsMessage } = useFloodXStore()

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
      console.info('[FLOOD-X WS] Connected')
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        handleWsMessage(msg)
      } catch (e) {
        console.warn('[FLOOD-X WS] Invalid message', e)
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
      console.warn('[FLOOD-X WS] Disconnected — reconnecting in 3s')
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
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
      wsRef.current?.close()
    }
  }, [])

  const send = (msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }

  return { send }
}
