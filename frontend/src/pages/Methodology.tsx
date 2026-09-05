import { BookOpen, Info } from 'lucide-react'

export default function Methodology() {
  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <h1 className="text-xl font-bold text-white flex items-center gap-2">
        <BookOpen size={20} className="text-accent-cyan" /> About & Methodology
      </h1>

      {[
        {
          title: 'What is FLOOD-X?',
          content: `FLOOD-X is an AI-Powered Urban Flood Nowcasting & Decision Support System built for SIH 2026 (Problem Statement SIH26085).
          It implements a credible end-to-end pipeline: Rainfall → Runoff → Drainage → Hydraulic State → AI Prediction → 0–3h Nowcast → Flood Depth → Risk → Safe Routes → Alerts.`
        },
        {
          title: 'Hydrology Model',
          content: `Rainfall-to-Runoff: SCS Curve Number (CN) method — USDA-NRCS standard, widely used in Indian urban hydrology.
          Peak Flow: Rational Method (Q = C×I×A/360).
          Time of Concentration: Kirpich (1940) formula.
          Assumptions: Uniform rainfall, AMC II moisture, no pipe routing in prototype.`
        },
        {
          title: 'Drainage Model',
          content: `Simplified Rational Method for inflow estimation. 30-node synthetic prototype network (not real CMWSSB data).
          Capacity utilization, surcharge detection, bottleneck identification via directed graph.
          SWMM integration path documented for production deployment.`
        },
        {
          title: 'AI/ML Pipeline',
          content: `Primary: XGBoost Classifier (flood probability) + XGBoost Regressor (flood depth).
          Comparison: Logistic Regression, Random Forest, DummyClassifier baseline.
          Features: rainfall intensity, duration, cumulative, drainage utilization, elevation, slope, imperviousness.
          Training data: Synthetic simulation outputs — physically consistent but not real event labels.`
        },
        {
          title: 'Nowcast Engine',
          content: `9 prediction horizons: T+0, T+15, T+30, T+45, T+60, T+90, T+120, T+150, T+180 minutes.
          Rainfall forecast: Exponential decay model from current intensity.
          Depth: Surface ponding estimate — not full hydrodynamic model.
          Confidence decreases with forecast horizon and rainfall variability.`
        },
        {
          title: 'Flood Clock',
          content: `Signature feature: answers "When will this location become dangerous?"
          Status levels: SAFE → WATCH (5cm) → WARNING (20cm) → CRITICAL (45cm).
          Time-to-critical derived from depth trajectory across prediction horizons.
          All thresholds based on Indian urban flood depth guidelines.`
        },
        {
          title: 'Risk Scoring',
          content: `Transparent weighted scoring: flood probability (35%) + drainage utilization (25%) + depth (20%) + rainfall intensity (12%) + terrain susceptibility (8%).
          Risk levels: LOW (<0.30), MODERATE (0.30–0.55), HIGH (0.55–0.80), CRITICAL (≥0.80).
          All weights and thresholds are documented and not hidden.`
        },
        {
          title: 'Data Integrity',
          content: `FLOOD-X never fabricates real-world data. All synthetic data is explicitly labelled SYNTHETIC_PROTOTYPE.
          Provider abstraction ensures real IMD, CMWSSB, and terrain data can be plugged in without changing service logic.
          Every prediction exposes its data source, model method, timestamp, and confidence.`
        },
      ].map(({ title, content }) => (
        <div key={title} className="card">
          <h2 className="text-sm font-semibold text-white mb-2">{title}</h2>
          <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-line">{content}</p>
        </div>
      ))}

      <div className="card bg-amber-500/5 border-amber-500/20">
        <h2 className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-2"><Info size={14} />Limitations</h2>
        <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
          <li>No real-time IMD rainfall feed — simulation provider used</li>
          <li>Drainage network is synthetic — not real CMWSSB infrastructure data</li>
          <li>ML model trained on synthetic data — real-event validation pending</li>
          <li>Not a full hydrodynamic solver — SWMM integration planned for production</li>
          <li>Terrain processing limited to synthetic prototype in this demo</li>
          <li>All recommendations are decision-support only — not official government alerts</li>
        </ul>
      </div>
    </div>
  )
}
