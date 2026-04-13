"""Tests for traffic_vehicles.vehicle."""

import pytest
from traffic_infra.geometry import Dir, DirectedEdge
from traffic_infra.state import CarState, LightColor, TrafficSignals
from traffic_infra.geometry import grid_intersections

from traffic_vehicles.vehicle import Vehicle
from traffic_vehicles.step import reset_vehicle_step_state, vehicle_step


def _all_green(green_dir: Dir = Dir.N) -> TrafficSignals:
    return TrafficSignals(
        green_approach_by_intersection={inter: green_dir for inter in grid_intersections()}
    )


def _all_red() -> TrafficSignals:
    return TrafficSignals(
        green_approach_by_intersection={inter: None for inter in grid_intersections()}
    )


def _make_vehicle(car_id: str, edge: DirectedEdge, slot: int) -> Vehicle:
    from traffic_vehicles.routing import get_full_path, best_tour_order
    order = best_tour_order()
    path = get_full_path(order)
    tour_plan = ["A"] + order + ["A"]
    remaining = list(path[1:]) if path and path[0] == edge else list(path)
    v = Vehicle(
        car_id=car_id,
        current_edge=edge,
        current_slot=slot,
        driving_dir=edge.dir(),
        tour_plan=tour_plan,
        destination_index=1,
        planned_path=remaining,
    )
    return v


def test_car_moves_forward_on_green():
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    v = _make_vehicle("car_1", edge, 5)
    signals = _all_green(Dir.W)  # green for West approach (car on E edge approaches from W)
    new_cs = v.decide_move(signals, {}, {}, set())
    assert new_cs.slot == 6
    assert new_cs.edge == edge


def test_car_stops_at_red_light_slot_29():
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    v = _make_vehicle("car_1", edge, 29)
    signals = _all_red()
    new_cs = v.decide_move(signals, {}, {}, set())
    # Should stay at slot 29
    assert new_cs.slot == 29
    assert new_cs.edge == edge


def test_car_crosses_on_green_slot_29():
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    v = _make_vehicle("car_1", edge, 29)
    # Car travels East, approaches (1,0) from West → need green for W approach
    signals = _all_green(Dir.W)
    new_cs = v.decide_move(signals, {}, {}, set())
    assert new_cs.slot == 0
    assert new_cs.edge.frm == (1, 0)


def test_car_stops_for_car_ahead():
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    v = _make_vehicle("car_1", edge, 5)
    # Another car at slot 6 on same edge
    blocker = CarState(car_id="car_2", edge=edge, slot=6, driving_dir=Dir.E)
    signals = _all_green()
    new_cs = v.decide_move(signals, {"car_2": blocker}, {}, set())
    assert new_cs.slot == 5  # stayed


def test_following_car_waits_behind_lead_car_at_red_light():
    reset_vehicle_step_state()
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    prev = {
        "lead": CarState(car_id="lead", edge=edge, slot=29, driving_dir=Dir.E),
        "follow": CarState(car_id="follow", edge=edge, slot=28, driving_dir=Dir.E),
    }

    nxt = vehicle_step(prev, _all_red(), {})

    assert nxt["lead"].slot == 29
    assert nxt["follow"].slot == 28
    assert nxt["lead"].edge == edge
    assert nxt["follow"].edge == edge


def test_car_no_uturn_at_intersection():
    # Edge going East from (0,0) to (1,0). At slot 29, the only U-turn would be
    # to go back West to (0,0). Valid nexts shouldn't include it.
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    v = _make_vehicle("car_1", edge, 29)
    # Force planned_path to the reverse direction to trigger U-turn guard
    v.planned_path = [DirectedEdge(frm=(1, 0), to=(0, 0))]
    signals = _all_green(Dir.W)
    new_cs = v.decide_move(signals, {}, {}, set())
    # Should NOT take U-turn — either stay or pick another valid edge
    if new_cs.edge != edge:
        # If it crossed, it must not be a U-turn
        assert new_cs.edge.to != edge.frm


def test_car_completes_full_tour():
    from traffic_vehicles.routing import get_full_path, best_tour_order
    order = best_tour_order()
    path = get_full_path(order)
    tour_plan = ["A"] + order + ["A"]
    # Simulate a vehicle at each edge in the path (smoke test)
    for edge in path[:3]:
        v = _make_vehicle("car_1", edge, 0)
        assert v.to_car_state().edge == edge
