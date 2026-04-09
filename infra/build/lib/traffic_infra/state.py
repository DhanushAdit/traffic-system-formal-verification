from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .geometry import Dir, DirectedEdge, Intersection


class LightColor(str, Enum):
    GREEN = "green"
    RED = "red"


@dataclass(frozen=True)
class IntersectionLight:
    intersection: Intersection
    green_approach: Dir | None

    def color_for_approach(self, approach: Dir) -> LightColor:
        if self.green_approach is None:
            return LightColor.RED
        return LightColor.GREEN if self.green_approach == approach else LightColor.RED


@dataclass(frozen=True)
class TrafficSignals:
    green_approach_by_intersection: dict[Intersection, Dir | None]

    def intersection_light(self, intersection: Intersection) -> IntersectionLight:
        return IntersectionLight(
            intersection=intersection,
            green_approach=self.green_approach_by_intersection.get(intersection),
        )

    def color_for(self, intersection: Intersection, approach: Dir) -> LightColor:
        return self.intersection_light(intersection).color_for_approach(approach)


@dataclass(frozen=True)
class CarState:
    car_id: str
    edge: DirectedEdge
    slot: int
    driving_dir: Dir


@dataclass(frozen=True)
class CarSignal:
    car_id: str
    edge: DirectedEdge
    slot: int
    driving_dir: Dir
