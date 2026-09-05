import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { floodxApi } from '@/api/client'
import { useFloodXStore } from '@/store'
import { Layers, Info } from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  LOW: '#10B981', MODERATE: '#F59E0B', HIGH: '#F97316', CRITICAL: '#EF4444'
}

export default function FloodMap() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [selectedFeature, setSelectedFeature] = useState<any>(null)
  const [activeLayer, setActiveLayer] = useState('flood_risk')
  const { rainfallIntensity } = useFloodXStore()

  useEffect(() => {
    if (!mapContainer.current || map.current) return
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [80.2707, 13.0827],
      zoom: 11,
    })
    map.current.addControl(new maplibregl.NavigationControl(), 'top-right')

    map.current.on('load', async () => {
      try {
        const zones = await floodxApi.flood.zones()
        const nodes = await floodxApi.drainage.nodes()

        map.current!.addSource('flood-zones', { type: 'geojson', data: zones })
        map.current!.addLayer({
          id: 'flood-zones-circle',
          type: 'circle',
          source: 'flood-zones',
          paint: {
            'circle-radius': 18,
            'circle-color': [
              'match', ['get', 'risk'],
              'LOW', '#10B981', 'MODERATE', '#F59E0B',
              'HIGH', '#F97316', 'CRITICAL', '#EF4444', '#10B981'
            ],
            'circle-opacity': 0.7,
            'circle-stroke-width': 1.5,
            'circle-stroke-color': '#fff',
          }
        })

        map.current!.addSource('drainage-nodes', { type: 'geojson', data: nodes })
        map.current!.addLayer({
          id: 'drainage-nodes-circle',
          type: 'circle',
          source: 'drainage-nodes',
          paint: {
            'circle-radius': 5,
            'circle-color': [
              'match', ['get', 'risk'],
              'LOW', '#10B981', 'MODERATE', '#F59E0B',
              'HIGH', '#F97316', 'CRITICAL', '#EF4444', '#10B981'
            ],
            'circle-opacity': 0.9,
          }
        })

        map.current!.on('click', 'flood-zones-circle', (e) => {
          const f = e.features?.[0]
          if (f) setSelectedFeature(f.properties)
        })
        map.current!.on('mouseenter', 'flood-zones-circle', () => {
          if (map.current) map.current.getCanvas().style.cursor = 'pointer'
        })
        map.current!.on('mouseleave', 'flood-zones-circle', () => {
          if (map.current) map.current.getCanvas().style.cursor = ''
        })
      } catch (e) {
        console.error('Map data load failed', e)
      }
    })

    return () => { map.current?.remove(); map.current = null }
  }, [])

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-3 px-4 py-2 bg-surface-800 border-b border-surface-500 flex-shrink-0">
        <Layers size={14} className="text-slate-400" />
        <span className="text-xs text-slate-400">Layers:</span>
        {['flood_risk', 'drainage', 'rainfall'].map(l => (
          <button key={l} onClick={() => setActiveLayer(l)}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${activeLayer === l ? 'bg-accent-blue text-white' : 'text-slate-400 hover:text-white'}`}>
            {l.replace('_', ' ')}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2">
          <span className="data-badge"><Info size={10} />SYNTHETIC DATA</span>
          <span className="text-xs text-slate-500">
            Rainfall: {rainfallIntensity.toFixed(1)} mm/hr
          </span>
        </div>
      </div>

      <div className="flex-1 relative">
        <div ref={mapContainer} className="absolute inset-0" />

        <div className="absolute bottom-6 left-4 card p-3 text-xs space-y-1.5 z-10">
          <p className="section-header mb-1">Risk Level</p>
          {Object.entries(RISK_COLORS).map(([lvl, color]) => (
            <div key={lvl} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ background: color }} />
              <span className="text-slate-300">{lvl}</span>
            </div>
          ))}
        </div>

        {selectedFeature && (
          <div className="absolute top-4 right-4 card max-w-xs z-10 animate-fade-in">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-white">{selectedFeature.location_name}</h3>
              <button onClick={() => setSelectedFeature(null)} className="text-slate-500 hover:text-white">✕</button>
            </div>
            <div className="space-y-1 text-xs">
              <div className="metric-row">
                <span className="metric-label">Risk</span>
                <span className="metric-value">{selectedFeature.risk}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Depth</span>
                <span className="metric-value">{selectedFeature.depth_cm?.toFixed?.(1) ?? '—'} cm</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Source</span>
                <span className="metric-value font-mono text-amber-400">{selectedFeature.data_source}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
