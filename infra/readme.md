Traffic Infrastructure Package

This folder contains the infrastructure-side implementation of the traffic
system.  Its job is to:

- define the road/intersection model used by the simulator
- choose traffic-signal states each control step
- evaluate the infrastructure safety properties after vehicle motion
- expose a CLI and web visualizer for stepping the integrated system

The current code is no longer just a placeholder i-group stub.  It supports the
full integrated runtime used by the project, while still keeping the original
infrastructure-only interfaces for testing and replay.

## What The Infrastructure Layer Does

At a high level, one control step is:

1. take the current snapshot of cars
2. choose the green approach at each intersection
3. let the vehicle layer compute the next snapshot
4. run infrastructure checks on `prev -> next`
5. accumulate safety metrics and congestion information

In code, that loop is implemented in:

- [traffic_infra/igroupsim.py](./traffic_infra/igroupsim.py)
- [traffic_infra/simulation.py](./traffic_infra/simulation.py)
- [traffic_infra/integrated_simulation.py](./traffic_infra/integrated_simulation.py)

## Main Modules

- [traffic_infra/geometry.py](./traffic_infra/geometry.py)
  Defines the directed road geometry, grid intersections, travel directions,
  and edge relationships used by both the checker and the visualizer.

- [traffic_infra/state.py](./traffic_infra/state.py)
  Defines the data model used by the infrastructure side, such as `CarState`
  and `TrafficSignals`.

- [traffic_infra/light_control.py](./traffic_infra/light_control.py)
  Implements the deterministic signal controller.  The current controller uses
  per-intersection offsets over a shared `N -> W -> S -> E` direction cycle so
  the outer perimeter favors the legal circulation pattern.

- [traffic_infra/checks.py](./traffic_infra/checks.py)
  Evaluates the infrastructure safety properties from a previous and next car
  snapshot.

- [traffic_infra/congestion.py](./traffic_infra/congestion.py)
  Computes stopped-car counts near intersections so the vehicle layer can use
  congestion information if needed.

- [traffic_infra/igroupsim.py](./traffic_infra/igroupsim.py)
  Infrastructure controller object.  It exposes the core protocol:
  `decide(prev_cars)` followed by `report(next_cars)`.

- [traffic_infra/simulation.py](./traffic_infra/simulation.py)
  Wraps the infrastructure controller with cumulative metric tracking and a
  generic `step(prev, next)` / `run_steps(...)` API.

- [traffic_infra/integrated_simulation.py](./traffic_infra/integrated_simulation.py)
  Runs the full project loop by connecting infrastructure control to the
  vehicle package.

- [traffic_infra/web_app.py](./traffic_infra/web_app.py)
  Hosts the HTTP visualizer used for interactive stepping.

## Checked Properties

The infrastructure checker currently reports these properties every step:

- `collision_count`
  Counts pairwise slot collisions in the next state.

- `red_light_violations`
  Counts cars that crossed an intersection on a non-green approach.

- `illegal_direction_count`
  Counts cars whose logical driving direction does not match the direction of
  the lane they occupy.

- `u_turn_count`
  Counts cars that leave an edge and immediately reverse direction through the
  intersection.

- `intersection_crossing_violations`
  Counts extra cars when more than one vehicle crosses the same intersection in
  the same control step.

These checks are evaluated in
[traffic_infra/checks.py](./traffic_infra/checks.py) and accumulated by
[traffic_infra/simulation.py](./traffic_infra/simulation.py).

## Signal Model

The signal controller is deterministic.  Every intersection exposes at most one
green approach at a time.

Important details:

- direction cycle: `N -> W -> S -> E`
- default control step length: 2 seconds
- no all-red gap in the current default runtime
- each intersection uses a phase offset based on its position so the perimeter
  loop gets a coordinated flow instead of a single global green everywhere

The signal API returns a `TrafficSignals` object keyed by intersection.

## Integrated Runtime

When the vehicle package is available, the recommended runtime is the
integrated simulator:

- infrastructure decides lights
- vehicle logic moves cars legally
- infrastructure checks the resulting transition
- congestion and cumulative metrics are updated
- scheduled spawning is applied

The CLI entry point prefers this integrated mode automatically.

## Stub Runtime

The old stub mode still exists for simple infrastructure-only testing.

Use it when you want to test the checker/control loop without importing the
vehicle package.  In stub mode, a simple step function is used instead of the
real vehicle controller.

## How To Run

From the repo root, use `PYTHONPATH=infra:vehicle` so both packages are
importable.

Integrated CLI demo:

```bash
PYTHONPATH=infra:vehicle python -m traffic_infra --steps 300 --cars 4 --spawn-interval 1
```

Stub-only CLI demo:

```bash
PYTHONPATH=infra:vehicle python -m traffic_infra --stub --steps 20
```

Web visualizer:

```bash
PYTHONPATH=infra:vehicle python -m traffic_infra.web_app
```

Then open:

```text
http://127.0.0.1:8765/
```

If port `8765` is busy:

```bash
PYTHONPATH=infra:vehicle python -m traffic_infra.web_app --port 8766
```

Convenience launcher:

```bash
./run_simulation.sh
```

## Tests

Run the infrastructure and vehicle tests from the repo root:

```bash
PYTHONPATH=infra:vehicle python -m pytest infra/tests vehicle/tests -q
```

The infrastructure-focused tests cover:

- geometry helpers
- traffic-light control behavior
- protocol serialization
- safety checkers
- depot/spawn assumptions
- integrated stepping behavior

## Design Intent

The infrastructure side is designed around a clean separation:

- vehicle logic decides how cars move
- infrastructure logic decides which approaches are green
- infrastructure verification checks whether the resulting transition was legal

This separation is what makes the system suitable for both:

- executable simulation in Python
- formal reasoning about the traffic protocol at the infrastructure level

## Notes

- The package metadata in `infra/pyproject.toml` refers to `README.md`, while
  this repo currently keeps the document as `readme.md`.
- The authoritative behavior description should follow the code paths listed
  above, not older placeholder comments.
