"""
Square / corner layout from the ECEN723 traffic diagram (course handout).

Grid indices follow the project geometry used everywhere else in the repo:
(0,0) = bottom-left intersection, (2,2) = top-right; +x right, +y up.

- **A**: start **square** immediately west of the top-left corner intersection (0,2).
- **B, C, D**: labels on the bottom-left (0,0), bottom-right (2,0),
  and top-right (2,2) corner intersections respectively.

Vehicles depart from A, visit B, C, D in some order, return to A.
"""

from __future__ import annotations

from dataclasses import dataclass

from .geometry import DirectedEdge, Intersection, is_neighbor
from .state import CarState


# Intersection each marker belongs to (matches standard course figure).
DEPOT_ADJACENT_INTERSECTION: dict[str, Intersection] = {
    "A": (0, 2),
    "B": (0, 0),
    "C": (2, 0),
    "D": (2, 2),
}


@dataclass(frozen=True)
class DepotSpec:
    label: str
    role: str
    adjacent: Intersection
    kind: str  # "start_square" | "corner_label"
    outward: str | None = None  # N|E|S|W from adjacent intersection toward square (A only)
    box: float = 0.34


def _specs() -> list[DepotSpec]:
    return [
        DepotSpec("A", "start", DEPOT_ADJACENT_INTERSECTION["A"], "start_square", "W"),
        DepotSpec("B", "destination", DEPOT_ADJACENT_INTERSECTION["B"], "corner_label"),
        DepotSpec("C", "destination", DEPOT_ADJACENT_INTERSECTION["C"], "corner_label"),
        DepotSpec("D", "destination", DEPOT_ADJACENT_INTERSECTION["D"], "corner_label"),
    ]


def depot_specs() -> tuple[DepotSpec, ...]:
    return tuple(_specs())


def depots_to_json() -> list[dict]:
    out: list[dict] = []
    for d in _specs():
        item: dict = {
            "label": d.label,
            "role": d.role,
            "adj": [d.adjacent[0], d.adjacent[1]],
            "kind": d.kind,
        }
        if d.kind == "start_square":
            item["outward"] = d.outward
            item["box"] = d.box
        out.append(item)
    return out


def first_road_edge_leaving_start() -> DirectedEdge:
    """First interior segment from A's intersection toward B."""
    a = DEPOT_ADJACENT_INTERSECTION["A"]
    b = DEPOT_ADJACENT_INTERSECTION["B"]
    if a[0] == b[0]:
        step_y = 1 if b[1] > a[1] else -1
        nxt = (a[0], a[1] + step_y)
    elif a[1] == b[1]:
        step_x = 1 if b[0] > a[0] else -1
        nxt = (a[0] + step_x, a[1])
    else:
        raise RuntimeError("A and B must share a row or column on the grid")

    edge = DirectedEdge(frm=a, to=nxt)
    if not is_neighbor(a, nxt):
        raise RuntimeError("invalid first segment from A")
    return edge


def initial_car_from_depot_a(car_id: str = "car1") -> CarState:
    edge = first_road_edge_leaving_start()
    return CarState(
        car_id=car_id,
        edge=edge,
        slot=0,
        driving_dir=edge.dir(),
    )


def assert_valid_start_state(cs: CarState) -> None:
    edge = cs.edge
    if cs.slot != 0:
        raise ValueError("start car must use slot 0 on the departing segment")
    if edge.frm != DEPOT_ADJACENT_INTERSECTION["A"]:
        raise ValueError("start segment must leave from intersection adjacent to depot A")
    if not edge.slot_at_frm_end(cs.slot):
        raise ValueError("slot 0 must be at the frm end of the directed edge")
    if cs.driving_dir != edge.dir():
        raise ValueError("driving_dir must match travel direction of the edge")
    if not is_neighbor(edge.frm, edge.to):
        raise ValueError("edge must connect neighboring intersections")
