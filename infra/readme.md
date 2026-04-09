A formal verification project for a simplified traffic system with a 3×3 grid road network.

## Current focus (i-group / infrastructure, Python)
For now we implement only the infrastructure side:
- Discrete road + slot geometry for mapping car positions onto the model.
- A traffic signal model (green/red only, at most one green per intersection).
- Safety checkers that i-group must report:
  - collision count (multiple cars in the same slot)
  - red-light violations (car crosses intersection on a red light)
  - illegal opposite-direction lane running
  - U-turn count

The vehicle (v-group) integration is intentionally deferred. The infrastructure code is written so it can later accept real vehicle transitions; for the moment the simulator API expects explicit `CarState` before/after positions.

## Repo contents (growing over time)
You will see these modules added:
- `traffic_infra/geometry.py`: grid, directed edges, slots
- `traffic_infra/state.py`: data structures (car state, lights, transitions)
- `traffic_infra/checks.py`: property evaluation + reporting
- `traffic_infra/light_control.py`: light constraint logic
- `traffic_infra/igroupsim.py`: i-group simulator loop (placeholder policy)
- `traffic_infra/congestion.py`: stopped cars per intersection (for v-group congestion)
- `traffic_infra/protocol.py`: JSON helpers for `CarState` / `TrafficSignals`
- `traffic_infra/simulation.py`: `InfraSimulation` orchestration + cumulative metrics
- `tests/`: unit tests for geometry, checkers, congestion, protocol

Run a stub demo: `python -m traffic_infra` or `traffic-infra --steps 5`

### Local real-time web UI
On Linux distributions that block system-wide `pip` (PEP 668), use a **virtual environment** in the repo:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[web]"
```

Start the server: `python -m traffic_infra.web_app` or `traffic-infra-web`.

Open **http://127.0.0.1:8765** in a browser — use **Step** / **Auto step** to advance the stub simulation; the canvas shows the grid, cars, and per-intersection green directions.

If **port 8765 is already in use**, stop the old server (the terminal where it is running: Ctrl+C), or run on another port: `python -m traffic_infra.web_app --port 8766` and open that URL instead.

**One-shot script (from repo root):** `./run_simulation.sh` — picks a venv under `/tmp/traffic-system-formal-venv` or `~/venvs/traffic-system-formal-venv` (or `TRAFFIC_VENV`), starts the web UI, and tries to open the browser. Use `PORT=8766 ./run_simulation.sh` if 8765 is busy. Terminal-only stub: `./run_simulation.sh --cli --steps 20`.
