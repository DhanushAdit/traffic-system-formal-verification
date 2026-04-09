"""Thin wrappers around i-group protocol functions."""

from __future__ import annotations

import json

from traffic_infra.geometry import Intersection
from traffic_infra.protocol import (
    car_state_to_json,
    dumps_car_states,
    loads_car_states,
    traffic_signals_from_json,
    traffic_signals_to_json,
)
from traffic_infra.state import CarState, TrafficSignals


def send_vehicle_states(cars: dict[str, CarState]) -> str:
    return dumps_car_states(cars)


def receive_signals(json_str: str) -> TrafficSignals:
    return traffic_signals_from_json(json.loads(json_str))


def receive_congestion(json_str: str) -> dict[Intersection, int]:
    raw: dict[str, int] = json.loads(json_str)
    result: dict[Intersection, int] = {}
    for key, count in raw.items():
        x, y = key.split(",")
        result[(int(x), int(y))] = count
    return result


def send_congestion_request() -> str:
    return json.dumps({"request": "congestion"})
