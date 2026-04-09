"""V-group violation detector — wraps i-group evaluate_checks()."""

from __future__ import annotations

from traffic_infra.checks import ChecksReport, evaluate_checks
from traffic_infra.state import CarState, TrafficSignals


class VGroupVerifier:
    def __init__(self) -> None:
        self.collision_count: int = 0
        self.red_light_violations: int = 0
        self.illegal_direction_count: int = 0
        self.u_turn_count: int = 0
        self.intersection_crossing_violations: int = 0

    def check_step(
        self,
        prev: dict[str, CarState],
        nxt: dict[str, CarState],
        signals: TrafficSignals,
    ) -> ChecksReport:
        report = evaluate_checks(prev_cars=prev, next_cars=nxt, signals=signals)
        self.collision_count += report.collision_count
        self.red_light_violations += report.red_light_violations
        self.illegal_direction_count += report.illegal_direction_count
        self.u_turn_count += report.u_turn_count
        self.intersection_crossing_violations += report.intersection_crossing_violations
        return report

    def summary(self) -> dict:
        return {
            "collision_count": self.collision_count,
            "red_light_violations": self.red_light_violations,
            "illegal_direction_count": self.illegal_direction_count,
            "u_turn_count": self.u_turn_count,
            "intersection_crossing_violations": self.intersection_crossing_violations,
        }
