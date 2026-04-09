"""Tests for traffic_vehicles.network."""

import pytest
from traffic_infra.geometry import Dir, DirectedEdge, directed_edges

from traffic_vehicles.network import (
    TERMINAL_ADJACENCY,
    bfs_shortest_path,
    get_all_edges,
    get_approach_dir,
    get_directed_edge,
    get_neighbors,
    get_turn_type,
    get_valid_next_edges,
)


def test_grid_has_correct_number_of_edges():
    # 3x3 grid: each intersection has up to 4 neighbors.
    # Counting manually: horizontal pairs each direction = 2*3*2 = 12 (E+W each row)
    # vertical pairs = 3*2*2 = 12. Total = 24.
    edges = get_all_edges()
    assert len(edges) == 24


def test_bfs_finds_shortest_path():
    path = bfs_shortest_path((0, 0), (2, 2))
    assert len(path) == 4  # Manhattan distance = 4 steps
    assert path[0].frm == (0, 0)
    assert path[-1].to == (2, 2)


def test_bfs_same_start_end():
    path = bfs_shortest_path((1, 1), (1, 1))
    assert path == []


def test_turn_type_straight():
    assert get_turn_type(Dir.N, Dir.N) == "straight"
    assert get_turn_type(Dir.E, Dir.E) == "straight"


def test_turn_type_left():
    # Travelling N, turning left = W
    assert get_turn_type(Dir.N, Dir.W) == "left"
    assert get_turn_type(Dir.E, Dir.N) == "left"


def test_turn_type_right():
    # Travelling N, turning right = E
    assert get_turn_type(Dir.N, Dir.E) == "right"
    assert get_turn_type(Dir.E, Dir.S) == "right"


def test_turn_type_uturn():
    assert get_turn_type(Dir.N, Dir.S) == "uturn"
    assert get_turn_type(Dir.E, Dir.W) == "uturn"


def test_no_uturn_in_valid_next_edges():
    # From (0,0)→(1,0), U-turn would go (1,0)→(0,0)
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    nexts = get_valid_next_edges(edge)
    for e in nexts:
        assert e.to != (0, 0), "U-turn should be excluded"


def test_terminal_adjacent_intersections():
    assert TERMINAL_ADJACENCY["A"] == (0, 2)
    assert TERMINAL_ADJACENCY["B"] == (0, 0)
    assert TERMINAL_ADJACENCY["C"] == (2, 0)
    assert TERMINAL_ADJACENCY["D"] == (2, 2)


def test_get_neighbors_corner():
    # (0,0) has neighbors (1,0) and (0,1)
    nb = get_neighbors((0, 0))
    assert set(nb) == {(1, 0), (0, 1)}


def test_get_directed_edge():
    e = get_directed_edge((0, 0), (1, 0))
    assert e.frm == (0, 0)
    assert e.to == (1, 0)


def test_approach_dir():
    # Car traveling East (frm=(0,0), to=(1,0)) approaches to-intersection from West
    edge = DirectedEdge(frm=(0, 0), to=(1, 0))
    assert get_approach_dir(edge) == Dir.W
