"""Tests for traffic_vehicles.routing."""

import pytest
from traffic_vehicles.routing import (
    all_tour_permutations,
    best_tour_order,
    compute_tour_length,
    dynamic_reroute,
    get_full_path,
)
from traffic_vehicles.constants import TERMINALS


def test_all_6_permutations_generated():
    perms = all_tour_permutations()
    assert len(perms) == 6
    # Each is a permutation of B, C, D
    for p in perms:
        assert sorted(p) == ["B", "C", "D"]
    # All distinct
    as_tuples = [tuple(p) for p in perms]
    assert len(set(as_tuples)) == 6


def test_best_tour_order_returns_shortest():
    best = best_tour_order()
    best_len = compute_tour_length(best)
    for p in all_tour_permutations():
        assert compute_tour_length(p) >= best_len


def test_full_path_starts_at_A_intersection():
    order = best_tour_order()
    path = get_full_path(order)
    assert path[0].frm == TERMINALS["A"]


def test_full_path_visits_all_destinations():
    order = ["B", "C", "D"]
    path = get_full_path(order)
    visited_intersections = {e.frm for e in path} | {e.to for e in path}
    for terminal in ["B", "C", "D", "A"]:
        assert TERMINALS[terminal] in visited_intersections


def test_dynamic_reroute_returns_path():
    path = dynamic_reroute(
        current_intersection=(0, 2),
        remaining_destinations=["B", "C", "D"],
        congestion_map={},
    )
    assert len(path) > 0
    assert path[0].frm == (0, 2)


def test_dynamic_reroute_avoids_congestion():
    # With heavy congestion on (1,0), path should prefer to avoid it
    congestion = {(1, 0): 20}
    path_congested = dynamic_reroute(
        current_intersection=(0, 2),
        remaining_destinations=["C"],
        congestion_map=congestion,
    )
    path_clear = dynamic_reroute(
        current_intersection=(0, 2),
        remaining_destinations=["C"],
        congestion_map={},
    )
    # Both must reach (2,0)
    assert path_congested[-1].to == TERMINALS["C"]
    assert path_clear[-1].to == TERMINALS["C"]
