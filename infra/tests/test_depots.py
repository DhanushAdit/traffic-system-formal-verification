"""Depot / start layout from project PDF."""

from traffic_infra.depots import (
    DEPOT_ADJACENT_INTERSECTION,
    assert_valid_start_state,
    depots_to_json,
    first_road_edge_leaving_start,
    initial_car_from_depot_a,
)


def test_first_segment_from_a_toward_b():
    edge = first_road_edge_leaving_start()
    assert edge.frm == (0, 0)
    assert edge.to == (0, 1)


def test_initial_car_validated():
    cs = initial_car_from_depot_a()
    assert_valid_start_state(cs)
    assert cs.slot == 0


def test_depots_json_has_start_and_destinations():
    js = depots_to_json()
    roles = {d["label"]: d["role"] for d in js}
    assert roles["A"] == "start"
    assert roles["B"] == roles["C"] == roles["D"] == "destination"
    a = next(x for x in js if x["label"] == "A")
    assert a["adj"] == [0, 0]
    assert a["kind"] == "start_square"
    assert a["outward"] == "W"
    assert "box" in a
    b = next(x for x in js if x["label"] == "B")
    assert b["kind"] == "corner_label"
    assert b["adj"] == [0, 2]
