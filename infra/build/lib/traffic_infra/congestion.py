from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from .constants import SLOTS_PER_SEGMENT
from .geometry import DirectedEdge, Intersection
from .state import CarState


def _intersection_for_slot(edge: DirectedEdge, slot: int) -> Intersection:
    """Assign a stopped car on a segment to the nearer intersection (PDF congestion per intersection)."""
    mid = SLOTS_PER_SEGMENT // 2
    return edge.frm if slot < mid else edge.to


def stopped_cars_per_intersection(
    prev_cars: Mapping[str, CarState],
    next_cars: Mapping[str, CarState],
) -> dict[Intersection, int]:
    """
    Count cars that did not move between steps, attributed to the nearest intersection on their edge.

    Matches PDF: "stopping" means no move from previous time step to current time step.
    v-group uses these counts as congestion information.
    """
    counts: dict[Intersection, int] = defaultdict(int)
    for car_id, prev in prev_cars.items():
        nxt = next_cars.get(car_id)
        if nxt is None:
            continue
        if prev.edge == nxt.edge and prev.slot == nxt.slot:
            inter = _intersection_for_slot(prev.edge, prev.slot)
            counts[inter] += 1
    return dict(counts)
