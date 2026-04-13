"""Integration checks for the combined infra + vehicle runtime."""

from traffic_infra.integrated_simulation import IntegratedSimulation
from traffic_infra.viz_session import VizSimulationSession
from traffic_vehicles.simulation import VGroupSimulation


def test_integrated_simulation_moves_cars_without_violations():
    sim = IntegratedSimulation(spawn_interval=0, num_initial_cars=1)

    first = sim.step()
    second = sim.step()

    assert first.current_cars
    assert second.current_cars
    assert sim.sim.cumulative.collision_count == 0
    assert sim.sim.cumulative.red_light_violations == 0
    assert sim.sim.cumulative.illegal_direction_count == 0
    assert sim.sim.cumulative.u_turn_count == 0
    assert sim.sim.cumulative.intersection_crossing_violations == 0


def test_integrated_simulation_can_seed_multiple_cars():
    sim = IntegratedSimulation(spawn_interval=0, num_initial_cars=3)

    assert len(sim.current_cars()) == 3
    assert sim.throughput_per_minute() == 0.0


def test_completed_car_stays_visible_in_arrival_snapshot():
    sim = IntegratedSimulation(spawn_interval=0, num_initial_cars=1)
    car_id, vehicle = next(iter(sim.fleet.vehicles.items()))
    final_edge = vehicle.planned_path[-1]
    vehicle.current_edge = final_edge
    vehicle.current_slot = 29
    vehicle.driving_dir = final_edge.dir()
    vehicle.destination_index = len(vehicle.tour_plan) - 1
    vehicle.planned_path = []

    result = sim.step()

    assert car_id in result.current_cars


def test_steps_for_two_hours():
    assert VGroupSimulation.steps_for_hours(2.0) == 3600


def test_viz_session_uses_integrated_runtime_when_available():
    session = VizSimulationSession()

    state = session.reset()
    stepped = session.step()

    assert state["cars"]
    assert stepped["cars"]
    assert stepped["signals"] is not None
    assert stepped["last_report"] is not None
