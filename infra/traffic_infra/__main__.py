from __future__ import annotations

import argparse

from .depots import initial_car_from_depot_a
from .simulation import InfraSimulation
from .stub_vehicle import stub_vehicle_step

try:
    from .integrated_simulation import IntegratedSimulation
except ImportError:
    IntegratedSimulation = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Traffic infrastructure (i-group) demo.")
    parser.add_argument(
        "--steps",
        type=int,
        default=5,
        help="Number of 2s control steps to simulate.",
    )
    parser.add_argument("--cars", type=int, default=4, help="Initial cars for the integrated run.")
    parser.add_argument(
        "--spawn-interval",
        type=int,
        default=1,
        help="Spawn a new car every N steps during the integrated run.",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use the old infrastructure-only stub vehicle motion.",
    )
    args = parser.parse_args()

    if not args.stub and IntegratedSimulation is not None:
        try:
            integrated = IntegratedSimulation(
                spawn_interval=args.spawn_interval,
                num_initial_cars=args.cars,
            )
            for _ in range(args.steps):
                integrated.step()

            m = integrated.sim.cumulative
            print("Infrastructure demo (integrated vehicle controller)")
            print(f"  steps: {args.steps}")
            print(f"  active cars: {len(integrated.current_cars())}")
            print(f"  completed tours: {integrated.fleet.completed_tours}")
            print(f"  throughput per minute: {integrated.throughput_per_minute():.4f}")
            print(f"  cumulative collisions: {m.collision_count}")
            print(f"  cumulative red-light violations: {m.red_light_violations}")
            print(f"  cumulative illegal direction: {m.illegal_direction_count}")
            print(f"  cumulative U-turns: {m.u_turn_count}")
            print(
                "  cumulative multi-crossing at intersection: "
                f"{m.intersection_crossing_violations}"
            )
            return
        except ImportError:
            print("Integrated vehicle package not available; falling back to stub motion.")
    elif not args.stub:
        print("Integrated vehicle package not available; falling back to stub motion.")

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
