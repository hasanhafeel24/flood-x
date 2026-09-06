# FLOOD-X — Drainage Network Specification

> Technical specification of the 30-node synthetic drainage prototype.  
> `DATA SOURCE: SYNTHETIC_PROTOTYPE` — not real CMWSSB infrastructure.

---

## Overview

| Attribute | Value |
|-----------|-------|
| Network type | Combined sewer / stormwater |
| Total nodes | 30 |
| Node types | 6 (INLET, PIPE, JUNCTION, OUTLET, PUMP, STORAGE) |
| Pilot area | Chennai Metropolitan Area (synthetic extents) |
| Hydraulic model | Rational Method inflow (no full pipe routing) |
| Capacity units | m³/s |

---

## Node Types

| Type | Count | Description |
|------|-------|-------------|
| `INLET` | 8 | Surface water entry points (grated inlets, kerb cuts) |
| `PIPE` | 6 | Conveyance conduits (simplified as nodes for prototype) |
| `JUNCTION` | 8 | Network confluence points |
| `OUTLET` | 4 | Discharge to water bodies (Adyar River, Buckingham Canal) |
| `PUMP` | 2 | Mechanical pump stations |
| `STORAGE` | 2 | Detention basins / retention ponds |

---

## Capacity Assumptions

Derived from published Chennai urban drainage studies and standard Indian urban drainage design standards (IS:4948, CPHEEO Manual):

| Area Type | Typical Pipe Capacity |
|-----------|----------------------|
| Trunk sewer | 5–15 m³/s |
| Primary collector | 1–5 m³/s |
| Secondary collector | 0.2–1 m³/s |
| Local inlet | 0.05–0.2 m³/s |

---

## Hydraulic Model

### Inflow Estimation

```
Q_inflow = (C × I × A) / 360    [Rational Method]

Where:
  C = runoff coefficient (0.65–0.90 for urban Chennai)
  I = rainfall intensity [mm/hr]
  A = contributing catchment area [ha]
```

### Utilization

```
utilization_pct = (Q_inflow / Q_capacity) × 100

Status thresholds:
  < 80%   → NORMAL
  80–100% → HIGH (approaching capacity)
  > 100%  → SURCHARGING (flooding risk)
```

### Surcharge Detection

A node is classified as surcharging when:
1. `utilization_pct > 100%`
2. OR `utilization_pct > 85%` AND a connected upstream node is also `> 85%`

Surcharging nodes are flagged as bottlenecks and highlighted on the drainage map.

---

## Node Network Topology

The 30 nodes are connected in a directed acyclic graph representing:
- Upstream inlets → local collectors → trunk sewers → outfalls
- Two pump stations serving low-lying areas
- Two detention basins for peak attenuation

Detailed node list, coordinates, and connectivity are defined in:
`backend/app/providers/synthetic_drainage.py`

---

## Real Data Upgrade

**CMWSSB SCADA Integration:**
```
Real replacement:
  - CMWSSB operates ~500 drainage monitoring points across Chennai
  - SCADA telemetry available at 15-minute intervals
  - Data access requires MoU with CMWSSB
  - API: http://scada.cmwssb.gov.in/api/v1/drainage/status

Full hydraulic simulation:
  - SWMM (Storm Water Management Model) integration
  - calibrate on Chennai 2015 event data
  - requires surveyed pipe dimensions and invert levels
```

---

## Simulation Scenarios Effect on Drainage

| Scenario | Peak Intensity | Expected Peak Utilization |
|----------|---------------|--------------------------|
| `normal_rainfall` | ~8 mm/hr | 20–35% |
| `heavy_rainfall` | ~35 mm/hr | 60–80% |
| `extreme_rainfall` | ~85 mm/hr | 90–130% |
| `drainage_blockage` | ~30 mm/hr | 120–180% (blocked nodes) |
| `pump_failure` | ~40 mm/hr | 110–160% (pump nodes offline) |
| `combined_extreme` | ~95 mm/hr | 150–200% |
