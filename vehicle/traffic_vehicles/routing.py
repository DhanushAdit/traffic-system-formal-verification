"""Tour planning: A→B/C/D permutations, path computation, dynamic rerouting."""

from __future__ import annotations

import heapq
from collections import deque
from itertools import permutations

from traffic_infra.geometry import Dir, DirectedEdge, Intersection

from .constants import PERIMETER_TOUR_ORDER, SLOTS_PER_SEGMENT, TERMINALS
from .network import get_directed_edge, get_neighbors


def all_tour_permutations() -> list[list[str]]:
    """All 6 orderings of [B, C, D]."""
    return [list(p) for p in permutations(["B", "C", "D"])]


def get_full_path(order: list[str]) -> list[DirectedEdge]:
    """Complete right-turn-free, U-turn-free edge sequence for entire tour A→...→A.

    Uses a single multi-waypoint BFS with state (intersection, last_dir, next_wp_index)
    so that the search never paints itself into a corner at a terminal junction.
    """
    _OPPOSITE: dict[Dir, Dir] = {
        Dir.N: Dir.S, Dir.S: Dir.N, Dir.E: Dir.W, Dir.W: Dir.E,
    }
    _RIGHT: dict[Dir, Dir] = {
        Dir.N: Dir.E, Dir.E: Dir.S, Dir.S: Dir.W, Dir.W: Dir.N,
    }
    waypoints: list[Intersection] = (
        [TERMINALS["A"]] + [TERMINALS[t] for t in order] + [TERMINALS["A"]]
    )
    # State: (current_intersection, last_travel_dir, next_waypoint_index)
    start = waypoints[0]
    init_state = (start, None, 1)
    visited: set[tuple[Intersection, Dir | None, int]] = {init_state}
    queue: deque[tuple[Intersection, Dir | None, int, list[DirectedEdge]]] = deque(
        [(start, None, 1, [])]
    )
    while queue:
        node, last_dir, wp_idx, path = queue.popleft()
        for nb in get_neighbors(node):
            edge = get_directed_edge(node, nb)
            new_dir = edge.dir()
            if last_dir is not None:
                if new_dir == _OPPOSITE[last_dir]:
                    continue  # no U-turn
                if new_dir == _RIGHT[last_dir]:
                    continue  # no right turn (project spec)
            new_wp_idx = wp_idx
            if nb == waypoints[wp_idx]:
                new_wp_idx = wp_idx + 1
                if new_wp_idx == len(waypoints):
                    return path + [edge]
            state = (nb, new_dir, new_wp_idx)
            if state not in visited:
                visited.add(state)
                queue.append((nb, new_dir, new_wp_idx, path + [edge]))
    raise ValueError(f"No valid right-turn-free, U-turn-free tour path for order {order}")


def compute_tour_length(order: list[str]) -> int:
    """Total slots for A → order[0] → order[1] → order[2] → A."""
    return len(get_full_path(order)) * SLOTS_PER_SEGMENT


def best_tour_order(
    occupied_edges: set[DirectedEdge] | None = None,
    congestion_map: dict[Intersection, int] | None = None,
) -> list[str]:
    occupied_edges = occupied_edges or set()
    congestion_map = congestion_map or {}

    best_order = list(PERIMETER_TOUR_ORDER)
    best_score = float("inf")
    for order in all_tour_permutations():
        path = get_full_path(order)
        score = len(path) * SLOTS_PER_SEGMENT
        if path[0] in occupied_edges:
            score += SLOTS_PER_SEGMENT * 100
        for edge in path:
            if edge in occupied_edges:
                score += SLOTS_PER_SEGMENT * 3
            score += congestion_map.get(edge.to, 0) * 5
        if score < best_score:
            best_score = score
            best_order = list(order)
    return best_order


def dynamic_reroute(
    current_intersection: Intersection,
    remaining_destinations: list[str],
    congestion_map: dict[Intersection, int],
) -> list[DirectedEdge]:
    """
    Dijkstra from current_intersection to each remaining destination in order,
    weighting congested intersections as having additional travel cost.
    """
    if not remaining_destinations:
        return []

    waypoints = [TERMINALS[d] for d in remaining_destinations]
    result: list[DirectedEdge] = []
    current = current_intersection
    for wp in waypoints:
        path = _dijkstra(current, wp, congestion_map)
        result.extend(path)
        current = wp
    return result


def _dijkstra(
    start: Intersection,
    end: Intersection,
    congestion_map: dict[Intersection, int],
) -> list[DirectedEdge]:
    """Dijkstra weighting: 1 edge = SLOTS_PER_SEGMENT + congestion penalty."""
    CONGESTION_WEIGHT = 10
    dist: dict[Intersection, float] = {start: 0.0}
    prev_edge: dict[Intersection, DirectedEdge | None] = {start: None}
    heap: list[tuple[float, Intersection]] = [(0.0, start)]

    while heap:
        cost, node = heapq.heappop(heap)
        if node == end:
            break
        if cost > dist.get(node, float("inf")):
            continue
        for nb in get_neighbors(node):
            edge_cost = SLOTS_PER_SEGMENT + congestion_map.get(nb, 0) * CONGESTION_WEIGHT
            new_cost = cost + edge_cost
            if new_cost < dist.get(nb, float("inf")):
                dist[nb] = new_cost
                prev_edge[nb] = get_directed_edge(node, nb)
                heapq.heappush(heap, (new_cost, nb))

    # Reconstruct path
    path: list[DirectedEdge] = []
    node = end
    while prev_edge.get(node) is not None:
        e = prev_edge[node]
        path.append(e)
        node = e.frm
    path.reverse()
    return path
