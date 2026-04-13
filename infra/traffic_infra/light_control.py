from __future__ import annotations

from dataclasses import dataclass

from .constants import CONTROL_STEP_SECONDS
from .geometry import Dir, Intersection
from .state import TrafficSignals


DIR_CYCLE: list[Dir] = [Dir.N, Dir.W, Dir.S, Dir.E]
DEFAULT_GREEN_STEPS = 15
DEFAULT_ALL_RED_STEPS = 0


def cycle_green(
    step_index: int,
    *,
    green_steps: int = DEFAULT_GREEN_STEPS,
    all_red_steps: int = DEFAULT_ALL_RED_STEPS,
) -> Dir | None:
    if green_steps <= 0:
        raise ValueError("green_steps must be positive")
    if all_red_steps < 0:
        raise ValueError("all_red_steps must be non-negative")

    cycle_span = green_steps + all_red_steps
    phase_index, phase_step = divmod(step_index, cycle_span)
    if phase_step >= green_steps:
        return None
    return DIR_CYCLE[phase_index % len(DIR_CYCLE)]


@dataclass
class LightController:
    """Deterministic rotating green with held phases and optional all-red clearance."""

    enable_all_red: bool = False
    green_steps: int = DEFAULT_GREEN_STEPS
    all_red_steps: int = DEFAULT_ALL_RED_STEPS

    def decide_signals(self, intersections: list[Intersection], step_index: int) -> TrafficSignals:
        green = cycle_green(
            step_index,
            green_steps=self.green_steps,
            all_red_steps=self.all_red_steps,
        )
        mapping: dict[Intersection, Dir | None] = {}
        for inter in intersections:
            mapping[inter] = None if self.enable_all_red else green
        return TrafficSignals(green_approach_by_intersection=mapping)

    @property
    def green_seconds(self) -> int:
        return self.green_steps * CONTROL_STEP_SECONDS

    @property
    def all_red_seconds(self) -> int:
        return self.all_red_steps * CONTROL_STEP_SECONDS

    def phase_window(self, step_index: int) -> dict[str, int | str | None]:
        cycle_span = self.green_steps + self.all_red_steps
        phase_index, phase_step = divmod(step_index, cycle_span)
        active = cycle_green(
            step_index,
            green_steps=self.green_steps,
            all_red_steps=self.all_red_steps,
        )
        if active is None:
            remaining_steps = self.all_red_steps - (phase_step - self.green_steps)
        else:
            remaining_steps = self.green_steps - phase_step
        return {
            "active_green": None if active is None else active.value,
            "phase_index": phase_index % len(DIR_CYCLE),
            "remaining_steps": remaining_steps,
            "remaining_seconds": remaining_steps * CONTROL_STEP_SECONDS,
        }
