/**
 * FLOOD-X Interactive Flood Map
 * ===============================
 * MapLibre GL JS with:
 *   - Flood risk zone circles (colour by risk, size by depth)
 *   - Drainage network nodes (by type and utilization)
 *   - Flood zone polygon bounding boxes (catchment extents)
 *   - Safe route overlay (flood-aware Dijkstra path)
 *   - Real-time layer updates from WebSocket simulation ticks
 *   - Click interaction → location detail panel
 *
 * DATA SOURCE: SYNTHETIC_PROTOTYPE — labels on every panel
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { floodxApi } from '@/api/client'
import { useFloodXStore } from '@/store'
import {
  Layers, Info, Route, Droplets, Network,
  RefreshCw, MapPin, X, ZapOff, AlertTriangle
} from 'lucide-react'

// ── Risk colour palette ───────────────────────────────────────────────────────
const RISK_COLORS: Record<string, string> = {
  LOW: '#10B981', MODERATE: '#F59E0B', HIGH: '#F97316', CRITICAL: '#EF4444'
}

// ── Catchment polygon extents (GeoJSON Polygons from centroid + radius) ───────
// SOURCE: SYNTHETIC_PROTOTYPE — approximate bounding boxes for visualization
const CATCHMENT_POLYGONS = [
  { id: 'C001', name: 'Velachery Basin',    bbox: [80.19, 12.97, 80.24, 13.00] },
  { id: 'C002', name: 'Adyar Corridor',     bbox: [80.22, 13.00, 80.27, 13.03] },
  { id: 'C003', name: 'T. Nagar Basin',     bbox: [80.22, 13.03, 80.27, 13.06] },
  { id: 'C004', name: 'Tambaram Sub-basin', bbox: [80.09, 12.91, 80.14, 12.95] },
  { id: 'C005', name: 'Sholinganallur',     bbox: [80.21, 12.88, 80.26, 12.93] },
  { id: 'C006', name: 'Porur Lake Basin',   bbox: [80.14, 13.02, 80.19, 13.06] },
  { id: 'C007', name: 'Chromepet Basin',    bbox: [80.12, 12.94, 80.17, 12.97] },
  { id: 'C008', name: 'Perungudi Basin',    bbox: [80.23, 12.94, 80.28, 12.98] },
  { id: 'C009', name: 'Mylapore Basin',     bbox: [80.25, 13.03, 80.29, 13.06] },
  { id: 'C010', name: 'Ambattur Basin',     bbox: [80.12, 13.09, 80.17, 13.13] },
  { id: 'C011', name: 'Pallavaram Basin',   bbox: [80.12, 12.95, 80.17, 12.99] },
  { id: 'C012', name: 'KK Nagar Basin',     bbox: [80.19, 13.03, 80.22, 13.06] },
]

function buildPolygonGeoJSON(nowcasts: any[]) {
  return {
    type: 'FeatureCollection',
    features: CATCHMENT_POLYGONS.map(cp => {
      const nc = nowcasts.find(n => n.properties?.location_id === cp.id || n.properties?.location_name?.includes(cp.name.split(' ')[0]))
      const risk = nc?.properties?.risk ?? 'LOW'
      const depth = nc?.properties?.depth_cm ?? 0
      const [w, s, e, n] = cp.bbox
      return {
        type: 'Feature',
        properties: { ...cp, risk, depth_cm: depth, data_source: 'SYNTHETIC_PROTOTYPE' },
        geometry: {
          type: 'Polygon',
          coordinates: [[[w,s],[e,s],[e,n],[w,n],[w,s]]]
        }
      }
    })
  }
}

type LayerKey = 'flood_risk' | 'drainage' | 'route'

const LAYER_LABELS: Record<LayerKey, string> = {
  flood_risk: 'Flood Zones',
  drainage: 'Drainage Nodes',
  route: 'Safe Route',
}

export default function FloodMap() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const popup = useRef<maplibregl.Popup | null>(null)
  const [selectedFeature, setSelectedFeature] = useState<any>(null)
  const [activeLayers, setActiveLayers] = useState<Set<LayerKey>>(
    new Set(['flood_risk', 'drainage'])
  )
  const [isLoading, setIsLoading] = useState(true)
  const [mapReady, setMapReady] = useState(false)
  const [route, setRoute] = useState<any>(null)
  const [routeLoading, setRouteLoading] = useState(false)

  const { rainfallIntensity, nowcastZones, drainage } = useFloodXStore()

  // ── Map initialisation ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainer.current || map.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [80.2350, 13.0200],
      zoom: 11.2,
      minZoom: 9,
      maxZoom: 16,
    })

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right')
    map.current.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right')

    popup.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      maxWidth: '280px',
    })

    map.current.on('load', async () => {
      try {
        await initLayers()
        setMapReady(true)
        setIsLoading(false)
      } catch (e) {
        console.error('[FLOOD-X Map] Layer init failed', e)
        setIsLoading(false)
      }
    })

    return () => {
      popup.current?.remove()
      map.current?.remove()
      map.current = null
    }
  }, [])

  const initLayers = async () => {
    const m = map.current!

    // ── Sources ──────────────────────────────────────────────────────────────
    const [zones, nodes] = await Promise.all([
      floodxApi.flood.zones(),
      floodxApi.drainage.nodes(),
    ])

    // Flood zones (points)
    m.addSource('flood-zones', { type: 'geojson', data: zones })

    // Flood zone polygons (catchment bounding boxes)
    const polygons = buildPolygonGeoJSON(zones.features ?? [])
    m.addSource('flood-polygons', { type: 'geojson', data: polygons })

    // Drainage nodes
    m.addSource('drainage-nodes', { type: 'geojson', data: nodes })

    // Safe route (initially empty)
    m.addSource('safe-route', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] }
    })

    // ── Layers ───────────────────────────────────────────────────────────────

    // 1. Flood polygon fill
    m.addLayer({
      id: 'flood-polygon-fill',
      type: 'fill',
      source: 'flood-polygons',
      paint: {
        'fill-color': [
          'match', ['get', 'risk'],
          'LOW', '#10B981', 'MODERATE', '#F59E0B',
          'HIGH', '#F97316', 'CRITICAL', '#EF4444', '#10B981'
        ],
        'fill-opacity': 0.18,
      },
    })

    // 2. Flood polygon outline
    m.addLayer({
      id: 'flood-polygon-outline',
      type: 'line',
      source: 'flood-polygons',
      paint: {
        'line-color': [
          'match', ['get', 'risk'],
          'LOW', '#10B981', 'MODERATE', '#F59E0B',
          'HIGH', '#F97316', 'CRITICAL', '#EF4444', '#10B981'
        ],
        'line-width': 1.5,
        'line-opacity': 0.6,
        'line-dasharray': [4, 2],
      },
    })

    // 3. Flood zone point circles (risk-coloured, depth-sized)
    m.addLayer({
      id: 'flood-zones-circle',
      type: 'circle',
      source: 'flood-zones',
      paint: {
        'circle-radius': [
          'interpolate', ['linear'], ['get', 'depth_cm'],
          0, 10, 20, 18, 45, 26, 80, 34
        ],
        'circle-color': [
          'match', ['get', 'risk'],
          'LOW', '#10B981', 'MODERATE', '#F59E0B',
          'HIGH', '#F97316', 'CRITICAL', '#EF4444', '#10B981'
        ],
        'circle-opacity': 0.75,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff',
        'circle-stroke-opacity': 0.4,
      },
    })

    // 4. Flood zone labels
    m.addLayer({
      id: 'flood-zones-label',
      type: 'symbol',
      source: 'flood-zones',
      layout: {
        'text-field': ['get', 'location_name'],
        'text-size': 10,
        'text-offset': [0, 1.8],
        'text-anchor': 'top',
      },
      paint: {
        'text-color': '#CBD5E1',
        'text-halo-color': '#080C14',
        'text-halo-width': 1,
      },
    })

    // 5. Drainage nodes
    m.addLayer({
      id: 'drainage-nodes-circle',
      type: 'circle',
      source: 'drainage-nodes',
      paint: {
        'circle-radius': [
          'case',
          ['get', 'is_surcharging'], 7,
          4
        ],
        'circle-color': [
          'match', ['get', 'risk'],
          'LOW', '#10B981', 'MODERATE', '#F59E0B',
          'HIGH', '#F97316', 'CRITICAL', '#EF4444', '#10B981'
        ],
        'circle-opacity': 0.9,
        'circle-stroke-width': ['case', ['get', 'is_surcharging'], 2, 0],
        'circle-stroke-color': '#fff',
      },
    })

    // 6. Safe route line
    m.addLayer({
      id: 'safe-route-line',
      type: 'line',
      source: 'safe-route',
      paint: {
        'line-color': '#22D3EE',
        'line-width': 3.5,
        'line-opacity': 0.9,
        'line-dasharray': [2, 1],
      },
    })

    // 7. Route waypoint dots
    m.addLayer({
      id: 'safe-route-points',
      type: 'circle',
      source: 'safe-route',
      filter: ['==', '$type', 'Point'],
      paint: {
        'circle-radius': 6,
        'circle-color': '#22D3EE',
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff',
      },
    })

    // ── Interactions ──────────────────────────────────────────────────────────
    const clickableLayers = ['flood-zones-circle', 'drainage-nodes-circle', 'flood-polygon-fill']

    clickableLayers.forEach(layerId => {
      m.on('click', layerId, (e) => {
        const f = e.features?.[0]
        if (f) setSelectedFeature({ ...f.properties, _layer: layerId })
      })
      m.on('mouseenter', layerId, () => { m.getCanvas().style.cursor = 'pointer' })
      m.on('mouseleave', layerId, () => { m.getCanvas().style.cursor = '' })
    })
  }

  // ── Real-time zone updates from WS ────────────────────────────────────────
  useEffect(() => {
    if (!mapReady || !map.current) return
    const m = map.current
    if (!m.getSource('flood-zones')) return

    // Re-fetch and update sources when WS data changes
    floodxApi.flood.zones().then(zones => {
      (m.getSource('flood-zones') as maplibregl.GeoJSONSource)?.setData(zones)
      const polygons = buildPolygonGeoJSON(zones.features ?? [])
      ;(m.getSource('flood-polygons') as maplibregl.GeoJSONSource)?.setData(polygons)
    }).catch(() => {})

    floodxApi.drainage.nodes().then(nodes => {
      (m.getSource('drainage-nodes') as maplibregl.GeoJSONSource)?.setData(nodes)
    }).catch(() => {})
  }, [mapReady, nowcastZones, rainfallIntensity])

  // ── Layer visibility toggle ───────────────────────────────────────────────
  useEffect(() => {
    if (!mapReady || !map.current) return
    const m = map.current
    const layers = {
      flood_risk: ['flood-polygon-fill', 'flood-polygon-outline', 'flood-zones-circle', 'flood-zones-label'],
      drainage: ['drainage-nodes-circle'],
      route: ['safe-route-line', 'safe-route-points'],
    }
    Object.entries(layers).forEach(([key, ids]) => {
      const vis = activeLayers.has(key as LayerKey) ? 'visible' : 'none'
      ids.forEach(id => {
        if (m.getLayer(id)) m.setLayoutProperty(id, 'visibility', vis)
      })
    })
  }, [activeLayers, mapReady])

  // ── Load safe route ───────────────────────────────────────────────────────
  const loadRoute = useCallback(async () => {
    if (!mapReady || !map.current) return
    setRouteLoading(true)
    try {
      const r = await floodxApi.routes.safe({ flood_aware: true })
      setRoute(r)

      const geojson = {
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: {},
            geometry: r.geometry_geojson,
          },
          ...r.waypoints.map((wp: any) => ({
            type: 'Feature',
            properties: {},
            geometry: { type: 'Point', coordinates: [wp.lon, wp.lat] },
          })),
        ],
      }
      ;(map.current.getSource('safe-route') as maplibregl.GeoJSONSource)?.setData(geojson as any)
      setActiveLayers(prev => new Set([...prev, 'route']))
    } catch (e) {
      console.error('[FLOOD-X Map] Route load failed', e)
    } finally {
      setRouteLoading(false)
    }
  }, [mapReady])

  const toggleLayer = (l: LayerKey) => {
    setActiveLayers(prev => {
      const next = new Set(prev)
      next.has(l) ? next.delete(l) : next.add(l)
      return next
    })
  }

  const riskBg = (risk: string) => ({
    LOW: 'text-emerald-400', MODERATE: 'text-amber-400',
    HIGH: 'text-orange-400', CRITICAL: 'text-red-400',
  }[risk] || 'text-emerald-400')

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* ── Toolbar ──────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 px-4 py-2 bg-surface-800 border-b border-surface-500 flex-shrink-0 flex-wrap">
        <Layers size={14} className="text-slate-400 flex-shrink-0" />
        <span className="text-xs text-slate-500">Layers:</span>

        {(Object.keys(LAYER_LABELS) as LayerKey[]).map(l => (
          <button
            key={l}
            id={`layer-toggle-${l}`}
            onClick={() => toggleLayer(l)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-all ${
              activeLayers.has(l)
                ? 'bg-accent-blue/20 text-accent-blue border border-accent-blue/40'
                : 'text-slate-500 hover:text-slate-300 border border-transparent'
            }`}
          >
            {l === 'flood_risk' && <Droplets size={11} />}
            {l === 'drainage' && <Network size={11} />}
            {l === 'route' && <Route size={11} />}
            {LAYER_LABELS[l]}
          </button>
        ))}

        <div className="w-px h-4 bg-surface-500 mx-1" />

        <button
          id="btn-load-route"
          onClick={loadRoute}
          disabled={routeLoading}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-accent-teal/20 text-accent-teal border border-accent-teal/40 hover:bg-accent-teal/30 transition-colors disabled:opacity-50"
        >
          {routeLoading ? <RefreshCw size={11} className="animate-spin" /> : <Route size={11} />}
          {routeLoading ? 'Routing…' : 'Safe Route'}
        </button>

        <div className="ml-auto flex items-center gap-2 text-xs">
          <span className="text-slate-500">{rainfallIntensity.toFixed(1)} mm/hr</span>
          {drainage && (
            <span className={`font-semibold ${riskBg(drainage.overall_status)}`}>
              {drainage.overall_status}
            </span>
          )}
          <span className="data-badge">
            <Info size={10} />SYNTHETIC
          </span>
        </div>
      </div>

      {/* ── Map ──────────────────────────────────────────────────────────── */}
      <div className="flex-1 relative min-h-0">
        <div ref={mapContainer} className="absolute inset-0" />

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-surface-900/80 z-20">
            <div className="text-center">
              <RefreshCw size={28} className="animate-spin text-accent-blue mx-auto mb-3" />
              <p className="text-sm text-slate-300">Loading map layers…</p>
            </div>
          </div>
        )}

        {/* ── Legend ───────────────────────────────────────────────────── */}
        <div className="absolute bottom-8 left-3 card p-3 text-xs space-y-2 z-10 min-w-[120px]">
          <p className="section-header mb-1">Risk Level</p>
          {Object.entries(RISK_COLORS).map(([lvl, color]) => (
            <div key={lvl} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: color }} />
              <span className="text-slate-300">{lvl}</span>
            </div>
          ))}
          <div className="border-t border-surface-500 pt-2 mt-2">
            <p className="text-slate-500 text-[10px]">Circle size = depth</p>
            <p className="text-slate-500 text-[10px]">Surcharging = larger dot</p>
          </div>
        </div>

        {/* ── Route Info Panel ─────────────────────────────────────────── */}
        {route && activeLayers.has('route') && (
          <div className="absolute bottom-8 right-3 card p-3 text-xs z-10 min-w-[180px]">
            <div className="flex items-center justify-between mb-2">
              <p className="section-header mb-0">Safe Route</p>
              <button onClick={() => setRoute(null)} className="text-slate-500 hover:text-white">
                <X size={12} />
              </button>
            </div>
            <div className="space-y-1">
              <div className="metric-row">
                <span className="metric-label">Distance</span>
                <span className="metric-value">{route.distance_km} km</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Travel</span>
                <span className="metric-value">{route.estimated_travel_min} min</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Max Depth</span>
                <span className={`metric-value ${route.max_predicted_depth_cm > 20 ? 'text-risk-high' : 'text-risk-low'}`}>
                  {route.max_predicted_depth_cm} cm
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Zones Avoided</span>
                <span className="metric-value text-accent-teal">{route.flood_zones_avoided}</span>
              </div>
            </div>
            <p className="text-[9px] text-slate-600 mt-2 font-mono">SYNTHETIC ROUTE</p>
          </div>
        )}

        {/* ── Feature Detail Panel ──────────────────────────────────────── */}
        {selectedFeature && (
          <div className="absolute top-3 right-3 card w-64 z-10">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <MapPin size={14} className="text-accent-blue flex-shrink-0" />
                <h3 className="text-sm font-semibold text-white leading-tight">
                  {selectedFeature.location_name || selectedFeature.name || selectedFeature.node_id || 'Location'}
                </h3>
              </div>
              <button onClick={() => setSelectedFeature(null)} className="text-slate-500 hover:text-white flex-shrink-0">
                <X size={14} />
              </button>
            </div>

            <div className="space-y-1 text-xs">
              {selectedFeature.risk && (
                <div className="metric-row">
                  <span className="metric-label">Risk Level</span>
                  <span className={`font-bold text-sm ${riskBg(selectedFeature.risk)}`}>
                    {selectedFeature.risk}
                  </span>
                </div>
              )}
              {selectedFeature.depth_cm !== undefined && (
                <div className="metric-row">
                  <span className="metric-label">Flood Depth</span>
                  <span className="metric-value">{Number(selectedFeature.depth_cm).toFixed(1)} cm</span>
                </div>
              )}
              {selectedFeature.utilization_pct !== undefined && (
                <div className="metric-row">
                  <span className="metric-label">Utilization</span>
                  <span className={`metric-value ${selectedFeature.utilization_pct > 100 ? 'text-risk-critical' : 'text-risk-low'}`}>
                    {Number(selectedFeature.utilization_pct).toFixed(0)}%
                  </span>
                </div>
              )}
              {selectedFeature.is_surcharging !== undefined && (
                <div className="metric-row">
                  <span className="metric-label">Surcharging</span>
                  <span className={`metric-value ${selectedFeature.is_surcharging ? 'text-risk-critical' : 'text-risk-low'}`}>
                    {selectedFeature.is_surcharging ? 'YES ⚠' : 'No'}
                  </span>
                </div>
              )}
              {selectedFeature.node_type && (
                <div className="metric-row">
                  <span className="metric-label">Node Type</span>
                  <span className="metric-value capitalize">{selectedFeature.node_type}</span>
                </div>
              )}
              {selectedFeature.capacity_m3_s !== undefined && (
                <div className="metric-row">
                  <span className="metric-label">Capacity</span>
                  <span className="metric-value">{Number(selectedFeature.capacity_m3_s).toFixed(2)} m³/s</span>
                </div>
              )}
              <div className="metric-row">
                <span className="metric-label">Data Source</span>
                <span className="font-mono text-[10px] text-amber-400">
                  {selectedFeature.data_source || 'SYNTHETIC_PROTOTYPE'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ── Live zone summary strip ───────────────────────────────────── */}
        {nowcastZones.length > 0 && (
          <div className="absolute top-3 left-3 z-10 space-y-1 max-w-[200px]">
            {nowcastZones.filter(z => z.risk === 'HIGH' || z.risk === 'CRITICAL').slice(0, 3).map(z => (
              <div key={z.location_id} className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs backdrop-blur-sm border
                ${z.risk === 'CRITICAL' ? 'bg-red-950/80 border-red-500/40 text-red-300' : 'bg-orange-950/80 border-orange-500/40 text-orange-300'}`}>
                <AlertTriangle size={11} className="flex-shrink-0" />
                <span className="truncate font-medium">{z.location_name}</span>
                <span className="ml-auto font-mono text-[10px]">{z.depth_cm.toFixed(0)}cm</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
