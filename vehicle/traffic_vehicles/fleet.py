"""Fleet: manages all vehicles, spawning, and congestion updates."""

from __future__ import annotations

from traffic_infra.geometry import DirectedEdge, Intersection
from traffic_infra.state import CarState

from .constants import MAX_CARS, TERMINALS
from .routing import all_tour_permutations, get_full_path
from .vehicle import Vehicle
# Import step registry so fleet and step share the same Vehicle objects
from .step import _fleet_registry as _step_registry


_ALL_PERMUTATIONS: list[list[str]] = all_tour_permutations()


def _get_spawn_edge(order: list[str]) -> DirectedEdge:
    """First edge of a tour with the given order — always starts at terminal A's intersection."""
    return get_full_path(order)[0]


class Fleet:
    def __init__(self) -> None:
        self.vehicles: dict[str, Vehicle] = {}
        self.next_car_id: int = 1
        self.completed_tours: int = 0
        self.congestion_map: dict[Intersection, int] = {}
        self.spawn_step_counter: int = 0
        self._perm_index: int = 0  # round-robin index into _ALL_PERMUTATIONS

    # ------------------------------------------------------------------ #
    def spawn_car(self) -> str | None:
        """Place a new car at slot 0 of its tour's first edge if free and below MAX_CARS.

        Cars are assigned tour permutations in round-robin order so that all six
        A→B/C/D→A orderings are exercised across the fleet.
        """
        if len(self.vehicles) >= MAX_CARS:
            return None
        order = _ALL_PERMUTATIONS[self._perm_index % len(_ALL_PERMUTATIONS)]
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
        self._perm_index += 1
        return car_id

    def update_congestion(self, congestion_map: dict[Intersection, int]) -> None:
        self.congestion_map = congestion_map

    def get_all_car_states(self) -> dict[str, CarState]:
        return {cid: v.to_car_state() for cid, v in self.vehicles.items()}

    def apply_next_states(self, next_states: dict[str, CarState]) -> None:
        """
        Update vehicle objects from new CarStates.
        Detect tour completions: vehicle returned to terminal A intersection.
        """
        terminal_a = TERMINALS["A"]
        to_remove: list[str] = []

        for car_id, new_cs in next_states.items():
            if car_id not in self.vehicles:
                continue
            v = self.vehicles[car_id]
            old_edge = v.current_edge
            v.current_edge = new_cs.edge
            v.current_slot = new_cs.slot
            v.driving_dir = new_cs.driving_dir

            # Detect crossing back to terminal A's intersection after visiting B/C/D
            # A tour completes when car arrives at terminal_a after completing all stops
            if (new_cs.edge.frm == terminal_a or new_cs.edge.to == terminal_a):
                if v.destination_index >= len(v.tour_plan) - 1:
                    # Completed a full tour
                    v.completed_tours += 1
                    self.completed_tours += 1
                    to_remove.append(car_id)

        for car_id in to_remove:
            del self.vehicles[car_id]
            _step_registry.pop(car_id, None)

    def throughput_per_hour(self, elapsed_steps: int) -> float:
        if elapsed_steps == 0:
            return 0.0
        elapsed_hours = elapsed_steps * 2 / 3600
        return self.completed_tours / elapsed_hours
