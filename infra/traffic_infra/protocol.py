from __future__ import annotations

import json
from typing import Any

from .geometry import Dir, DirectedEdge, Intersection
from .state import CarState, TrafficSignals


def _edge_to_json(e: DirectedEdge) -> dict[str, Any]:
    return {"frm": list(e.frm), "to": list(e.to)}


def _edge_from_json(d: dict[str, Any]) -> DirectedEdge:
    frm = tuple(d["frm"])
    to = tuple(d["to"])
    if len(frm) != 2 or len(to) != 2:
        raise ValueError("frm/to must be length-2 tuples")
    return DirectedEdge(frm=(int(frm[0]), int(frm[1])), to=(int(to[0]), int(to[1])))


def car_state_to_json(c: CarState) -> dict[str, Any]:
    return {
        "car_id": c.car_id,
        "edge": _edge_to_json(c.edge),
        "slot": c.slot,
        "driving_dir": c.driving_dir.value,
    }


def car_state_from_json(d: dict[str, Any]) -> CarState:
    return CarState(
        car_id=str(d["car_id"]),
        edge=_edge_from_json(d["edge"]),
        slot=int(d["slot"]),
        driving_dir=Dir(str(d["driving_dir"])),
    )


def traffic_signals_to_json(s: TrafficSignals) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for inter, g in s.green_approach_by_intersection.items():
        key = f"{inter[0]},{inter[1]}"
        out[key] = None if g is None else g.value
    return {"green_approach_by_intersection": out}


def traffic_signals_from_json(d: dict[str, Any]) -> TrafficSignals:
    raw = d["green_approach_by_intersection"]
    mapping: dict[Intersection, Dir | None] = {}
    for key, val in raw.items():
        parts = key.split(",")
        inter = (int(parts[0]), int(parts[1]))
        if val is None:
            mapping[inter] = None
        else:
            mapping[inter] = Dir(str(val))
    return TrafficSignals(green_approach_by_intersection=mapping)


def dumps_car_states(cars: dict[str, CarState]) -> str:
    return json.dumps({cid: car_state_to_json(c) for cid, c in cars.items()}, sort_keys=True)


def loads_car_states(s: str) -> dict[str, CarState]:
    data = json.loads(s)
    return {cid: car_state_from_json(obj) for cid, obj in data.items()}
