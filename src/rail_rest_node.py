"""REST-based node for UR robots"""

from typing import Annotated, Optional

from madsci.common.types.action_types import ActionFailed
from madsci.common.types.admin_command_types import AdminCommandResponse
from madsci.common.types.location_types import LocationArgument
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from vention_rail_interface.rail_interface import RailInterface, RailStatus

from madsci.common.types.node_types import RestNodeConfig

from vention_rail_interface.MachineMotion import DEFAULT_IP


class VentionRailNodeConfig(RestNodeConfig):
    """Node Config Class for the Vention Rail Node Module."""

    rail_ip: Optional[str] = DEFAULT_IP
    """The IP address of the Vention Rail Controller"""
    speed: float = 10
    """Default speed in mm/s, must be less than 100"""
    acceleration: float = 5
    """Default acceleration, in mm/s^2, must be less than 100"""
    rail_span: float = 1000
    """Default rail span in mm, must be half the true length (for some reason)"""

class VentionRailNode(RestNode):
    """MADSci Rest Node for controlling a Vention Linear Rail"""
    rail_interface: RailInterface = None
    config: VentionRailNodeConfig = VentionRailNodeConfig()
    config_model = VentionRailNodeConfig

    def startup_handler(self) -> None:
        """Initialize the Rail Interface"""
        try:
            self.logger.log("Node initializing")
            self.rail_interface = RailInterface(ip=self.config.rail_ip, speed=self.config.speed, acceleration=self.config.acceleration, logger=self.logger)
        except Exception as e:
            self.logger.log_error(f"Failed to initialize Rail Interface: {e}")
            self.startup_has_run = False
        else:
            self.startup_has_run = True
            self.logger.log("Vention Rail node initialized!")

    def shutdown_handler(self) -> None:
        """Vention rail shutdown handler."""
        try:
            self.logger.log("Shutting down")
            self.rail_interface.disconnect()
            self.shutdown_has_run = True
            del self.rail_interface
            self.rail_interface = None
            self.logger.log("Shutdown complete.")
        except Exception as e:
            self.logger.log_error(f"Failed to shutdown Rail Interface: {e}")

    def state_handler(self) -> None:
        """Periodically update the node's state"""
        if self.rail_interface is None:
            self.logger.log_error("Rail interface is not initialized")
            self.node_state = {
                "rail_status_code": "NOT_INITIALIZED",
                "current_position": None,
                "estop_active": None,
                "is_homed": False,
                "is_moving": False,
            }
            return
        
        # Get comprehensive status from rail interface
        detailed_status = self.rail_interface.get_detailed_status()
        
        # Update node state with all relevant information
        self.node_state = {
            "rail_status_code": detailed_status["status"],
            "current_position": detailed_status["position"],
            "estop_active": detailed_status["estop_active"],
            "is_homed": detailed_status["is_homed"],
            "is_moving": detailed_status["is_moving"],
        }
        
        # Log status changes or important states
        status = self.rail_interface.get_status()
        if status == RailStatus.ESTOP:
            self.logger.log_error("E-STOP is active")
        elif status == RailStatus.ERROR:
            self.logger.log_error(f"ERROR: {detailed_status['last_error']}")
        elif status == RailStatus.NOT_HOMED:
            self.logger.log_warning("Rail is not HOMED")

    @action
    def home(self):
        """Move the robot to home"""
        self.rail_interface.home()
        return 

    @action
    def stop(self):
        """Stop the Rail"""
        self.rail_interface.stop()
        return 

    @action
    def move(
        self,
        position: Annotated[LocationArgument, "Joint position to move to"],
        speed: Annotated[Optional[int], "Speed"] = None,
        acceleration: Annotated[Optional[int], "Acceleration"] = None,
    ):
        """Move the robot to a joint position"""
        self.rail_interface.move(
            position=position.location, speed=speed, acceleration=acceleration
        )
        if self.rail_interface.get_position() - position.location < 1:
            return 
        return ActionFailed(error="Move Interrupted")

    @action
    def move_relative(
        self,
        distance: Annotated[int, "Distance to move to"],
        speed: Annotated[Optional[int], "Speed"] = None,
        acceleration: Annotated[Optional[int], "Acceleration"] = None,
    ):
        """Move the robot to a relative position"""
        self.rail_interface.move_relative(
            distance=distance, speed=speed, acceleration=acceleration
        )
        return 

    def safety_stop(self) -> AdminCommandResponse:
        """Stop the rail immediately"""
        if self.rail_interface:
            self.logger.log_error("Emergency stop activated")
            self.rail_interface.estop()
            return AdminCommandResponse(success=True)
        return AdminCommandResponse(success=False)
    
    def estop_clear(self) -> AdminCommandResponse:
        """Clear the emergency stop"""
        if self.rail_interface:
            self.logger.log("Clearing emergency stop...")
            self.rail_interface.release_estop()
            self.logger.log("Emergency stop cleared.")
            return AdminCommandResponse(success=True)
        return AdminCommandResponse(success=False)
    
    def reset(self) -> AdminCommandResponse:
        """Reset the Vention Rail"""
        self.logger.log("Resetting node...")
        self.rail_interface.system_reset()
        result = super().reset()
        self.logger.log("Node reset.")
        return result

if __name__ == "__main__":
    vention_rail_node = VentionRailNode()
    vention_rail_node.start_node()
