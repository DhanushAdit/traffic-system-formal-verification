"""Tests for traffic_vehicles.fleet."""

import pytest
from traffic_infra.geometry import Dir, DirectedEdge
from traffic_infra.state import CarState

from traffic_vehicles.fleet import Fleet, _get_spawn_edge


def test_spawn_car_at_A():
    fleet = Fleet()
    spawn_edge = _get_spawn_edge()
    car_id = fleet.spawn_car()
    assert car_id is not None
    assert car_id in fleet.vehicles
    v = fleet.vehicles[car_id]
    assert v.current_edge == spawn_edge
    assert v.current_slot == 0


def test_no_spawn_when_A_occupied():
    fleet = Fleet()
    id1 = fleet.spawn_car()
    # Slot 0 is occupied — should not spawn another
    id2 = fleet.spawn_car()
    assert id2 is None


def test_throughput_calculation():
    fleet = Fleet()
    fleet.completed_tours = 10
    # 900 steps * 2s = 1800s = 0.5 hour → 10 / 0.5 = 20.0
    result = fleet.throughput_per_hour(900)
    assert abs(result - 20.0) < 1e-6


def test_throughput_zero_steps():
    fleet = Fleet()
    assert fleet.throughput_per_hour(0) == 0.0


def test_multi_car_spawn():
    fleet = Fleet()
    spawn_edge = _get_spawn_edge()
    id1 = fleet.spawn_car()
    # Manually move first car off slot 0
    v = fleet.vehicles[id1]
    v.current_slot = 5
    id2 = fleet.spawn_car()
    assert id2 is not None
    assert id2 != id1


def test_congestion_update():
    fleet = Fleet()
    fleet.update_congestion({(0, 0): 3, (1, 1): 1})
    assert fleet.congestion_map == {(0, 0): 3, (1, 1): 1}


def test_get_all_car_states():
    fleet = Fleet()
    fleet.spawn_car()
    states = fleet.get_all_car_states()
    assert len(states) == 1
    for cid, cs in states.items():
        assert cs.car_id == cid


def test_apply_next_states_updates_vehicle():
    fleet = Fleet()
    spawn_edge = _get_spawn_edge()
    car_id = fleet.spawn_car()
    v = fleet.vehicles[car_id]
    # Move car to slot 5
    new_state = CarState(car_id=car_id, edge=spawn_edge, slot=5, driving_dir=spawn_edge.dir())
    fleet.apply_next_states({car_id: new_state})
    assert fleet.vehicles[car_id].current_slot == 5
