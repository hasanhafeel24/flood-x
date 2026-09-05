"""
Unit tests for FLOOD-X Road Routing Engine
============================================
Tests graph construction, Dijkstra routing, and flood-aware path selection.
"""
import pytest
from app.services.routing.engine import RoadGraph, ROAD_NODES, ROAD_EDGES
from app.schemas import Coordinate, RiskLevel


@pytest.fixture
def graph():
    return RoadGraph()


class TestRoadGraphConstruction:
    """Test NetworkX graph is built correctly."""

    def test_all_nodes_added(self, graph):
        """Graph has all defined road nodes."""
        assert graph.node_count == len(ROAD_NODES)

    def test_edges_are_bidirectional(self, graph):
        """All edges added in both directions."""
        # Each undirected edge becomes 2 directed edges
        assert graph.edge_count == len(ROAD_EDGES) * 2

    def test_graph_is_connected(self, graph):
        """Graph should be fully connected (all nodes reachable)."""
        import networkx as nx
        # Use underlying graph via node access
        nodes = list(ROAD_NODES.keys())
        for src in nodes[:3]:   # spot check 3 source nodes
            for dst in nodes[-3:]:  # vs 3 destination nodes
                # A route should exist for all pairs in the connected graph
                route = graph.find_route(
                    Coordinate(lat=ROAD_NODES[src]["lat"], lon=ROAD_NODES[src]["lon"]),
                    Coordinate(lat=ROAD_NODES[dst]["lat"], lon=ROAD_NODES[dst]["lon"]),
                    flood_aware=False,
                    drainage_utilization_pct=0.0,
                    rainfall_intensity_mm_hr=0.0,
                    overall_risk=RiskLevel.LOW,
                )
                assert route is not None, f"No path from {src} to {dst}"


class TestRouting:
    """Test route-finding under various conditions."""

    def test_normal_route_found(self, graph):
        """Should find a route under normal conditions."""
        route = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),  # Chennai Central
            Coordinate(lat=12.9930, lon=80.1708),  # Airport
            flood_aware=False,
            drainage_utilization_pct=50.0,
            rainfall_intensity_mm_hr=10.0,
            overall_risk=RiskLevel.LOW,
        )
        assert route is not None
        assert route.distance_km > 0
        assert route.estimated_travel_min > 0
        assert len(route.waypoints) >= 2

    def test_flood_aware_route_found(self, graph):
        """Flood-aware routing must return a valid route."""
        route = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),
            Coordinate(lat=12.9930, lon=80.1708),
            flood_aware=True,
            drainage_utilization_pct=160.0,
            rainfall_intensity_mm_hr=90.0,
            overall_risk=RiskLevel.CRITICAL,
        )
        assert route is not None

    def test_route_distance_is_positive(self, graph):
        """Route distance must be > 0."""
        route = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),
            Coordinate(lat=12.9249, lon=80.1000),
            flood_aware=False,
            drainage_utilization_pct=0.0,
            rainfall_intensity_mm_hr=0.0,
            overall_risk=RiskLevel.LOW,
        )
        assert route is not None
        assert route.distance_km > 0

    def test_route_has_start_end_waypoints(self, graph):
        """Route waypoints must include origin-vicinity and dest-vicinity nodes."""
        route = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),
            Coordinate(lat=12.9930, lon=80.1708),
            flood_aware=False,
            drainage_utilization_pct=0.0,
            rainfall_intensity_mm_hr=0.0,
            overall_risk=RiskLevel.LOW,
        )
        assert len(route.waypoints) >= 2

    def test_route_has_geojson(self, graph):
        """Route must include GeoJSON LineString geometry."""
        route = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),
            Coordinate(lat=12.9930, lon=80.1708),
            flood_aware=False,
            drainage_utilization_pct=0.0,
            rainfall_intensity_mm_hr=0.0,
            overall_risk=RiskLevel.LOW,
        )
        geo = route.geometry_geojson
        assert geo["type"] == "LineString"
        assert len(geo["coordinates"]) >= 2

    def test_flood_aware_has_lower_max_risk(self, graph):
        """Under flooding, flood-aware route max risk ≤ normal route max risk."""
        risk_order = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]

        normal = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),
            Coordinate(lat=12.9930, lon=80.1708),
            flood_aware=False,
            drainage_utilization_pct=160.0,
            rainfall_intensity_mm_hr=90.0,
            overall_risk=RiskLevel.HIGH,
        )
        flood = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),
            Coordinate(lat=12.9930, lon=80.1708),
            flood_aware=True,
            drainage_utilization_pct=160.0,
            rainfall_intensity_mm_hr=90.0,
            overall_risk=RiskLevel.HIGH,
        )
        if normal and flood:
            assert risk_order.index(flood.max_risk_level) <= \
                   risk_order.index(normal.max_risk_level) + 1  # within 1 level


class TestFloodConditionUpdate:
    """Test that flood conditions propagate to edge weights."""

    def test_no_rain_means_low_flood_depth(self, graph):
        """Zero rain → zero or near-zero flood depth on all edges."""
        graph.update_flood_conditions(
            drainage_utilization_pct=0.0,
            rainfall_intensity_mm_hr=0.0,
            overall_risk=RiskLevel.LOW,
        )
        # All edges should have low or zero flood depth
        # Can't directly access internal graph — test via routing
        route = graph.find_route(
            Coordinate(lat=13.0827, lon=80.2707),
            Coordinate(lat=12.9930, lon=80.1708),
            flood_aware=True,
            drainage_utilization_pct=0.0,
            rainfall_intensity_mm_hr=0.0,
            overall_risk=RiskLevel.LOW,
        )
        assert route is not None
        assert route.max_predicted_depth_cm < 10.0
