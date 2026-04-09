import unittest

from traffic_infra.geometry import DirectedEdge, Dir, travel_dir


class GeometryTests(unittest.TestCase):
    def test_travel_dir_horizontal_vertical(self) -> None:
        self.assertEqual(travel_dir((0, 0), (1, 0)), Dir.E)
        self.assertEqual(travel_dir((1, 0), (0, 0)), Dir.W)
        self.assertEqual(travel_dir((0, 0), (0, 1)), Dir.N)
        self.assertEqual(travel_dir((0, 1), (0, 0)), Dir.S)

    def test_approach_dir_at_to_intersection(self) -> None:
        edge = DirectedEdge(frm=(0, 0), to=(1, 0))
        self.assertEqual(edge.approach_dir_at_to_intersection(), Dir.W)


if __name__ == "__main__":
    unittest.main()
