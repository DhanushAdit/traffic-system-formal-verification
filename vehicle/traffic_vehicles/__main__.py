"""CLI entry point for v-group standalone simulation."""

from __future__ import annotations

import argparse

from .simulation import VGroupSimulation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="V-Group standalone simulation (ECEN723 Spring 2026)"
    )
    parser.add_argument("--steps", type=int, default=1800, help="Number of simulation steps")
    parser.add_argument(
        "--hours",
        type=float,
        default=None,
        help="Fast-forward simulation for this many simulated hours.",
    )
    parser.add_argument("--cars", type=int, default=4, help="Number of initial cars")
    parser.add_argument("--spawn-interval", type=int, default=1,
                        help="Spawn a new car every N steps if A-slot is free")
    parser.add_argument(
        "--unsafe-rate",
        type=float,
        default=0.0,
        help="Fraction of cars per step to randomly perturb for violation demos (0.0-1.0).",
    )
    parser.add_argument("--seed", type=int, default=723, help="Random seed for unsafe mode")
    parser.add_argument("--verbose", action="store_true", help="Print every step")
    args = parser.parse_args()

    sim = VGroupSimulation(
        spawn_interval=args.spawn_interval,
        unsafe_rate=args.unsafe_rate,
        random_seed=args.seed,
    )
    steps = args.steps if args.hours is None else sim.steps_for_hours(args.hours)
    result = sim.run(num_steps=steps, num_initial_cars=args.cars, verbose=args.verbose)

    print("\n=== SimulationResult ===")
    print(f"  total_steps                     : {result.total_steps}")
    print(f"  simulated_hours                 : {result.simulated_hours:.4f}")
    print(f"  completed_tours                 : {result.completed_tours}")
    print(f"  completed_loops                 : {result.completed_tours}")
    print(f"  throughput_per_minute           : {result.throughput_per_minute:.4f}")
    print(f"  throughput_per_hour             : {result.throughput_per_hour:.4f}")
    print(f"  collision_count                 : {result.collision_count}")
    print(f"  red_light_violations            : {result.red_light_violations}")
    print(f"  illegal_direction_count         : {result.illegal_direction_count}")
    print(f"  u_turn_count                    : {result.u_turn_count}")
    print(f"  intersection_crossing_violations: {result.intersection_crossing_violations}")


if __name__ == "__main__":
    main()
