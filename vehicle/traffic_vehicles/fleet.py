"""Fleet: manages all vehicles, spawning, and congestion updates."""

from __future__ import annotations

from traffic_infra.geometry import DirectedEdge, Intersection
from traffic_infra.state import CarState

from .constants import MAX_CARS, PERIMETER_TOUR_ORDER, TERMINALS
from .routing import all_tour_permutations, get_full_path
from .vehicle import Vehicle
# Import step registry so fleet and step share the same Vehicle objects
from .step import _fleet_registry as _step_registry


def _get_spawn_edge(order: list[str] | None = None) -> DirectedEdge:
    """First edge of a tour with the given order — always starts at terminal A's intersection."""
    if order is None:
        order = PERIMETER_TOUR_ORDER
    return get_full_path(order)[0]


class Fleet:
    def __init__(self) -> None:
        self.vehicles: dict[str, Vehicle] = {}
        self.next_car_id: int = 1
        self.completed_tours: int = 0
        self.congestion_map: dict[Intersection, int] = {}
        self.spawn_step_counter: int = 0

    # ------------------------------------------------------------------ #
    def spawn_car(self) -> str | None:
        """Place a new car on the fixed perimeter tour if the entry slot is free."""
        if len(self.vehicles) >= MAX_CARS:
            return None
        order = list(PERIMETER_TOUR_ORDER)
        spawn_edge = _get_spawn_edge(order)
        # Check slot 0 of spawn edge is clear
        for v in self.vehicles.values():
            if v.current_edge == spawn_edge and v.current_slot == 0:
                return None
        car_id = f"car_{self.next_car_id}"
        self.next_car_id += 1
        v = Vehicle.spawn(car_id, order=list(order))
        self.vehicles[car_id] = v
        _step_registry[car_id] = v  # share same object with step.py
        return car_id

    def update_congestion(self, congestion_map: dict[Intersection, int]) -> None:
        self.congestion_map = congestion_map

    def get_all_car_states(self) -> dict[str, CarState]:
        return {cid: v.to_car_state() for cid, v in self.vehicles.items()}

    def apply_next_states(self, next_states: dict[str, CarState]) -> dict[str, CarState]:
        """
        Update vehicle objects from new CarStates.
        Detect tour completions: vehicle returned to terminal A intersection.
        """
        terminal_a = TERMINALS["A"]
        to_remove: list[str] = []
        completed_snapshot: dict[str, CarState] = {}

        for car_id, new_cs in next_states.items():
            if car_id not in self.vehicles:
                continue
            v = self.vehicles[car_id]
            v.current_edge = new_cs.edge
            v.current_slot = new_cs.slot
            v.driving_dir = new_cs.driving_dir

            # A tour completes only when the car enters terminal A after visiting B, C, and D.
            if new_cs.edge.to == terminal_a and v.destination_index >= len(v.tour_plan) - 1:
                v.completed_tours += 1
                self.completed_tours += 1
                completed_snapshot[car_id] = new_cs
                to_remove.append(car_id)

        for car_id in to_remove:
            del self.vehicles[car_id]
            _step_registry.pop(car_id, None)

        return completed_snapshot

    def throughput_per_hour(self, elapsed_steps: int) -> float:
        if elapsed_steps == 0:
            return 0.0
        elapsed_hours = elapsed_steps * 2 / 3600
        return self.completed_tours / elapsed_hours

    def throughput_per_minute(self, elapsed_steps: int) -> float:
        if elapsed_steps == 0:
            return 0.0
        elapsed_minutes = elapsed_steps * 2 / 60
        return self.completed_tours / elapsed_minutes
