"""Vehicle class: state machine wrapping CarState with tour tracking."""

from __future__ import annotations

from dataclasses import dataclass

from traffic_infra.geometry import Dir, DirectedEdge, Intersection
from traffic_infra.state import CarState, LightColor, TrafficSignals

from .constants import SLOTS_PER_SEGMENT, TERMINALS
from .network import get_approach_dir, get_turn_type, get_valid_next_edges
from .routing import best_tour_order, get_full_path


@dataclass
class Vehicle:
    car_id: str
    current_edge: DirectedEdge
    current_slot: int
    driving_dir: Dir
    tour_plan: list[str]            # e.g. ["A","B","D","C","A"]
    destination_index: int          # index into tour_plan (current target)
    planned_path: list[DirectedEdge]# remaining edges to follow
    status: str = "moving"          # "moving" | "stopped" | "waiting" | "completed"
    completed_tours: int = 0

    # ------------------------------------------------------------------ #
    @classmethod
    def spawn(cls, car_id: str, order: list[str] | None = None) -> "Vehicle":
        """Create a fresh vehicle at the first edge of the given tour order.

        If *order* is None the shortest (best) order is used as a fallback.
        """
        if order is None:
            order = best_tour_order()
        tour_plan = ["A"] + order + ["A"]   # full waypoints
        path = get_full_path(order)
        spawn_edge = path[0]
        remaining = list(path[1:])
        return cls(
            car_id=car_id,
            current_edge=spawn_edge,
            current_slot=0,
            driving_dir=spawn_edge.dir(),
            tour_plan=tour_plan,
            destination_index=1,    # heading toward tour_plan[1]
            planned_path=remaining,
            status="moving",
            completed_tours=0,
        )

    @classmethod
    def from_car_state(
        cls,
        cs: CarState,
        tour_plan: list[str],
        destination_index: int,
        planned_path: list[DirectedEdge],
        status: str = "moving",
        completed_tours: int = 0,
    ) -> "Vehicle":
        return cls(
            car_id=cs.car_id,
            current_edge=cs.edge,
            current_slot=cs.slot,
            driving_dir=cs.driving_dir,
            tour_plan=tour_plan,
            destination_index=destination_index,
            planned_path=planned_path,
            status=status,
            completed_tours=completed_tours,
        )

    def current_destination(self) -> str:
        if self.destination_index < len(self.tour_plan):
            return self.tour_plan[self.destination_index]
        return self.tour_plan[-1]

    def to_car_state(self) -> CarState:
        return CarState(
            car_id=self.car_id,
            edge=self.current_edge,
            slot=self.current_slot,
            driving_dir=self.driving_dir,
        )

    # ------------------------------------------------------------------ #
    def decide_move(
        self,
        signals: TrafficSignals,
        all_car_states: dict[str, CarState],
        congestion_map: dict[Intersection, int],
        intersection_crossing_reserved: set[Intersection],
    ) -> CarState:
        """
        Returns the new CarState for this vehicle.
        Priority rules applied in order — all create new CarState (immutable).
        """
        at_end_of_edge = (self.current_slot == SLOTS_PER_SEGMENT - 1)

        if not at_end_of_edge:
            # --- On-edge movement ---
            next_slot = self.current_slot + 1
            if self._slot_occupied(next_slot, self.current_edge, all_car_states):
                return self._stay()
            return CarState(
                car_id=self.car_id,
                edge=self.current_edge,
                slot=next_slot,
                driving_dir=self.driving_dir,
            )
        else:
            # --- At slot 29: intersection crossing logic ---
            intersection = self.current_edge.to
            approach = get_approach_dir(self.current_edge)

            # Determine next edge
            next_edge = self._pick_next_edge()
            if next_edge is None:
                return self._stay()

            turn = get_turn_type(self.current_edge.dir(), next_edge.dir())

            # No U-turns or right turns (project spec constraints)
            if turn == "uturn":
                return self._stay()
            if turn == "right":
                return self._stay()

            # Check signal
            color = signals.color_for(intersection=intersection, approach=approach)
            if color != LightColor.GREEN:
                return self._stay()

            # Check intersection reservation (max 1 car per intersection per step)
            if intersection in intersection_crossing_reserved:
                return self._stay()

            # Slot-based entry: a car may enter the next edge iff slot 0 is free.
            if self._slot_occupied(0, next_edge, all_car_states):
                return self._stay()

            # Cross the intersection
            intersection_crossing_reserved.add(intersection)
            # Advance planned_path
            self._advance_path(next_edge)
            return CarState(
                car_id=self.car_id,
                edge=next_edge,
                slot=0,
                driving_dir=next_edge.dir(),
            )

    # ------------------------------------------------------------------ #
    def _stay(self) -> CarState:
        return CarState(
            car_id=self.car_id,
            edge=self.current_edge,
            slot=self.current_slot,
            driving_dir=self.driving_dir,
        )

    def _pick_next_edge(self) -> DirectedEdge | None:
        """Follow planned_path if available; otherwise pick valid continuation."""
        if self.planned_path:
            candidate = self.planned_path[0]
            # Verify it continues from our current edge's to-intersection
            if candidate.frm == self.current_edge.to:
                return candidate
        # Fallback: any valid (non-U-turn) edge
        valids = get_valid_next_edges(self.current_edge)
        return valids[0] if valids else None

    def _advance_path(self, taken_edge: DirectedEdge) -> None:
        """Pop taken_edge off planned_path and update destination_index."""
        if self.planned_path and self.planned_path[0] == taken_edge:
            self.planned_path.pop(0)
        # Check if we arrived at current destination's adjacent intersection
        dest_name = self.current_destination()
        if dest_name in TERMINALS and taken_edge.to == TERMINALS[dest_name]:
            self.destination_index = min(self.destination_index + 1, len(self.tour_plan) - 1)

    def _slot_occupied(
        self,
        slot: int,
        edge: DirectedEdge,
        all_car_states: dict[str, CarState],
    ) -> bool:
        for cid, cs in all_car_states.items():
            if cid == self.car_id:
                continue
            if cs.edge == edge and cs.slot == slot:
                return True
        return False
