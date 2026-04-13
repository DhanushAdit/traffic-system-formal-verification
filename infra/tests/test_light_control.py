import unittest

from traffic_infra.geometry import Dir
from traffic_infra.light_control import LightController, cycle_green


class LightControlTests(unittest.TestCase):
    def test_cycle_green_holds_green_for_multiple_steps(self) -> None:
        self.assertEqual(cycle_green(0, green_steps=5, all_red_steps=1), Dir.N)
        self.assertEqual(cycle_green(4, green_steps=5, all_red_steps=1), Dir.N)
        self.assertIsNone(cycle_green(5, green_steps=5, all_red_steps=1))
        self.assertEqual(cycle_green(6, green_steps=5, all_red_steps=1), Dir.W)

    def test_controller_exposes_timing_in_seconds(self) -> None:
        controller = LightController(green_steps=5, all_red_steps=1)
        self.assertEqual(controller.green_seconds, 10)
        self.assertEqual(controller.all_red_seconds, 2)

    def test_default_cycle_matches_perimeter_flow(self) -> None:
        self.assertEqual(cycle_green(0), Dir.N)
        self.assertEqual(cycle_green(15), Dir.W)
        self.assertEqual(cycle_green(30), Dir.S)
        self.assertEqual(cycle_green(45), Dir.E)


if __name__ == "__main__":
    unittest.main()
