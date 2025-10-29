"""Wrapper Interface for MachineMotion - RailInterface"""

from typing import Any, Optional, Dict
from enum import Enum

from madsci.client.event_client import EventClient

from vention_rail_interface.MachineMotion import MachineMotion

class RailStatus(Enum):
    """Rail status states"""
    IDLE = "IDLE"
    BUSY = "BUSY"
    ESTOP = "ESTOP"
    ERROR = "ERROR"
    NOT_HOMED = "NOT_HOMED"
    UNKNOWN = "UNKNOWN"

class RailInterface:
    """An interface to control Vention Rail over the MachineMotion driver"""

    def __init__(
        self, ip: str, speed: float, acceleration: float, logger: Optional[EventClient] = None
    ) -> "RailInterface":
        """Initialize the RailInterface with a MachineMotion instance."""
        self.rail_ip = ip
        self.rail = None
        self.speed = speed
        self.acceleration = acceleration
        self.rail_span = 1000  # mm, rail span (half the true length, for some reason)

        self.logger = logger if logger else EventClient()
        # Track initialization and homing state
        self._is_initialized = False
        self._is_homed = False
        self._last_error = None

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
            self._last_error = str(e)
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
            self._is_initialized = True
            self._last_error = None
            self.logger.info("Initialization complete.")
        except Exception as e:
            self._is_initialized = False
            self._last_error = str(e)
            self.logger.error(f"Initialization failed: {e}")
            raise e

    def home(self) -> None:
        """Home the rail."""
        try:
            self.speed = 10
            self.acceleration = 5
            self.initialize()
            self.rail.emitHome(axis=1)
            self.rail.waitForMotionCompletion()
            self._is_homed = True
            self._last_error = None
            self.logger.info("Rail Homed.")
        except Exception as e:
            self._is_homed = False
            self._last_error = str(e)
            self.logger.error(f"Failed to home axes: {e}")
            raise e

    def get_estop_state(self) -> Optional[bool]:
        """Get the current emergency stop state.
        
        The estop state is continuously updated by the MachineMotion MQTT client
        in the background, so this method returns the current state at any time.
        
        Returns:
            bool: True if estop is active (triggered)
                  False if estop is not active (released)
                  None if state is unknown or unavailable
        """
        try:
            # The estopStatus attribute is automatically updated by MQTT callbacks
            # in the MachineMotion class, so we can read it at any time
            if self.rail and hasattr(self.rail, 'estopStatus'):
                return self.rail.estopStatus
            else:
                self.logger.warning("Estop status not available - rail not initialized")
                return None
        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Failed to get estop state: {e}")
            return None
        
    def is_moving(self) -> bool:
        """Check if the rail is currently moving.
        
        Returns:
            bool: True if rail is moving, False if motion is complete
        """
        try:
            # isMotionCompleted returns True when NOT moving
            return not self.rail.isMotionCompleted()
        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Failed to check motion status: {e}")
            return False

    def get_status(self) -> RailStatus:
        """Get the comprehensive status of the rail system.
        
        Returns:
            RailStatus: Current status of the rail:
                - IDLE: Initialized, homed, not moving, no errors
                - BUSY: Rail is currently moving
                - ESTOP: Emergency stop is active
                - NOT_HOMED: Rail is initialized but not homed
                - ERROR: System has encountered an error
                - UNKNOWN: Status cannot be determined
        """
        try:
            # Check E-Stop first (highest priority)
            estop_state = self.get_estop_state()
            if estop_state is True:
                return RailStatus.ESTOP
            
            # Check if rail is even initialized/connected
            if not self._is_initialized or self.rail is None:
                return RailStatus.ERROR
            
            # Check for recent errors
            if self._last_error is not None:
                return RailStatus.ERROR
            
            # Check if rail is moving
            if self.is_moving():
                return RailStatus.BUSY
            
            # Check if homed
            if not self._is_homed:
                return RailStatus.NOT_HOMED
            
            # Everything is fine - system is idle
            return RailStatus.IDLE
            
        except Exception as e:
            self.logger.error(f"Failed to get status: {e}")
            self._last_error = str(e)
            return RailStatus.UNKNOWN
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed status information about the rail system.
        
        Returns:
            dict: Detailed status information including:
                - status: Overall status (RailStatus enum)
                - estop_active: E-Stop state
                - is_initialized: Initialization state
                - is_homed: Homing state
                - is_moving: Motion state
                - position: Current position (if available)
                - last_error: Last error message (if any)
        """
        try:
            status = {
                "status": self.get_status().value,
                "estop_active": self.get_estop_state(),
                "is_initialized": self._is_initialized,
                "is_homed": self._is_homed,
                "is_moving": self.is_moving(),
                "position": None,
                "last_error": self._last_error
            }
            
            # Try to get position if system is in good state
            if status["estop_active"] is False and self._is_initialized:
                try:
                    status["position"] = self.get_position()
                except:
                    status["position"] = "unavailable"
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get detailed status: {e}")
            return {
                "status": RailStatus.ERROR.value,
                "estop_active": None,
                "is_initialized": self._is_initialized,
                "is_homed": self._is_homed,
                "is_moving": False,
                "position": None,
                "last_error": str(e)
            }
    
    def clear_error(self) -> None:
        """Clear the last error state."""
        self._last_error = None
        self.logger.info("Error state cleared")

    def get_position(self) -> float:
        """Gets the current position of the rail"""
        try:
            return self.rail.getActualPositions(axis=1)
        except Exception as er:
            self._last_error = str(er)
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
            self._last_error = str(e)
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

    def system_reset(self) -> None:
        """Reset the system."""
        try:
            self.rail.resetSystem()
            self.logger.info("System reset.")
        except Exception as e:
            self.logger.error(f"Failed to reset system: {e}")

# Example of usage
if __name__ == "__main__":
    rail = RailInterface()
    rail.home()
    rail.move(position=100)
    rail.stop()
    rail.estop()
    rail.release_estop()
    rail.disconnect()
