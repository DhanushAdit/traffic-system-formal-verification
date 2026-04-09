import json
import unittest

from traffic_infra.geometry import Dir, DirectedEdge
from traffic_infra.protocol import (
    car_state_from_json,
    car_state_to_json,
    dumps_car_states,
    loads_car_states,
    traffic_signals_from_json,
    traffic_signals_to_json,
)
from traffic_infra.state import CarState, TrafficSignals


class ProtocolTests(unittest.TestCase):
    def test_car_state_roundtrip(self) -> None:
        c = CarState(
            car_id="x",
            edge=DirectedEdge(frm=(0, 0), to=(1, 0)),
            slot=3,
            driving_dir=Dir.E,
        )
        d = car_state_to_json(c)
        self.assertEqual(car_state_from_json(d), c)

    def test_traffic_signals_roundtrip(self) -> None:
        s = TrafficSignals(green_approach_by_intersection={(1, 0): Dir.N, (0, 0): None})
        d = traffic_signals_to_json(s)
        self.assertEqual(traffic_signals_from_json(d), s)

    def test_dumps_loads_car_states(self) -> None:
        cars = {
            "a": CarState(
                car_id="a",
                edge=DirectedEdge(frm=(0, 0), to=(0, 1)),
                slot=0,
                driving_dir=Dir.N,
            )
        }
        s = dumps_car_states(cars)
        json.loads(s)
        self.assertEqual(loads_car_states(s), cars)


if __name__ == "__main__":
    unittest.main()
