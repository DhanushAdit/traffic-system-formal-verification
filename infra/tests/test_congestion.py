import unittest

from traffic_infra.congestion import stopped_cars_per_intersection
from traffic_infra.geometry import Dir, DirectedEdge
from traffic_infra.state import CarState


class CongestionTests(unittest.TestCase):
    def test_stopped_car_counted_at_nearer_intersection(self) -> None:
        e = DirectedEdge(frm=(0, 0), to=(1, 0))
        prev = {"a": CarState(car_id="a", edge=e, slot=10, driving_dir=Dir.E)}
        nxt = {"a": CarState(car_id="a", edge=e, slot=10, driving_dir=Dir.E)}
        counts = stopped_cars_per_intersection(prev, nxt)
        self.assertEqual(counts.get((0, 0), 0), 1)
        self.assertEqual(counts.get((1, 0), 0), 0)

    def test_moving_car_not_counted(self) -> None:
        e = DirectedEdge(frm=(0, 0), to=(1, 0))
        prev = {"a": CarState(car_id="a", edge=e, slot=10, driving_dir=Dir.E)}
        nxt = {"a": CarState(car_id="a", edge=e, slot=11, driving_dir=Dir.E)}
        counts = stopped_cars_per_intersection(prev, nxt)
        self.assertEqual(counts, {})


if __name__ == "__main__":
    unittest.main()
