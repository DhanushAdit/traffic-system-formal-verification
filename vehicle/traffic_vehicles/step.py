"""vehicle_step() — the StepFn the i-group InfraSimulation calls."""

from __future__ import annotations

from traffic_infra.geometry import Intersection
from traffic_infra.state import CarState, TrafficSignals

from .constants import SLOTS_PER_SEGMENT
from .vehicle import Vehicle
from .routing import best_tour_order, get_full_path

# Module-level fleet state (persists across calls from InfraSimulation)
_fleet_registry: dict[str, Vehicle] = {}


def reset_vehicle_step_state() -> None:
    """Clear the persistent registry used by vehicle_step()."""
    _fleet_registry.clear()


def _priority(cs: CarState) -> int:
    """Higher priority = closer to intersection (higher slot number)."""
    return cs.slot


def vehicle_step(
    prev: dict[str, CarState],
    signals: TrafficSignals,
    congestion_map: dict[Intersection, int] | None = None,
) -> dict[str, CarState]:
    """
    The exact StepFn the i-group InfraSimulation calls.

    1. Sort cars by priority (closer to intersection = higher slot first)
    2. Track reserved intersections (max 1 crossing per intersection per step)
    3. For each car: decide_move, reserving intersection on crossing
    4. Return dict of new CarStates
    """
    if congestion_map is None:
        congestion_map = {}

    # Ensure all cars have a Vehicle wrapper
    _sync_registry(prev)

    # Sort cars: higher slot = closer to intersection = higher priority
    sorted_ids = sorted(prev.keys(), key=lambda cid: _priority(prev[cid]), reverse=True)

    reserved: set[Intersection] = set()
    next_states: dict[str, CarState] = {}

    # We need a mutable snapshot of current positions for collision avoidance
    current_positions: dict[str, CarState] = dict(prev)

    for car_id in sorted_ids:
        v = _fleet_registry[car_id]
        new_cs = v.decide_move(
            signals=signals,
            all_car_states=current_positions,
            congestion_map=congestion_map,
            intersection_crossing_reserved=reserved,
        )
        next_states[car_id] = new_cs
        # Update current_positions so later cars see already-claimed slots
        current_positions[car_id] = new_cs
        # Sync vehicle state
        v.current_edge = new_cs.edge
        v.current_slot = new_cs.slot
        v.driving_dir = new_cs.driving_dir

    return next_states


def _sync_registry(prev: dict[str, CarState]) -> None:
    """Add newly seen cars to the fleet registry; remove departed ones."""
    order = best_tour_order()
    full_path = get_full_path(order)
    tour_plan = ["A"] + order + ["A"]

    for car_id, cs in prev.items():
        if car_id not in _fleet_registry:
            # New car — create Vehicle from its current CarState
            # Find position in path
            remaining = _find_remaining_path(cs, full_path)
            v = Vehicle.from_car_state(
                cs=cs,
                tour_plan=tour_plan,
                destination_index=1,
                planned_path=remaining,
            )
            _fleet_registry[car_id] = v

    # Remove cars no longer in prev
    for gone in set(_fleet_registry) - set(prev):
        del _fleet_registry[gone]


def _find_remaining_path(
    cs: CarState, full_path: list
) -> list:
    """Find where cs.edge appears in full_path and return the rest."""
    for i, e in enumerate(full_path):
        if e == cs.edge:
            return list(full_path[i + 1:])
    return []
