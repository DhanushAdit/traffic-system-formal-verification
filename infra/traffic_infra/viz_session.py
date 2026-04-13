"""Simulation state for the web visualizer."""

from __future__ import annotations

from dataclasses import asdict

from .checks import ChecksReport
from .congestion import stopped_cars_per_intersection
from .constants import SLOTS_PER_SEGMENT
from .depots import assert_valid_start_state, depots_to_json, initial_car_from_depot_a
from .geometry import grid_intersections
from .protocol import car_state_to_json, traffic_signals_to_json
from .simulation import InfraSimulation
from .state import CarState, TrafficSignals
from .stub_vehicle import stub_vehicle_step

try:
    from .integrated_simulation import IntegratedSimulation
except ImportError:
    IntegratedSimulation = None


def _initial_cars() -> dict[str, CarState]:
    initial = {"car1": initial_car_from_depot_a("car1")}
    assert_valid_start_state(initial["car1"])
    return initial


class VizSimulationSession:
    """One runnable session for either the integrated or stub simulator."""

    def __init__(self) -> None:
        self._integrated: IntegratedSimulation | None = self._build_integrated()
        if self._integrated is None:
            self.initial = _initial_cars()
            self.sim = InfraSimulation()
            self.prev: dict[str, CarState] = dict(self.initial)
        else:
            self.initial = {}
            self.sim = self._integrated.sim
            self.prev = self._integrated.current_cars()

    def reset(self) -> dict:
        if self._integrated is not None:
            self.prev = self._integrated.reset()
            self.sim = self._integrated.sim
        else:
            self.sim = InfraSimulation()
            self.prev = dict(self.initial)
        return self._snapshot(
            report=None,
            signals=None,
            congestion={},
            stepped=False,
        )

    def step(self) -> dict:
        if self._integrated is not None:
            result = self._integrated.step()
            self.sim = self._integrated.sim
            self.prev = result.current_cars
            report = result.report
            signals = result.signals
            cong = result.congestion
        else:
            signals = self.sim.igroup.decide(self.prev)
            nxt = stub_vehicle_step(self.prev, signals)
            report = self.sim.igroup.report(nxt)
            self.sim.cumulative.add(report)
            cong = stopped_cars_per_intersection(self.prev, nxt)
            self.prev = nxt
        return self._snapshot(
            report=report,
            signals=signals,
            congestion=cong,
            stepped=True,
        )

    def _snapshot(
        self,
        *,
        report: ChecksReport | None,
        signals: TrafficSignals | None,
        congestion: dict[tuple[int, int], int],
        stepped: bool,
    ) -> dict:
        c = self.sim.cumulative
        return {
            "type": "state",
            "stepped": stepped,
            "step_index": self.sim.igroup.step_index,
            "slots_per_segment": SLOTS_PER_SEGMENT,
            "depots": depots_to_json(),
            "cars": {cid: car_state_to_json(c) for cid, c in self.prev.items()},
            "signals": traffic_signals_to_json(signals) if signals else None,
            "signals_all_intersections": self._signals_full_grid(signals),
            "signal_timing": self._signal_timing(),
            "congestion": {f"{x},{y}": n for (x, y), n in congestion.items()},
            "cumulative": {
                "collision_count": c.collision_count,
                "red_light_violations": c.red_light_violations,
                "illegal_direction_count": c.illegal_direction_count,
                "u_turn_count": c.u_turn_count,
                "intersection_crossing_violations": c.intersection_crossing_violations,
            },
            "last_report": asdict(report) if report else None,
            "intersections": [list(p) for p in grid_intersections()],
        }

    def _signals_full_grid(self, signals: TrafficSignals | None) -> dict[str, str | None]:
        out: dict[str, str | None] = {}
        for inter in grid_intersections():
            key = f"{inter[0]},{inter[1]}"
            if signals is None:
                out[key] = None
            else:
                g = signals.green_approach_by_intersection.get(inter)
                out[key] = None if g is None else g.value
        return out

    def _signal_timing(self) -> dict[str, int]:
        controller = self.sim.igroup.controller
        timing = {
            "green_steps": controller.green_steps,
            "green_seconds": controller.green_seconds,
            "all_red_steps": controller.all_red_steps,
            "all_red_seconds": controller.all_red_seconds,
        }
        timing.update(controller.phase_window(self.sim.igroup.step_index))
        return timing

    def _build_integrated(self) -> IntegratedSimulation | None:
        if IntegratedSimulation is None:
            return None
        return IntegratedSimulation()
