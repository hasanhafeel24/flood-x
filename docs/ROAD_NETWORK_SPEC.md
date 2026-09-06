# FLOOD-X — Road Network Specification

> Technical specification of the synthetic road network used for flood-aware routing.  
> `DATA SOURCE: SYNTHETIC_PROTOTYPE` — 22-node simplified graph.

---

## Overview

| Attribute | Value |
|-----------|-------|
| Graph type | Directed weighted |
| Library | NetworkX 3.x |
| Algorithm | Dijkstra shortest path (flood-weight variant) |
| Nodes | 22 (representative Chennai locations) |
| Edges | 58 directed connections |
| Coordinate system | WGS84 (lat/lon) |
| Edge weight | travel_time_min × flood_penalty |

---

## Graph Structure

### Nodes

Each node represents a key road junction or landmark in the Chennai pilot area:

| Range | Area | Count |
|-------|------|-------|
| N01–N06 | South Chennai (Velachery, Adyar, Kotturpuram) | 6 |
| N07–N12 | Central Chennai (T. Nagar, Nungambakkam, Egmore) | 6 |
| N13–N18 | West Chennai (Porur, Tambaram, Chromepet) | 6 |
| N19–N22 | North Chennai (Ambattur, Perambur) | 4 |

### Edges

Each directed edge carries:
- `base_weight` — travel time in minutes under normal conditions
- `distance_km` — road segment length
- `road_type` — arterial / collector / local
- `flood_susceptibility` — pre-computed [0.0–1.0] from terrain slope

---

## Flood-Aware Routing Algorithm

### Edge Weight Computation

```python
def flood_weight(base_weight, risk_level, depth_cm):
    """
    Compute flood-penalised edge weight for Dijkstra.
    
    Risk multipliers (tuned for Chennai urban conditions):
      LOW      → 1.0   (no penalty)
      MODERATE → 1.5   (15–20cm water)
      HIGH     → 3.0   (20–45cm water)
      CRITICAL → 10.0  (>45cm — near-impassable)
    
    Depth surcharge: +0.1× per cm above 10cm threshold
    """
    RISK_MULTIPLIERS = {
        "LOW": 1.0, "MODERATE": 1.5, "HIGH": 3.0, "CRITICAL": 10.0
    }
    multiplier = RISK_MULTIPLIERS.get(risk_level, 1.0)
    depth_surcharge = max(0, (depth_cm - 10) * 0.1)
    return base_weight * (multiplier + depth_surcharge)
```

### Route Comparison

Two routes are always returned:
1. **Flood-aware route:** Dijkstra with dynamic flood weights applied
2. **Normal route:** Dijkstra with base weights only (no flood penalties)

The frontend renders both routes on the FloodMap layer for comparison.

---

## Depth Thresholds for Road Safety

Based on Indian road safety guidelines and NDRF operational standards:

| Depth | Road Status | Action |
|-------|-------------|--------|
| 0–5 cm | Passable | Normal routing |
| 5–15 cm | Caution | Slow down, avoid if alternate available |
| 15–30 cm | Restricted | Avoid (risk to low-clearance vehicles) |
| 30–45 cm | High Risk | Emergency vehicles only |
| > 45 cm | Impassable | Road closed, removed from graph |

---

## Real Data Upgrade Path

### OSM Full Network

```python
import osmnx as ox

# Download complete Chennai road network
G = ox.graph_from_place(
    "Chennai, India",
    network_type="drive",
    simplify=True,
    retain_all=False,
)

print(f"Nodes: {G.number_of_nodes():,}")   # ~50,000
print(f"Edges: {G.number_of_edges():,}")   # ~120,000

# Project to UTM for distance calculations
G_proj = ox.project_graph(G)

# Add flood susceptibility from DEM
# (spatial join with SRTM elevation data)
for u, v, data in G.edges(data=True):
    elev = sample_dem(data["geometry"])  # sample DEM along edge
    data["flood_susceptibility"] = compute_susceptibility(elev)

# Save
ox.save_graphml(G, "data/chennai_road_network.graphml")
```

**Approximate scale:** 50,000 nodes, 120,000 edges  
**Routing time at full scale:** ~100–500ms per query (acceptable for 5-sec WS tick)  
**Recommended:** Run NetworkX on projected UTM graph, not lat/lon (Haversine is slow at scale)

### Real-Time Traffic Integration

Future enhancement: weight edges by real-time traffic from Google Maps Platform or HERE APIs, combined with flood penalties for compound road risk scoring.
