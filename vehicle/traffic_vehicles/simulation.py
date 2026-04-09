"""Standalone Phase A simulation loop."""

from __future__ import annotations

from dataclasses import dataclass

from traffic_infra.congestion import stopped_cars_per_intersection
from traffic_infra.geometry import grid_intersections
from traffic_infra.light_control import LightController
from traffic_infra.state import CarState

from .fleet import Fleet
from .step import vehicle_step
from .verifier import VGroupVerifier


@dataclass
class SimulationResult:
    total_steps: int
    completed_tours: int
    throughput_per_hour: float
    collision_count: int
    red_light_violations: int
    illegal_direction_count: int
    u_turn_count: int
    intersection_crossing_violations: int


class VGroupSimulation:
    def __init__(self, spawn_interval: int = 5) -> None:
        self.fleet = Fleet()
        self.verifier = VGroupVerifier()
        self.step_count: int = 0
        self.spawn_interval: int = spawn_interval
        self._controller = LightController()
        self._intersections = grid_intersections()

    def run(
        self,
        num_steps: int = 1800,
        num_initial_cars: int = 4,
        verbose: bool = False,
    ) -> SimulationResult:
        # Spawn initial cars — stagger them by advancing each off slot 0 first
        for i in range(num_initial_cars):
            new_id = self.fleet.spawn_car()
            if new_id is not None and i > 0:
                # Move this car forward so it doesn't block slot 0 for the next spawn
                v = self.fleet.vehicles[new_id]
                v.current_slot = i * 3  # space them out

        prev: dict[str, CarState] = self.fleet.get_all_car_states()

        for step in range(num_steps):
            # 1. Generate stub signals (same rotating green as i-group LightController)
            signals = self._controller.decide_signals(self._intersections, step)

            # 2. Compute next states for active cars
            congestion = self.fleet.congestion_map
            nxt = vehicle_step(prev, signals, congestion)

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
        return SimulationResult(
            total_steps=self.step_count,
            completed_tours=self.fleet.completed_tours,
            throughput_per_hour=throughput,
            collision_count=self.verifier.collision_count,
            red_light_violations=self.verifier.red_light_violations,
            illegal_direction_count=self.verifier.illegal_direction_count,
            u_turn_count=self.verifier.u_turn_count,
            intersection_crossing_violations=self.verifier.intersection_crossing_violations,
        )

    def print_report(self) -> None:
        s = self.verifier.summary()
        print(f"\n=== V-Group Simulation Report ===")
        print(f"  Steps run          : {self.step_count}")
        print(f"  Completed tours    : {self.fleet.completed_tours}")
        print(f"  Throughput/hr      : {self.fleet.throughput_per_hour(self.step_count):.2f}")
        for k, v in s.items():
            print(f"  {k:<35}: {v}")
