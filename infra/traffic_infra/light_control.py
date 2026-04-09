from __future__ import annotations

from dataclasses import dataclass

from .geometry import Dir, Intersection
from .state import TrafficSignals


DIR_CYCLE: list[Dir] = [Dir.N, Dir.E, Dir.S, Dir.W]


def cycle_green(step_index: int) -> Dir:
    return DIR_CYCLE[step_index % len(DIR_CYCLE)]


@dataclass
class LightController:
    """Deterministic rotating green per intersection (placeholder policy)."""

    enable_all_red: bool = False

    def decide_signals(self, intersections: list[Intersection], step_index: int) -> TrafficSignals:
        green = cycle_green(step_index)
        mapping: dict[Intersection, Dir | None] = {}
        for inter in intersections:
            mapping[inter] = None if self.enable_all_red else green
        return TrafficSignals(green_approach_by_intersection=mapping)
