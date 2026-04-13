# Traffic System Formal Verification

A discrete-time traffic simulator for a 3x3 road grid with runtime safety checking, throughput measurement, and a browser visualizer.

This repository contains both parts of the system:

- `infra/traffic_infra`: traffic signals, formal safety checks, integrated simulation, web UI
- `vehicle/traffic_vehicles`: vehicle motion, routing, fleet management, throughput simulation

The main goal is to move cars through the grid, make them complete the full corner loop

`A -> B -> C -> D -> A`

while tracking:

- completed loops
- throughput per minute
- throughput per hour
- collisions
- red-light violations
- illegal direction violations
- U-turn violations
- intersection crossing violations

## System Flow

Each simulation step represents `2 seconds`.

The current implementation works like this:

1. The infrastructure controller selects the signal phase.
2. Vehicles read the signal and attempt to move one slot forward.
3. A car at the end of an edge may cross only if:
   - its approach has green
   - the target slot is free
   - the intersection is not already reserved in that step
4. The infrastructure checker evaluates the next state.
5. Cars that finish the full loop `A -> B -> C -> D -> A` are counted and removed.
6. New cars are spawned if the entry slot is available.

Cars queue behind each other, so under safe operation there should be at most one car per edge-slot.

## Current Driving Logic

- All cars follow the same perimeter loop for higher throughput:
  `A -> B -> C -> D -> A`
- Signal phases are aligned with that loop.
- Cars stop before the intersection when the light is not green.
- A completed loop increases the completion counter by `1`.
- A completed car does not restart.

## Safety Metrics

The checker reports these cumulative metrics:

- `collision_count`
- `red_light_violations`
- `illegal_direction_count`
- `u_turn_count`
- `intersection_crossing_violations`

Important note:

`collision_count` is counted as pairwise slot conflicts, not “number of crashed cars”.
If `k` cars occupy the same slot in the same step, the count added is:

`k * (k - 1) / 2`

## Repository Layout

```text
.
├── README.md
├── infra/
│   ├── traffic_infra/
│   └── tests/
└── vehicle/
    ├── traffic_vehicles/
    └── tests/
```

Useful files:

- `infra/traffic_infra/integrated_simulation.py`
- `infra/traffic_infra/light_control.py`
- `infra/traffic_infra/checks.py`
- `infra/traffic_infra/web_app.py`
- `vehicle/traffic_vehicles/vehicle.py`
- `vehicle/traffic_vehicles/step.py`
- `vehicle/traffic_vehicles/fleet.py`
- `vehicle/traffic_vehicles/routing.py`
- `vehicle/traffic_vehicles/simulation.py`

## Setup

Use Python `3.10+`. On the shared server, Python `3.12` is recommended.

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e ./infra
pip install -e ./vehicle
pip install pytest
```

## Run Tests

Run all tests:

```bash
python -m pytest infra/tests vehicle/tests -v
```

Quiet mode:

```bash
python -m pytest infra/tests vehicle/tests -q
```

## Run the Integrated Simulation

This runs the infrastructure-controlled simulation and prints summary metrics:

```bash
python -m traffic_infra --steps 600 --cars 4 --spawn-interval 1
```

Save the output:

```bash
python -m traffic_infra --steps 600 --cars 4 --spawn-interval 1 | tee infra_run.txt
```

## Run the Vehicle Throughput Simulation

This runs the standalone vehicle simulation:

```bash
python -m traffic_vehicles --steps 1800 --cars 4 --spawn-interval 1
```

### Simulate 2 Hours Quickly

The simulation can fast-forward `2 hours` of traffic without taking `2 hours` of real time:

```bash
python -m traffic_vehicles --hours 2 --cars 4 --spawn-interval 1
```

Save the output:

```bash
python -m traffic_vehicles --hours 2 --cars 4 --spawn-interval 1 | tee sim_output.txt
```

The most important values in the output are:

- `completed_tours`
- `completed_loops`
- `throughput_per_minute`
- `throughput_per_hour`
- all safety violation counters

## Unsafe / Randomized Demonstration

To intentionally generate unsafe behavior and show that the checker detects violations:

```bash
python -m traffic_vehicles --hours 2 --cars 4 --spawn-interval 1 --unsafe-rate 0.05
```

With a fixed seed:

```bash
python -m traffic_vehicles --hours 2 --cars 4 --spawn-interval 1 --unsafe-rate 0.05 --seed 723
```

## Recommended Reproduction Steps

If you want to replicate the main results from scratch:

1. Create and activate a Python `3.12` virtual environment.
2. Install `infra`, `vehicle`, and `pytest`.
3. Run all tests.
4. Run the safe 2-hour simulation:

```bash
python -m traffic_vehicles --hours 2 --cars 4 --spawn-interval 1
```

5. Run the unsafe comparison simulation:

```bash
python -m traffic_vehicles --hours 2 --cars 4 --spawn-interval 1 --unsafe-rate 0.05
```

## Notes

- The visualizer renders backend snapshots from Python. It is not a fake frontend-only animation.
- Completed loops are counted only when a car returns to `A` after visiting all required corners.
- Throughput is derived from completed loops.
- The browser view is useful for qualitative inspection; the CLI output should be used for final metrics.
