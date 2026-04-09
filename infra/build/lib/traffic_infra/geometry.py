from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .constants import SLOTS_PER_SEGMENT


class Dir(str, Enum):
    N = "N"
    E = "E"
    S = "S"
    W = "W"


Intersection = tuple[int, int]


def opposite_dir(d: Dir) -> Dir:
    return {Dir.N: Dir.S, Dir.S: Dir.N, Dir.E: Dir.W, Dir.W: Dir.E}[d]


def travel_dir(frm: Intersection, to: Intersection) -> Dir:
    fx, fy = frm
    tx, ty = to
    if fx == tx and ty == fy + 1:
        return Dir.N
    if fx == tx and ty == fy - 1:
        return Dir.S
    if fy == ty and tx == fx + 1:
        return Dir.E
    if fy == ty and tx == fx - 1:
        return Dir.W
    raise ValueError(f"Intersections are not neighbors: {frm} -> {to}")


@dataclass(frozen=True)
class DirectedEdge:
    frm: Intersection
    to: Intersection

    def dir(self) -> Dir:
        return travel_dir(self.frm, self.to)

    def is_valid_slot(self, slot: int) -> bool:
        return 0 <= slot < SLOTS_PER_SEGMENT

    def slot_at_frm_end(self, slot: int) -> bool:
        return slot == 0

    def slot_at_to_end(self, slot: int) -> bool:
        return slot == SLOTS_PER_SEGMENT - 1

    def approach_dir_at_to_intersection(self) -> Dir:
        return opposite_dir(self.dir())


def grid_intersections() -> list[Intersection]:
    return [(x, y) for x in range(3) for y in range(3)]


def directed_edges() -> list[DirectedEdge]:
    edges: list[DirectedEdge] = []
    for x in range(3):
        for y in range(3):
            if x + 1 < 3:
                edges.append(DirectedEdge((x, y), (x + 1, y)))
            if x - 1 >= 0:
                edges.append(DirectedEdge((x, y), (x - 1, y)))
            if y + 1 < 3:
                edges.append(DirectedEdge((x, y), (x, y + 1)))
            if y - 1 >= 0:
                edges.append(DirectedEdge((x, y), (x, y - 1)))
    return sorted(edges, key=lambda e: (e.frm, e.to))


def is_neighbor(frm: Intersection, to: Intersection) -> bool:
    fx, fy = frm
    tx, ty = to
    return (abs(fx - tx) + abs(fy - ty)) == 1
