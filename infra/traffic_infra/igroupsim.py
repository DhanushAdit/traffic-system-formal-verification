from __future__ import annotations

from dataclasses import dataclass, field

from .geometry import grid_intersections
from .light_control import LightController
from .checks import ChecksReport, evaluate_checks
from .state import CarState, TrafficSignals


@dataclass
class IGroup:
    """
    Infrastructure simulator: chooses lights each step and evaluates safety checks
    on (prev_cars, next_cars) once v-group (or a stub) supplies both snapshots.
    """

    controller: LightController = field(default_factory=LightController)
    intersections: list = field(default_factory=grid_intersections)
    step_index: int = 0

    _last_prev_cars: dict[str, CarState] | None = None
    _last_signals: TrafficSignals | None = None

    def decide(self, prev_cars: dict[str, CarState]) -> TrafficSignals:
        signals = self.controller.decide_signals(self.intersections, self.step_index)
        self._last_prev_cars = prev_cars
        self._last_signals = signals
        return signals

    def report(self, next_cars: dict[str, CarState]) -> ChecksReport:
        if self._last_prev_cars is None or self._last_signals is None:
            raise RuntimeError("Call decide(prev_cars) before report(next_cars).")
        report = evaluate_checks(
            prev_cars=self._last_prev_cars,
            next_cars=next_cars,
            signals=self._last_signals,
        )
        self.step_index += 1
        self._last_prev_cars = None
        self._last_signals = None
        return report
