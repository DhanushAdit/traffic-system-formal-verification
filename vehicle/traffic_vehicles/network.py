"""Road network graph for the 3x3 grid plus terminal nodes A-D."""

from __future__ import annotations

from collections import deque

from traffic_infra.geometry import Dir, DirectedEdge, Intersection, directed_edges, grid_intersections

# Terminal label → adjacent intersection
TERMINAL_ADJACENCY: dict[str, Intersection] = {
    "A": (0, 2),
    "B": (0, 0),
    "C": (2, 0),
    "D": (2, 2),
}

# Pre-build the grid edge set
_GRID_EDGES: list[DirectedEdge] = directed_edges()
_EDGE_MAP: dict[tuple[Intersection, Intersection], DirectedEdge] = {
    (e.frm, e.to): e for e in _GRID_EDGES
}

# Adjacency list: intersection → list of reachable intersections
_NEIGHBORS: dict[Intersection, list[Intersection]] = {}
for _e in _GRID_EDGES:
    _NEIGHBORS.setdefault(_e.frm, []).append(_e.to)


def get_neighbors(intersection: Intersection) -> list[Intersection]:
    return _NEIGHBORS.get(intersection, [])


def get_directed_edge(frm: Intersection, to: Intersection) -> DirectedEdge:
    key = (frm, to)
    if key not in _EDGE_MAP:
        raise KeyError(f"No edge {frm} → {to}")
    return _EDGE_MAP[key]


def get_all_edges() -> list[DirectedEdge]:
    return list(_GRID_EDGES)


def bfs_shortest_path(
    start: Intersection, end: Intersection
) -> list[DirectedEdge]:
    """BFS over grid intersections; returns list of DirectedEdges."""
    if start == end:
        return []
    visited: set[Intersection] = {start}
    queue: deque[tuple[Intersection, list[DirectedEdge]]] = deque([(start, [])])
    while queue:
        node, path = queue.popleft()
        for nb in get_neighbors(node):
            edge = get_directed_edge(node, nb)
            new_path = path + [edge]
            if nb == end:
                return new_path
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, new_path))
    raise ValueError(f"No path from {start} to {end}")


def bfs_no_uturn(
    start: Intersection,
    end: Intersection,
    incoming_dir: Dir | None = None,
) -> list[DirectedEdge]:
    """BFS that never makes a U-turn or a right turn (project spec prohibits both).

    *incoming_dir* is the direction of travel used to ARRIVE at *start*.
    State = (node, last_travel_dir) prevents revisiting the same node from
    the same approach direction.
    """
    if start == end:
        return []
    _OPPOSITE: dict[Dir, Dir] = {
        Dir.N: Dir.S, Dir.S: Dir.N, Dir.E: Dir.W, Dir.W: Dir.E
    }
    _RIGHT: dict[Dir, Dir] = {
        Dir.N: Dir.E, Dir.E: Dir.S, Dir.S: Dir.W, Dir.W: Dir.N
    }
    visited: set[tuple[Intersection, Dir | None]] = {(start, incoming_dir)}
    queue: deque[tuple[Intersection, Dir | None, list[DirectedEdge]]] = deque(
        [(start, incoming_dir, [])]
    )
    while queue:
        node, last_dir, path = queue.popleft()
        for nb in get_neighbors(node):
            edge = get_directed_edge(node, nb)
            new_dir = edge.dir()
            if last_dir is not None:
                if new_dir == _OPPOSITE[last_dir]:
                    continue  # skip U-turn
                if new_dir == _RIGHT[last_dir]:
                    continue  # skip right turn (project spec: cannot make right turn)
            new_path = path + [edge]
            if nb == end:
                return new_path
            state = (nb, new_dir)
            if state not in visited:
                visited.add(state)
                queue.append((nb, new_dir, new_path))
    raise ValueError(f"No right-turn-free, U-turn-free path from {start} to {end}")


_TURN_TABLE: dict[tuple[Dir, Dir], str] = {
    (Dir.N, Dir.N): "straight",
    (Dir.E, Dir.E): "straight",
    (Dir.S, Dir.S): "straight",
    (Dir.W, Dir.W): "straight",
    (Dir.N, Dir.E): "right",
    (Dir.E, Dir.S): "right",
    (Dir.S, Dir.W): "right",
    (Dir.W, Dir.N): "right",
    (Dir.N, Dir.W): "left",
    (Dir.W, Dir.S): "left",
    (Dir.S, Dir.E): "left",
    (Dir.E, Dir.N): "left",
    (Dir.N, Dir.S): "uturn",
    (Dir.S, Dir.N): "uturn",
    (Dir.E, Dir.W): "uturn",
    (Dir.W, Dir.E): "uturn",
}


def get_turn_type(current_dir: Dir, next_dir: Dir) -> str:
    return _TURN_TABLE[(current_dir, next_dir)]


def get_valid_next_edges(current_edge: DirectedEdge) -> list[DirectedEdge]:
    """All edges continuing from current_edge.to, excluding U-turns and right turns."""
    current_dir = current_edge.dir()
    _RIGHT: dict[Dir, Dir] = {
        Dir.N: Dir.E, Dir.E: Dir.S, Dir.S: Dir.W, Dir.W: Dir.N
    }
    result: list[DirectedEdge] = []
    for nb in get_neighbors(current_edge.to):
        if nb == current_edge.frm:
            continue  # U-turn
        edge = get_directed_edge(current_edge.to, nb)
        if edge.dir() == _RIGHT[current_dir]:
            continue  # right turn (project spec: cannot make right turn)
        result.append(edge)
    return result


def get_approach_dir(edge: DirectedEdge) -> Dir:
    """Direction from which a car on this edge approaches the to-intersection."""
    return edge.approach_dir_at_to_intersection()
