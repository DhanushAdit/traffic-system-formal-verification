from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from .checks import ChecksReport
from .congestion import stopped_cars_per_intersection
from .igroupsim import IGroup
from .state import CarState, TrafficSignals


@dataclass
class CumulativeMetrics:
    collision_count: int = 0
    red_light_violations: int = 0
    illegal_direction_count: int = 0
    u_turn_count: int = 0
    intersection_crossing_violations: int = 0

    def add(self, report: ChecksReport) -> None:
        self.collision_count += report.collision_count
        self.red_light_violations += report.red_light_violations
        self.illegal_direction_count += report.illegal_direction_count
        self.u_turn_count += report.u_turn_count
        self.intersection_crossing_violations += report.intersection_crossing_violations


StepFn = Callable[[dict[str, CarState], TrafficSignals], dict[str, CarState]]


@dataclass
class InfraSimulation:
    """
    Runs the i-group loop: decide(prev) -> v-group/step_fn(next) -> report.
    """

    igroup: IGroup = field(default_factory=IGroup)
    cumulative: CumulativeMetrics = field(default_factory=CumulativeMetrics)

    def step(
        self,
        prev_cars: Mapping[str, CarState],
        next_cars: Mapping[str, CarState],
    ) -> tuple[ChecksReport, TrafficSignals, dict[tuple[int, int], int]]:
        """When both snapshots are already known (e.g. log replay)."""
        prev = dict(prev_cars)
        nxt = dict(next_cars)
        signals = self.igroup.decide(prev)
        report = self.igroup.report(nxt)
        self.cumulative.add(report)
        congestion = stopped_cars_per_intersection(prev, nxt)
        return report, signals, congestion

    def run_steps(
        self,
        initial: Mapping[str, CarState],
        step_fn: StepFn,
        num_steps: int,
    ) -> dict[str, CarState]:
        """
        For each step: emit signals from decide(prev), build next via step_fn(prev, signals), then report.
        """
        prev = dict(initial)
        for _ in range(num_steps):
            signals = self.igroup.decide(prev)
            nxt = step_fn(prev, signals)
            report = self.igroup.report(nxt)
            self.cumulative.add(report)
            prev = nxt
        return prev
