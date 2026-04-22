"""End-to-end runtime that combines infrastructure checks with vehicle control."""

from __future__ import annotations

from dataclasses import dataclass

from traffic_vehicles.fleet import Fleet
from traffic_vehicles.step import reset_vehicle_step_state, vehicle_step

from .checks import ChecksReport
from .congestion import stopped_cars_per_intersection
from .simulation import InfraSimulation
from .state import CarState, TrafficSignals


@dataclass
class IntegratedStepResult:
    prev_cars: dict[str, CarState]
    current_cars: dict[str, CarState]
    signals: TrafficSignals
    report: ChecksReport
    congestion: dict[tuple[int, int], int]
    spawned_car_id: str | None = None


class IntegratedSimulation:
    """Runs the full project loop: signals -> vehicle motion -> formal checks."""

    def __init__(self, *, spawn_interval: int = 1, num_initial_cars: int = 4) -> None:
        self.spawn_interval = spawn_interval
        self.num_initial_cars = num_initial_cars
        self.sim = InfraSimulation()
        self.fleet = Fleet()
        self.step_count = 0
        self.reset()

    def reset(self) -> dict[str, CarState]:
        reset_vehicle_step_state()
        self.sim = InfraSimulation()
        self.fleet = Fleet()
        self.step_count = 0
        self._spawn_initial_cars()
        return self.current_cars()

    def current_cars(self) -> dict[str, CarState]:
        return self.fleet.get_all_car_states()

    def step(self) -> IntegratedStepResult:
        prev = self.current_cars()
        signals = self.sim.igroup.decide(prev)
        nxt = vehicle_step(prev, signals, self.fleet.congestion_map)
        report = self.sim.igroup.report(nxt)
        self.sim.cumulative.add(report)

        congestion = stopped_cars_per_intersection(prev, nxt)
        self.fleet.update_congestion(congestion)
        completed_snapshot = self.fleet.apply_next_states(nxt)

        self.step_count += 1
        spawned_car_id = self._spawn_scheduled_car()
        current_snapshot = self.current_cars()
        current_snapshot.update(completed_snapshot)

        return IntegratedStepResult(
            prev_cars=prev,
            current_cars=current_snapshot,
            signals=signals,
            report=report,
            congestion=congestion,
            spawned_car_id=spawned_car_id,
        )

    def throughput_per_minute(self) -> float:
        return self.fleet.throughput_per_minute(self.step_count)

    def _spawn_initial_cars(self) -> None:
        for _ in range(self.num_initial_cars):
            car_id = self.fleet.spawn_car()
            if car_id is None:
                break

    def _spawn_scheduled_car(self) -> str | None:
        if self.spawn_interval <= 0:
            return None
        if self.step_count % self.spawn_interval != 0:
            return None
        return self.fleet.spawn_car()
