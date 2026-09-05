import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import CommandCenter from '@/pages/CommandCenter'
import FloodMap from '@/pages/FloodMap'
import Nowcast from '@/pages/Nowcast'
import DrainageNetwork from '@/pages/DrainageNetwork'
import FloodClockPage from '@/pages/FloodClockPage'
import SafeRouting from '@/pages/SafeRouting'
import AlertsPage from '@/pages/AlertsPage'
import SimulationCenter from '@/pages/SimulationCenter'
import DataConfidence from '@/pages/DataConfidence'
import SystemHealth from '@/pages/SystemHealth'
import Methodology from '@/pages/Methodology'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<CommandCenter />} />
          <Route path="map" element={<FloodMap />} />
          <Route path="nowcast" element={<Nowcast />} />
          <Route path="drainage" element={<DrainageNetwork />} />
          <Route path="flood-clock" element={<FloodClockPage />} />
          <Route path="routing" element={<SafeRouting />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="simulation" element={<SimulationCenter />} />
          <Route path="data" element={<DataConfidence />} />
          <Route path="health" element={<SystemHealth />} />
          <Route path="methodology" element={<Methodology />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
