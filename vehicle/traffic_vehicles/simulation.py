"""Standalone Phase A simulation loop."""

from __future__ import annotations

from dataclasses import dataclass
import random

from traffic_infra.congestion import stopped_cars_per_intersection
from traffic_infra.constants import CONTROL_STEP_SECONDS
from traffic_infra.geometry import Dir, DirectedEdge, grid_intersections
from traffic_infra.light_control import LightController
from traffic_infra.state import CarState

from .fleet import Fleet
from .network import get_valid_next_edges
from .step import vehicle_step
from .verifier import VGroupVerifier


@dataclass
class SimulationResult:
    total_steps: int
    simulated_hours: float
    completed_tours: int
    throughput_per_minute: float
    throughput_per_hour: float
    collision_count: int
    red_light_violations: int
    illegal_direction_count: int
    u_turn_count: int
    intersection_crossing_violations: int


class VGroupSimulation:
    def __init__(
        self,
        spawn_interval: int = 1,
        *,
        unsafe_rate: float = 0.0,
        random_seed: int = 723,
    ) -> None:
        self.fleet = Fleet()
        self.verifier = VGroupVerifier()
        self.step_count: int = 0
        self.spawn_interval: int = spawn_interval
        self._controller = LightController()
        self._intersections = grid_intersections()
        self.unsafe_rate = unsafe_rate
        self._rng = random.Random(random_seed)

    @staticmethod
    def steps_for_hours(hours: float) -> int:
        return int((hours * 3600) / CONTROL_STEP_SECONDS)

    def run(
        self,
        num_steps: int = 1800,
        num_initial_cars: int = 4,
        verbose: bool = False,
    ) -> SimulationResult:
        # Spawn as many cars from A as the outbound lanes can legally accept.
        for i in range(num_initial_cars):
            new_id = self.fleet.spawn_car()
            if new_id is None:
                break

        prev: dict[str, CarState] = self.fleet.get_all_car_states()

        for step in range(num_steps):
            # 1. Generate stub signals (same rotating green as i-group LightController)
            signals = self._controller.decide_signals(self._intersections, step)

            # 2. Compute next states for active cars
            congestion = self.fleet.congestion_map
            nxt = vehicle_step(prev, signals, congestion)
            nxt = self._inject_random_violations(prev, nxt)

            # 3. Verify
            report = self.verifier.check_step(prev, nxt, signals)

            # 4. Compute congestion from stopped cars
            new_congestion = stopped_cars_per_intersection(prev, nxt)
            self.fleet.update_congestion(new_congestion)

            # 5. Apply new states (removes completed vehicles from fleet)
            self.fleet.apply_next_states(nxt)

            # 6. Build prev = latest states for surviving cars
            prev = {cid: cs for cid, cs in nxt.items() if cid in self.fleet.vehicles}

            # 7. Spawn new car every spawn_interval steps; add it to prev immediately
            if (step + 1) % self.spawn_interval == 0:
                new_id = self.fleet.spawn_car()
                if new_id is not None:
                    prev[new_id] = self.fleet.vehicles[new_id].to_car_state()

            self.step_count += 1

            if verbose or (step + 1) % 100 == 0:
                print(
                    f"Step {step+1:4d} | cars={len(self.fleet.vehicles):3d} "
                    f"| completed_tours={self.fleet.completed_tours} "
                    f"| collisions={self.verifier.collision_count}"
                )

        throughput = self.fleet.throughput_per_hour(self.step_count)
        throughput_per_minute = self.fleet.throughput_per_minute(self.step_count)
        return SimulationResult(
            total_steps=self.step_count,
            simulated_hours=(self.step_count * CONTROL_STEP_SECONDS) / 3600,
            completed_tours=self.fleet.completed_tours,
            throughput_per_minute=throughput_per_minute,
            throughput_per_hour=throughput,
            collision_count=self.verifier.collision_count,
            red_light_violations=self.verifier.red_light_violations,
            illegal_direction_count=self.verifier.illegal_direction_count,
            u_turn_count=self.verifier.u_turn_count,
            intersection_crossing_violations=self.verifier.intersection_crossing_violations,
        )

    def _inject_random_violations(
        self,
        prev: dict[str, CarState],
        nxt: dict[str, CarState],
    ) -> dict[str, CarState]:
        """Optional chaos mode to demonstrate violations and robustness metrics."""
        if self.unsafe_rate <= 0.0 or not nxt:
            return nxt

        mutated = dict(nxt)
        for car_id, next_state in list(mutated.items()):
            if self._rng.random() >= self.unsafe_rate:
                continue
            prev_state = prev.get(car_id)
            if prev_state is None:
                continue
            scenario = self._rng.choice(("red_light", "wrong_way", "collision"))
            if scenario == "red_light":
                forced = self._force_red_light_crossing(prev_state)
                if forced is not None:
                    mutated[car_id] = forced
            elif scenario == "wrong_way":
                mutated[car_id] = CarState(
                    car_id=next_state.car_id,
                    edge=next_state.edge,
                    slot=next_state.slot,
                    driving_dir=self._rng.choice([d for d in Dir if d != next_state.driving_dir]),
                )
            elif scenario == "collision":
                target_id = self._rng.choice(list(mutated.keys()))
                if target_id != car_id:
                    target = mutated[target_id]
                    mutated[car_id] = CarState(
                        car_id=next_state.car_id,
                        edge=target.edge,
                        slot=target.slot,
                        driving_dir=target.driving_dir,
                    )
        return mutated

    def _force_red_light_crossing(self, prev_state: CarState) -> CarState | None:
        if prev_state.slot != 29:
            return None
        options = get_valid_next_edges(prev_state.edge)
        if not options:
            return None
        forced_edge = self._rng.choice(options)
        return CarState(
            car_id=prev_state.car_id,
            edge=forced_edge,
            slot=0,
            driving_dir=forced_edge.dir(),
        )

    def print_report(self) -> None:
        s = self.verifier.summary()
        print(f"\n=== V-Group Simulation Report ===")
        print(f"  Steps run          : {self.step_count}")
        print(f"  Simulated hours    : {(self.step_count * CONTROL_STEP_SECONDS) / 3600:.2f}")
        print(f"  Completed tours    : {self.fleet.completed_tours}")
        print(f"  Throughput/min     : {self.fleet.throughput_per_minute(self.step_count):.2f}")
        print(f"  Throughput/hr      : {self.fleet.throughput_per_hour(self.step_count):.2f}")
        for k, v in s.items():
            print(f"  {k:<35}: {v}")
