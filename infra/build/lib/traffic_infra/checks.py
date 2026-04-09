from __future__ import annotations

from dataclasses import dataclass

from .geometry import Dir
from .state import CarState, TrafficSignals


@dataclass(frozen=True)
class ChecksReport:
    collision_count: int
    red_light_violations: int
    illegal_direction_count: int
    u_turn_count: int
    intersection_crossing_violations: int


def _position_key(car: CarState) -> tuple[tuple[int, int], tuple[int, int], int]:
    return (car.edge.frm, car.edge.to, car.slot)


def _crossing_info(prev: CarState, nxt: CarState) -> tuple[tuple[int, int], Dir] | None:
    if prev.edge == nxt.edge:
        return None
    inter = prev.edge.to
    if nxt.edge.frm != inter:
        return None
    if prev.slot != 29 or nxt.slot != 0:
        return None
    approach = prev.edge.approach_dir_at_to_intersection()
    return inter, approach


def _is_u_turn(prev: CarState, nxt: CarState) -> bool:
    info = _crossing_info(prev, nxt)
    if info is None:
        return False
    return nxt.edge.to == prev.edge.frm


def evaluate_checks(
    prev_cars: dict[str, CarState],
    next_cars: dict[str, CarState],
    signals: TrafficSignals,
) -> ChecksReport:
    pos_to_count: dict[tuple[tuple[int, int], tuple[int, int], int], int] = {}
    for car in next_cars.values():
        key = _position_key(car)
        pos_to_count[key] = pos_to_count.get(key, 0) + 1

    collision_count = 0
    for k in pos_to_count.values():
        if k >= 2:
            collision_count += (k * (k - 1)) // 2

    red_light_violations = 0
    intersection_crossings: dict[tuple[int, int], int] = {}

    for car_id, prev in prev_cars.items():
        nxt = next_cars.get(car_id)
        if nxt is None:
            continue
        info = _crossing_info(prev, nxt)
        if info is None:
            continue
        inter, approach = info
        intersection_crossings[inter] = intersection_crossings.get(inter, 0) + 1
        if signals.color_for(intersection=inter, approach=approach).value != "green":
            red_light_violations += 1

    intersection_crossing_violations = 0
    for _, k in intersection_crossings.items():
        if k >= 2:
            intersection_crossing_violations += k - 1

    illegal_direction_count = 0
    for car in next_cars.values():
        physical_dir = car.edge.dir()
        if car.driving_dir != physical_dir:
            illegal_direction_count += 1

    u_turn_count = 0
    for car_id, prev in prev_cars.items():
        nxt = next_cars.get(car_id)
        if nxt is None:
            continue
        if _is_u_turn(prev, nxt):
            u_turn_count += 1

    return ChecksReport(
        collision_count=collision_count,
        red_light_violations=red_light_violations,
        illegal_direction_count=illegal_direction_count,
        u_turn_count=u_turn_count,
        intersection_crossing_violations=intersection_crossing_violations,
    )
