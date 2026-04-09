"""Tests for traffic_vehicles.verifier."""

import pytest
from traffic_infra.geometry import Dir, DirectedEdge, grid_intersections
from traffic_infra.state import CarState, TrafficSignals

from traffic_vehicles.verifier import VGroupVerifier


def _signals(green: Dir = Dir.N) -> TrafficSignals:
    return TrafficSignals(
        green_approach_by_intersection={i: green for i in grid_intersections()}
    )


def _red_signals() -> TrafficSignals:
    return TrafficSignals(
        green_approach_by_intersection={i: None for i in grid_intersections()}
    )


def test_collision_detected():
    verifier = VGroupVerifier()
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    prev = {
        "car_1": CarState("car_1", edge, 5, Dir.E),
        "car_2": CarState("car_2", edge, 4, Dir.E),
    }
    # Both end up at slot 5 → collision
    nxt = {
        "car_1": CarState("car_1", edge, 5, Dir.E),
        "car_2": CarState("car_2", edge, 5, Dir.E),
    }
    report = verifier.check_step(prev, nxt, _signals())
    assert report.collision_count == 1
    assert verifier.collision_count == 1


def test_red_light_violation_detected():
    verifier = VGroupVerifier()
    e1 = DirectedEdge(frm=(0, 0), to=(1, 0))
    e2 = DirectedEdge(frm=(1, 0), to=(2, 0))
    prev = {"car_1": CarState("car_1", e1, 29, Dir.E)}
    nxt = {"car_1": CarState("car_1", e2, 0, Dir.E)}
    # All red → crossing is a red light violation
    report = verifier.check_step(prev, nxt, _red_signals())
    assert report.red_light_violations == 1
    assert verifier.red_light_violations == 1


def test_illegal_direction_detected():
    verifier = VGroupVerifier()
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))  # East edge
    prev = {"car_1": CarState("car_1", edge, 5, Dir.E)}
    # Car claims to drive North on an East edge
    nxt = {"car_1": CarState("car_1", edge, 6, Dir.N)}
    report = verifier.check_step(prev, nxt, _signals())
    assert report.illegal_direction_count == 1
    assert verifier.illegal_direction_count == 1


def test_uturn_detected():
    verifier = VGroupVerifier()
    e1 = DirectedEdge(frm=(0, 0), to=(1, 0))
    e_uturn = DirectedEdge(frm=(1, 0), to=(0, 0))
    prev = {"car_1": CarState("car_1", e1, 29, Dir.E)}
    nxt = {"car_1": CarState("car_1", e_uturn, 0, Dir.W)}
    report = verifier.check_step(prev, nxt, _signals(Dir.W))
    assert report.u_turn_count == 1
    assert verifier.u_turn_count == 1


def test_clean_step_no_violations():
    verifier = VGroupVerifier()
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    prev = {"car_1": CarState("car_1", edge, 5, Dir.E)}
    nxt = {"car_1": CarState("car_1", edge, 6, Dir.E)}
    report = verifier.check_step(prev, nxt, _signals())
    assert report.collision_count == 0
    assert report.red_light_violations == 0
    assert report.illegal_direction_count == 0
    assert report.u_turn_count == 0


def test_verifier_matches_igroup_checks():
    """Results must match i-group evaluate_checks() exactly."""
    from traffic_infra.checks import evaluate_checks
    verifier = VGroupVerifier()
    e1 = DirectedEdge(frm=(0, 0), to=(1, 0))
    e2 = DirectedEdge(frm=(1, 0), to=(2, 0))
    prev = {
        "car_1": CarState("car_1", e1, 29, Dir.E),
        "car_2": CarState("car_2", e1, 10, Dir.E),
    }
    nxt = {
        "car_1": CarState("car_1", e2, 0, Dir.E),
        "car_2": CarState("car_2", e1, 11, Dir.E),
    }
    sig = _red_signals()
    our_report = verifier.check_step(prev, nxt, sig)
    ref_report = evaluate_checks(prev, nxt, sig)
    assert our_report.collision_count == ref_report.collision_count
    assert our_report.red_light_violations == ref_report.red_light_violations
    assert our_report.illegal_direction_count == ref_report.illegal_direction_count
    assert our_report.u_turn_count == ref_report.u_turn_count
    assert our_report.intersection_crossing_violations == ref_report.intersection_crossing_violations


def test_summary_accumulates():
    verifier = VGroupVerifier()
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    prev = {"c": CarState("c", edge, 5, Dir.E)}
    nxt = {"c": CarState("c", edge, 5, Dir.E)}  # stopped
    verifier.check_step(prev, nxt, _signals())
    verifier.check_step(prev, nxt, _signals())
    s = verifier.summary()
    assert s["collision_count"] == 0
