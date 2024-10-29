"""REST-based node for UR robots"""

from pathlib import Path

from fastapi.datastructures import State
from typing_extensions import Annotated
from vention_rail_driver.rail_interface import RailInterface
from wei.modules.rest_module import RESTModule
from wei.types.module_types import ModuleState, ModuleStatus
from wei.types.step_types import ActionRequest, StepResponse
from wei.utils import extract_version

rest_module = RESTModule(
    name="vention_rail_node",
    version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
    description="A node to control the vention rail",
    model="vention_rail",
)
rest_module.arg_parser.add_argument(
    "--rail_ip",
    type=str,
    default="192.168.7.2",
    help="Hostname or IP address to connect to Vention Rail",
)


@rest_module.startup()
def ur_startup(state: State):
    """UR startup handler."""
    state.rail = None
    state.rail = RailInterface(hostname=state.rail_ip)
    print("Vention Rail is online")


@rest_module.shutdown()
def rail_shutdown(state: State):
    """Vention rail shutdown handler."""
    state.rail.disconnect()
    print("Rail offline")



@rest_module.action()
def home(
    state: State,
    action: ActionRequest,
) -> StepResponse:
    """Move the robot to a joint position"""
    state.rail.home()
    return StepResponse.step_succeeded()


@rest_module.action()
def stop(
    state: State,
    action: ActionRequest,
) -> StepResponse:
    """Move the robot to a joint position"""
    state.rail.stop()
    return StepResponse.step_succeeded()


@rest_module.action()
def move(
    state: State,
    action: ActionRequest,
    position: Annotated[float, "Joint position to move to"],
    speed: Annotated[int, "Acceleration"] = None,
    acceleration: Annotated[int, "Velocity"] = None,
) -> StepResponse:
    """Move the robot to a joint position"""
    state.rail.move(position=position, speed=speed, acceleration=acceleration)
    if state.rail.get_position() == position:
        return StepResponse.step_succeeded()
    else:
        return StepResponse.step_failed(error="Move Interrupted")

@rest_module.action()
def move_relative(
    state: State,
    action: ActionRequest,
    distance: Annotated[int, "Distance to move to"],
    speed: Annotated[int, "Acceleration"] = None,
    acceleration: Annotated[int, "Velocity"] = None,
) -> StepResponse:
    """Move the robot to a joint position"""
    state.rail.move_relative(distance=distance, speed=speed, acceleration=acceleration)
    return StepResponse.step_succeeded()


if __name__ == "__main__":
    rest_module.start()
