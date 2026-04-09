"""Placeholder vehicle motion until v-group integration."""

from __future__ import annotations

from .state import CarState, TrafficSignals


def stub_vehicle_step(
    prev: dict[str, CarState],
    signals: TrafficSignals,
) -> dict[str, CarState]:
    """
    Advances each car one slot along its current edge (ignores signals — demo only).
    `signals` is accepted for API compatibility with a real controller.
    """
    _ = signals
    nxt: dict[str, CarState] = {}
    for cid, c in prev.items():
        if c.slot < 29:
            nxt[cid] = CarState(
                car_id=cid,
                edge=c.edge,
                slot=c.slot + 1,
                driving_dir=c.driving_dir,
            )
        else:
            nxt[cid] = c
    return nxt
