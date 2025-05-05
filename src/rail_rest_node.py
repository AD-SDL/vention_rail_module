"""REST-based node for UR robots"""

from typing import Annotated, Optional

from madsci.common.types.action_types import ActionFailed, ActionSucceeded
from madsci.common.types.location_types import LocationArgument
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from MADSci.src.madsci_common.madsci.common.types.action_types import ActionResult

from vention_rail_interface.rail_interface import RailInterface
from vention_rail_node_config import VentionRailNodeConfig


class VentionRailNode(RestNode):
    """MADSci Rest Node for controlling a Vention Linear Rail"""

    config_model = VentionRailNodeConfig

    def startup_handler(self) -> None:
        """Initialize the Rail Interface"""
        self.rail = RailInterface(config=self.config, logger=self.logger)

    def shutdown_handler(self) -> None:
        """Vention rail shutdown handler."""
        self.rail.disconnect()

    def state_handler(self) -> None:
        """Periodically update the node's state"""
        if self.rail:
            self.node_state["position"] = self.rail.get_position()

    @action
    def home(self) -> ActionResult:
        """Move the robot to home"""
        self.rail.home()
        return ActionSucceeded()

    @action
    def stop(self) -> ActionResult:
        """Stop the Rail"""
        self.rail.stop()
        return ActionSucceeded()

    @action
    def move(
        self,
        position: Annotated[LocationArgument, "Joint position to move to"],
        speed: Annotated[Optional[int], "Speed"] = None,
        acceleration: Annotated[Optional[int], "Acceleration"] = None,
    ) -> ActionResult:
        """Move the robot to a joint position"""
        self.rail.move(
            position=position.location, speed=speed, acceleration=acceleration
        )
        if self.rail.get_position() - position.location < 1:
            return ActionSucceeded()
        return ActionFailed(error="Move Interrupted")

    @action
    def move_relative(
        self,
        distance: Annotated[int, "Distance to move to"],
        speed: Annotated[Optional[int], "Speed"] = None,
        acceleration: Annotated[Optional[int], "Acceleration"] = None,
    ) -> ActionResult:
        """Move the robot to a relative position"""
        self.rail.move_relative(
            distance=distance, speed=speed, acceleration=acceleration
        )
        return ActionSucceeded()

    def safety_stop(self) -> None:
        """Stop the rail immediately"""
        if self.rail:
            return self.rail.estop()
        return False


if __name__ == "__main__":
    vention_rail_node = VentionRailNode()
    vention_rail_node.start_node()
