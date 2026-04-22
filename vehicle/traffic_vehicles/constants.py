"""V-group constants — mirrors i-group values exactly."""

from traffic_infra.constants import SLOTS_PER_SEGMENT, CONTROL_STEP_SECONDS, MPH_RUNNING

TOTAL_SIMULATION_STEPS = 1800  # 1 hour at 2 s/step
PERIMETER_TOUR_ORDER: list[str] = ["B", "C", "D"]

# Terminal labels → adjacent intersection coordinates
TERMINALS: dict[str, tuple[int, int]] = {
    "A": (0, 2),
    "B": (0, 0),
    "C": (2, 0),
    "D": (2, 2),
}

__all__ = [
    "SLOTS_PER_SEGMENT",
    "CONTROL_STEP_SECONDS",
    "MPH_RUNNING",
    "TOTAL_SIMULATION_STEPS",
    "PERIMETER_TOUR_ORDER",
    "TERMINALS",
]
