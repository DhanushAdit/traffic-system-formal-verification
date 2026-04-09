import unittest

from traffic_infra.checks import evaluate_checks
from traffic_infra.geometry import Dir, DirectedEdge
from traffic_infra.state import CarState, TrafficSignals


class ChecksTests(unittest.TestCase):
    def test_red_light_violation_on_crossing(self) -> None:
        prev = CarState(
            car_id="c1",
            edge=DirectedEdge(frm=(0, 0), to=(1, 0)),
            slot=29,
            driving_dir=Dir.E,
        )
        nxt = CarState(
            car_id="c1",
            edge=DirectedEdge(frm=(1, 0), to=(2, 0)),
            slot=0,
            driving_dir=Dir.E,
        )
        signals = TrafficSignals(green_approach_by_intersection={(1, 0): Dir.N})
        report = evaluate_checks(prev_cars={"c1": prev}, next_cars={"c1": nxt}, signals=signals)
        self.assertEqual(report.red_light_violations, 1)

    def test_collision_count_two_cars_same_slot(self) -> None:
        e = DirectedEdge(frm=(0, 0), to=(1, 0))
        next_cars = {
            "c1": CarState(car_id="c1", edge=e, slot=5, driving_dir=Dir.E),
            "c2": CarState(car_id="c2", edge=e, slot=5, driving_dir=Dir.E),
        }
        signals = TrafficSignals(green_approach_by_intersection={})
        report = evaluate_checks(prev_cars={}, next_cars=next_cars, signals=signals)
        self.assertEqual(report.collision_count, 1)

    def test_illegal_direction_count_on_next_state(self) -> None:
        e = DirectedEdge(frm=(0, 0), to=(1, 0))
        prev = {"c1": CarState(car_id="c1", edge=e, slot=10, driving_dir=Dir.W)}
        nxt = {"c1": CarState(car_id="c1", edge=e, slot=11, driving_dir=Dir.W)}
        signals = TrafficSignals(green_approach_by_intersection={})
        report = evaluate_checks(prev_cars=prev, next_cars=nxt, signals=signals)
        self.assertEqual(report.illegal_direction_count, 1)

    def test_u_turn_count(self) -> None:
        prev = CarState(
            car_id="c1",
            edge=DirectedEdge(frm=(0, 0), to=(1, 0)),
            slot=29,
            driving_dir=Dir.E,
        )
        nxt = CarState(
            car_id="c1",
            edge=DirectedEdge(frm=(1, 0), to=(0, 0)),
            slot=0,
            driving_dir=Dir.W,
        )
        signals = TrafficSignals(green_approach_by_intersection={})
        report = evaluate_checks(prev_cars={"c1": prev}, next_cars={"c1": nxt}, signals=signals)
        self.assertEqual(report.u_turn_count, 1)


if __name__ == "__main__":
    unittest.main()
