"""Wrapper Interface for MachineMotion - RailInterface"""

from typing import Any, Optional

from madsci.client.event_client import EventClient

from vention_rail_interface.MachineMotion import MachineMotion
from vention_rail_node_config import VentionRailNodeConfig


class RailInterface:
    """An interface to control Vention Rail over the MachineMotion driver"""

    def __init__(
        self, config: VentionRailNodeConfig, logger: Optional[EventClient] = None
    ) -> "RailInterface":
        """Initialize the RailInterface with a MachineMotion instance."""
        self.rail_ip = config.rail_ip
        self.rail = None
        self.speed = config.speed
        self.acceleration = config.acceleration
        self.rail_span = 1000  # mm, rail span (half the true length, for some reason)

        self.logger = logger if logger else EventClient()

        self.connect()
        self.initialize()

    def connect(self) -> None:
        """Connect to the Rail"""
        try:
            # Establish connection logic (if applicable)
            self.rail = MachineMotion(self.rail_ip, self.gcode_callback)
            self.logger.info("Connected to the Vention Rail.")
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise e

    def gcode_callback(self, data: Any) -> None:
        """Template gcode Callback"""
        self.gcode = data

    def disconnect(self) -> None:
        """Disconnect from the Rail"""
        try:
            self.rail.myMqttClient.loop_stop()
            self.rail.myMqttClient.disconnect()
            self.logger.info("Disconnected from the Rail")
        except Exception as e:
            self.logger.error(f"Failed to disconnect: {e}")

    def initialize(self) -> None:
        """Initialize the Rail system (configurations or setup)."""
        try:
            # Placeholder for any initialization logic
            self.rail.emitSpeed(speed=self.speed)
            self.rail.emitAcceleration(acceleration=self.acceleration)
            self.logger.info("Initialization complete.")
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")

    def home(self) -> None:
        """Home the rail."""
        try:
            self.speed = 10
            self.acceleration = 5
            self.initialize()
            self.rail.emitHome(axis=1)
            self.rail.waitForMotionCompletion()
            self.logger.info("Rail Homed.")
        except Exception as e:
            self.logger.error(f"Failed to home axes: {e}")

    def get_position(self) -> float:
        """Gets the current position of the rail"""
        try:
            return self.rail.getActualPositions(axis=1)
        except Exception as er:
            self.logger.error(f"Failed to get the current position: {er}")

    def move(
        self,
        position: float,
        speed: Optional[int] = None,
        acceleration: Optional[int] = None,
    ) -> None:
        """Move the rail to a desired position."""
        try:
            if speed or acceleration:
                self.speed = speed
                self.acceleration = acceleration
                self.initialize()
            if position < 0 or position > self.rail_span:
                self.logger.warning("Position must be in 0-500 range")
                return
            self.rail.moveToPosition(axis=1, position=position)
            self.rail.waitForMotionCompletion()
            self.logger.info(f"Rail moved to position {position}.")
        except Exception as e:
            self.logger.error(f"Failed to move the rail: {e}")

    def move_relative(
        self,
        distance: float,
        speed: Optional[int] = None,
        acceleration: Optional[int] = None,
    ) -> float:
        """Moves the rail to relative distance"""
        try:
            if speed or acceleration:
                self.speed = speed
                self.acceleration = acceleration
                self.initialize()
            distance *= 2  # Don't know why this was multiplied in the original tests
            if distance > 0:
                self.rail.emitRelativeMove(1, "positive", distance)
            else:
                self.rail.emitRelativeMove(1, "negative", -distance)
            self.rail.waitForMotionCompletion()
            return self.get_position()
        except Exception as er:
            self.logger.error(er)

    def stop(self) -> bool:
        """Stop all motion."""
        try:
            self.rail.stopAllMotion()
            self.logger.info("All motion stopped.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop motion: {e}")
            return False

    def estop(self) -> None:
        """Trigger emergency stop."""
        try:
            self.rail.triggerEstop()
            self.logger.info("Emergency stop triggered.")
        except Exception as e:
            self.logger.error(f"Failed to trigger emergency stop: {e}")

    def release_estop(self) -> None:
        """Release emergency stop."""
        try:
            self.rail.releaseEstop()
            self.logger.info("Emergency stop released.")
        except Exception as e:
            self.logger.error(f"Failed to release emergency stop: {e}")


# Example of usage
if __name__ == "__main__":
    rail = RailInterface()
    rail.home()
    rail.move(position=100)
    rail.stop()
    rail.estop()
    rail.release_estop()
    rail.disconnect()
