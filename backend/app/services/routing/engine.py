"""
FLOOD-X Road Graph Engine — Flood-Aware Routing
================================================
Implements a synthetic road network for Chennai pilot area using NetworkX.

DATA SOURCE: SYNTHETIC_PROTOTYPE — not real road data
ALGORITHM: Dijkstra shortest path with flood-risk edge weights

Road segments connect key Chennai landmarks and cover flood-prone corridors.
Edge weights are dynamically adjusted based on predicted flood depth/risk.

REAL DATA PATH: Replace edge list with OSM Chennai road network via
    osmnx.graph_from_place("Chennai, India", network_type="drive")
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import networkx as nx
import structlog

from app.schemas import (
    Coordinate,
    RiskLevel,
    RoutePoint,
    SafeRoute,
)

log = structlog.get_logger(__name__)

# ── Synthetic Road Node Registry ──────────────────────────────────────────────
# Key landmarks / intersections in Chennai
# SOURCE: SYNTHETIC_PROTOTYPE — approximate coordinates for demonstration

ROAD_NODES: Dict[str, Dict] = {
    # North
    "N_CENTRAL":  {"lat": 13.0827, "lon": 80.2707, "name": "Chennai Central"},
    "N_EGMORE":   {"lat": 13.0734, "lon": 80.2620, "name": "Egmore"},
    "N_ANNA_SQ":  {"lat": 13.0678, "lon": 80.2758, "name": "Anna Square"},
    "N_TNAGAR":   {"lat": 13.0418, "lon": 80.2341, "name": "T. Nagar"},
    "N_KODAMBAK": {"lat": 13.0524, "lon": 80.2399, "name": "Kodambakkam"},
    # Central-East (flood-prone)
    "C_VELACHERY": {"lat": 12.9815, "lon": 80.2209, "name": "Velachery"},
    "C_ADYAR":    {"lat": 13.0100, "lon": 80.2550, "name": "Adyar"},
    "C_MYLAPORE": {"lat": 13.0368, "lon": 80.2676, "name": "Mylapore"},
    "C_ROYAPETTAH":{"lat": 13.0524, "lon": 80.2638, "name": "Royapettah"},
    # West
    "W_ASHOK":    {"lat": 13.0317, "lon": 80.2101, "name": "Ashok Nagar"},
    "W_KKNAGAR":  {"lat": 13.0373, "lon": 80.1986, "name": "KK Nagar"},
    "W_PORUR":    {"lat": 13.0375, "lon": 80.1568, "name": "Porur"},
    "W_AMBATTUR": {"lat": 13.1147, "lon": 80.1596, "name": "Ambattur"},
    # South
    "S_CHROMEPET":{"lat": 12.9516, "lon": 80.1411, "name": "Chromepet"},
    "S_TAMBARAM": {"lat": 12.9249, "lon": 80.1000, "name": "Tambaram"},
    "S_PALLAVARAM":{"lat": 12.9675, "lon": 80.1494, "name": "Pallavaram"},
    "S_SHOLING":  {"lat": 12.9010, "lon": 80.2276, "name": "Sholinganallur"},
    "S_PERUNGUDI":{"lat": 12.9632, "lon": 80.2302, "name": "Perungudi"},
    # Airport
    "AIRPORT":    {"lat": 12.9930, "lon": 80.1708, "name": "Chennai Airport"},
    # Flood bypass nodes
    "ALT_NORTH":  {"lat": 13.0900, "lon": 80.2400, "name": "NH-16 Bypass North"},
    "ALT_WEST":   {"lat": 13.0600, "lon": 80.1900, "name": "Outer Ring Road West"},
    "ALT_SOUTH":  {"lat": 13.0300, "lon": 80.1700, "name": "Outer Ring Road South"},
}

# ── Road Edges ────────────────────────────────────────────────────────────────
# (node_a, node_b, base_speed_kmh, flood_susceptibility 0–1)
# flood_susceptibility: 1.0 = highly flood-prone road

ROAD_EDGES: List[Tuple[str, str, float, float]] = [
    # Main arterials (moderate flood risk)
    ("N_CENTRAL",   "N_EGMORE",    40, 0.3),
    ("N_EGMORE",    "N_ANNA_SQ",   35, 0.4),
    ("N_EGMORE",    "C_ROYAPETTAH",35, 0.5),
    ("C_ROYAPETTAH","C_MYLAPORE",  30, 0.6),
    ("C_MYLAPORE",  "C_ADYAR",     35, 0.7),  # Adyar river corridor — high risk
    ("C_ADYAR",     "C_VELACHERY", 30, 0.8),  # Very flood-prone
    ("C_VELACHERY", "S_PERUNGUDI", 35, 0.6),
    ("S_PERUNGUDI", "S_SHOLING",   45, 0.4),
    # T. Nagar corridor
    ("N_TNAGAR",    "N_KODAMBAK",  30, 0.5),
    ("N_CENTRAL",   "N_KODAMBAK",  35, 0.4),
    ("N_KODAMBAK",  "C_MYLAPORE",  30, 0.5),
    ("N_TNAGAR",    "W_ASHOK",     35, 0.3),
    # West corridor
    ("W_ASHOK",     "W_KKNAGAR",   40, 0.2),
    ("W_KKNAGAR",   "W_PORUR",     50, 0.2),
    ("W_PORUR",     "AIRPORT",     55, 0.2),
    ("W_PORUR",     "S_PALLAVARAM",50, 0.2),
    ("S_PALLAVARAM","AIRPORT",     45, 0.3),
    # South routes
    ("AIRPORT",     "S_CHROMEPET", 45, 0.2),
    ("S_CHROMEPET", "S_TAMBARAM",  50, 0.1),
    ("C_VELACHERY", "AIRPORT",     35, 0.5),  # Pallavaram-Velachery road — flood risk
    # North routes
    ("N_CENTRAL",   "W_AMBATTUR",  45, 0.3),
    ("W_AMBATTUR",  "W_PORUR",     50, 0.2),
    # Bypass / alternative routes (low flood risk — elevated or inland)
    ("N_CENTRAL",   "ALT_NORTH",   55, 0.1),
    ("ALT_NORTH",   "ALT_WEST",    55, 0.1),
    ("ALT_WEST",    "ALT_SOUTH",   55, 0.1),
    ("ALT_SOUTH",   "AIRPORT",     55, 0.1),
    ("ALT_SOUTH",   "S_PALLAVARAM",50, 0.1),
    ("ALT_NORTH",   "N_TNAGAR",    45, 0.2),
    ("ALT_WEST",    "W_KKNAGAR",   50, 0.2),
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in km."""
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@dataclass
class RoadGraph:
    """
    Synthetic road graph for Chennai pilot.
    Supports flood-aware Dijkstra routing.
    """
    _graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    def __post_init__(self) -> None:
        self._build()

    def _build(self) -> None:
        """Build the NetworkX directed graph from node/edge definitions."""
        # Add nodes with position attributes
        for node_id, data in ROAD_NODES.items():
            self._graph.add_node(
                node_id,
                lat=data["lat"],
                lon=data["lon"],
                name=data["name"],
            )

        # Add bidirectional edges with computed travel time and flood risk
        for src, dst, speed_kmh, flood_susceptibility in ROAD_EDGES:
            src_d = ROAD_NODES[src]
            dst_d = ROAD_NODES[dst]
            dist_km = _haversine_km(src_d["lat"], src_d["lon"], dst_d["lat"], dst_d["lon"])
            travel_min = (dist_km / speed_kmh) * 60.0

            attrs = {
                "distance_km": dist_km,
                "speed_kmh": speed_kmh,
                "travel_min": travel_min,
                "flood_susceptibility": flood_susceptibility,
                "current_flood_depth_cm": 0.0,
                "flood_risk": RiskLevel.LOW,
                "passable": True,
            }
            self._graph.add_edge(src, dst, **attrs)
            self._graph.add_edge(dst, src, **attrs)  # bidirectional

        log.info(
            "road_graph_built",
            nodes=self._graph.number_of_nodes(),
            edges=self._graph.number_of_edges(),
        )

    def update_flood_conditions(
        self,
        drainage_utilization_pct: float,
        rainfall_intensity_mm_hr: float,
        overall_risk: RiskLevel,
    ) -> None:
        """Update edge flood depths and risk based on current hydraulic state."""
        for src, dst, data in self._graph.edges(data=True):
            susc = data["flood_susceptibility"]

            # Estimate depth: proportional to drainage overload × susceptibility
            overload_factor = max(0.0, drainage_utilization_pct - 80.0) / 120.0
            rain_factor = max(0.0, rainfall_intensity_mm_hr - 20.0) / 100.0
            depth_cm = (overload_factor * 0.6 + rain_factor * 0.4) * susc * 60.0

            # Risk level from depth + susceptibility
            if depth_cm < 5:
                risk = RiskLevel.LOW
            elif depth_cm < 20:
                risk = RiskLevel.MODERATE
            elif depth_cm < 45:
                risk = RiskLevel.HIGH
            else:
                risk = RiskLevel.CRITICAL

            passable = depth_cm < 50.0  # 50cm = impassable

            self._graph[src][dst]["current_flood_depth_cm"] = round(depth_cm, 1)
            self._graph[src][dst]["flood_risk"] = risk
            self._graph[src][dst]["passable"] = passable

    def _nearest_node(self, lat: float, lon: float) -> str:
        """Return the closest graph node to a coordinate."""
        best_node = None
        best_dist = float("inf")
        for node_id, data in self._graph.nodes(data=True):
            d = _haversine_km(lat, lon, data["lat"], data["lon"])
            if d < best_dist:
                best_dist = d
                best_node = node_id
        return best_node

    def _edge_weight_flood_aware(self, u: str, v: str, data: dict) -> float:
        """Weight function for Dijkstra: penalise flooded edges heavily."""
        base = data.get("travel_min", 5.0)
        if not data.get("passable", True):
            return float("inf")  # impassable
        depth = data.get("current_flood_depth_cm", 0.0)
        risk = data.get("flood_risk", RiskLevel.LOW)

        # Risk multipliers
        multipliers = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MODERATE: 2.0,
            RiskLevel.HIGH: 5.0,
            RiskLevel.CRITICAL: 20.0,
        }
        return base * multipliers.get(risk, 1.0) + depth * 0.1

    def _edge_weight_normal(self, u: str, v: str, data: dict) -> float:
        return data.get("travel_min", 5.0)

    def find_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        flood_aware: bool = True,
        drainage_utilization_pct: float = 0.0,
        rainfall_intensity_mm_hr: float = 0.0,
        overall_risk: RiskLevel = RiskLevel.LOW,
    ) -> Optional[SafeRoute]:
        """
        Find shortest (or flood-aware) route between two coordinates.

        Returns SafeRoute with waypoints, distance, travel time, risk metrics.
        """
        # Update flood conditions
        self.update_flood_conditions(
            drainage_utilization_pct, rainfall_intensity_mm_hr, overall_risk
        )

        # Find nearest graph nodes
        orig_node = self._nearest_node(origin.lat, origin.lon)
        dest_node = self._nearest_node(destination.lat, destination.lon)

        if orig_node == dest_node:
            log.warning("routing_same_node", orig=orig_node)

        weight_fn = self._edge_weight_flood_aware if flood_aware else self._edge_weight_normal

        try:
            path_nodes = nx.dijkstra_path(
                self._graph, orig_node, dest_node,
                weight=weight_fn,
            )
        except nx.NetworkXNoPath:
            log.warning("routing_no_path", orig=orig_node, dest=dest_node)
            # Fallback: try without flood penalties
            try:
                path_nodes = nx.dijkstra_path(
                    self._graph, orig_node, dest_node,
                    weight=self._edge_weight_normal,
                )
            except nx.NetworkXNoPath:
                return None

        # Compute route metrics
        total_dist = 0.0
        total_time = 0.0
        max_depth = 0.0
        max_risk = RiskLevel.LOW
        flood_zones_avoided = 0
        waypoints: List[RoutePoint] = []

        risk_order = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]

        for i, node_id in enumerate(path_nodes):
            n = self._graph.nodes[node_id]
            waypoints.append(RoutePoint(lat=n["lat"], lon=n["lon"]))

            if i < len(path_nodes) - 1:
                edge = self._graph[node_id][path_nodes[i + 1]]
                total_dist += edge.get("distance_km", 0.0)
                total_time += edge.get("travel_min", 0.0)
                depth = edge.get("current_flood_depth_cm", 0.0)
                risk = edge.get("flood_risk", RiskLevel.LOW)
                max_depth = max(max_depth, depth)
                if risk_order.index(risk) > risk_order.index(max_risk):
                    max_risk = risk

        # Count avoided flood zones (vs direct route)
        if flood_aware:
            try:
                direct = nx.dijkstra_path(
                    self._graph, orig_node, dest_node,
                    weight=self._edge_weight_normal,
                )
                for i in range(len(direct) - 1):
                    edge = self._graph[direct[i]][direct[i+1]]
                    if edge.get("flood_risk") in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                        flood_zones_avoided += 1
            except Exception:
                pass

        from datetime import datetime, timezone
        return SafeRoute(
            route_id=str(uuid.uuid4())[:8],
            origin=origin,
            destination=destination,
            is_flood_aware=flood_aware,
            distance_km=round(total_dist, 2),
            estimated_travel_min=round(total_time, 1),
            max_predicted_depth_cm=round(max_depth, 1),
            max_risk_level=max_risk,
            flood_zones_avoided=flood_zones_avoided,
            waypoints=waypoints,
            geometry_geojson={
                "type": "LineString",
                "coordinates": [[wp.lon, wp.lat] for wp in waypoints],
            },
            note="SYNTHETIC_PROTOTYPE road network — Dijkstra with flood-risk weights",
            timestamp=datetime.now(timezone.utc),
        )

    @property
    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()


# Module singleton
road_graph = RoadGraph()
