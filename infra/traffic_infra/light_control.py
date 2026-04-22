from __future__ import annotations

from dataclasses import dataclass

from .constants import CONTROL_STEP_SECONDS
from .geometry import Dir, Intersection
from .state import TrafficSignals


DIR_CYCLE: list[Dir] = [Dir.N, Dir.W, Dir.S, Dir.E]
DEFAULT_GREEN_STEPS = 1
DEFAULT_ALL_RED_STEPS = 0
DEFAULT_PHASE_DURATIONS: tuple[int, int, int, int] = (8, 7, 8, 7)


def _phase_starts(phase_durations: tuple[int, int, int, int]) -> dict[Dir, int]:
    starts: dict[Dir, int] = {}
    cursor = 0
    for direction, duration in zip(DIR_CYCLE, phase_durations):
        starts[direction] = cursor
        cursor += duration
    return starts


PHASE_STARTS = _phase_starts(DEFAULT_PHASE_DURATIONS)


def _dominant_approach(intersection: Intersection) -> Dir:
    x, y = intersection
    if x == 0 and y in (0, 1):
        return Dir.N
    if y == 0 and x in (1, 2):
        return Dir.W
    if x == 2 and y in (1, 2):
        return Dir.S
    if y == 2 and x in (0, 1):
        return Dir.E
    return Dir.N


def cycle_green(
    step_index: int,
    *,
    green_steps: int = DEFAULT_GREEN_STEPS,
    all_red_steps: int = DEFAULT_ALL_RED_STEPS,
    phase_durations: tuple[int, int, int, int] | None = None,
    phase_offset: int = 0,
) -> Dir | None:
    if phase_durations is None:
        if green_steps <= 0:
            raise ValueError("green_steps must be positive")
        if all_red_steps < 0:
            raise ValueError("all_red_steps must be non-negative")
        if green_steps == DEFAULT_GREEN_STEPS and all_red_steps == DEFAULT_ALL_RED_STEPS:
            phase_durations = DEFAULT_PHASE_DURATIONS
        else:
            phase_durations = (green_steps, green_steps, green_steps, green_steps)

    if any(duration <= 0 for duration in phase_durations):
        raise ValueError("phase durations must be positive")
    cycle_span = sum(phase_durations)
    local_step = (step_index + phase_offset) % cycle_span
    cursor = 0
    for direction, duration in zip(DIR_CYCLE, phase_durations):
        if cursor <= local_step < cursor + duration:
            return direction
        cursor += duration
    return None


@dataclass
class LightController:
    """Deterministic rotating green with held phases and optional all-red clearance."""

    enable_all_red: bool = False
    green_steps: int = DEFAULT_GREEN_STEPS
    all_red_steps: int = DEFAULT_ALL_RED_STEPS
    phase_durations: tuple[int, int, int, int] | None = None

    def __post_init__(self) -> None:
        if self.phase_durations is None:
            if (
                self.green_steps == DEFAULT_GREEN_STEPS
                and self.all_red_steps == DEFAULT_ALL_RED_STEPS
            ):
                self.phase_durations = DEFAULT_PHASE_DURATIONS
            else:
                self.phase_durations = (
                    self.green_steps,
                    self.green_steps,
                    self.green_steps,
                    self.green_steps,
                )

    def decide_signals(self, intersections: list[Intersection], step_index: int) -> TrafficSignals:
        mapping: dict[Intersection, Dir | None] = {}
        for inter in intersections:
            if self.enable_all_red:
                mapping[inter] = None
                continue
            dominant = _dominant_approach(inter)
            mapping[inter] = cycle_green(
                step_index,
                green_steps=self.green_steps,
                all_red_steps=self.all_red_steps,
                phase_durations=self.phase_durations,
                phase_offset=PHASE_STARTS[dominant],
            )
        return TrafficSignals(green_approach_by_intersection=mapping)

    @property
    def green_seconds(self) -> int:
        return max(self.phase_durations) * CONTROL_STEP_SECONDS

    @property
    def all_red_seconds(self) -> int:
        return self.all_red_steps * CONTROL_STEP_SECONDS

    def phase_window(self, step_index: int) -> dict[str, int | str | None]:
        cycle_span = sum(self.phase_durations)
        phase_index, phase_step = divmod(step_index, cycle_span)
        active = cycle_green(
            step_index,
            green_steps=self.green_steps,
            all_red_steps=self.all_red_steps,
            phase_durations=self.phase_durations,
        )
        remaining_steps = 0
        cursor = 0
        for direction, duration in zip(DIR_CYCLE, self.phase_durations):
            if cursor <= phase_step < cursor + duration:
                remaining_steps = cursor + duration - phase_step
                active = direction
                break
            cursor += duration
        return {
            "active_green": None if active is None else active.value,
            "phase_index": phase_index % len(DIR_CYCLE),
            "remaining_steps": remaining_steps,
            "remaining_seconds": remaining_steps * CONTROL_STEP_SECONDS,
            "cycle_steps": cycle_span,
            "cycle_seconds": cycle_span * CONTROL_STEP_SECONDS,
        }
