from __future__ import annotations

import argparse

from .depots import initial_car_from_depot_a
from .simulation import InfraSimulation
from .stub_vehicle import stub_vehicle_step


def main() -> None:
    parser = argparse.ArgumentParser(description="Traffic infrastructure (i-group) demo.")
    parser.add_argument(
        "--steps",
        type=int,
        default=5,
        help="Number of 2s control steps to simulate (stub vehicles).",
    )
    args = parser.parse_args()

    initial = {"car1": initial_car_from_depot_a("car1")}

    sim = InfraSimulation()
    sim.run_steps(initial=initial, step_fn=stub_vehicle_step, num_steps=args.steps)

    m = sim.cumulative
    print("Infrastructure demo (stub vehicles, rotating green policy)")
    print(f"  steps: {args.steps}")
    print(f"  cumulative collisions: {m.collision_count}")
    print(f"  cumulative red-light violations: {m.red_light_violations}")
    print(f"  cumulative illegal direction: {m.illegal_direction_count}")
    print(f"  cumulative U-turns: {m.u_turn_count}")
    print(f"  cumulative multi-crossing at intersection: {m.intersection_crossing_violations}")


if __name__ == "__main__":
    main()
