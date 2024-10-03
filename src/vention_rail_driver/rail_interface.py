"""Wrapper Interface for MachineMotion - RailInterface"""

from MachineMotion import DEFAULT_IP, MachineMotion


class RailInterface:
    """An interface to control Vention Rail over the MachineMotion driver"""

    def __init__(self, hostname=DEFAULT_IP):
        """Initialize the RailInterface with a MachineMotion instance."""
        self.hostname = hostname
        self.rail = None
        self.speed = 50  # mm/s, must be less than 100
        self.acceleration = 25  # mm/s^2, must be less than 100
        self.rail_span = 500  # mm, rail span

        self.connect()
        self.initialize()

    def connect(self):
        """Connect to the Rail"""
        try:
            # Establish connection logic (if applicable)
            self.rail = MachineMotion(self.hostname, self.templateCallback)
            print("Connected to the Vention Rail.")
        except Exception as e:
            print(f"Failed to connect: {e}")

    def templateCallback(self, data):
        "Templete Callback"
        self.g = data
        if self.verbose:
            print("gCode %s" % data)

    def disconnect(self):
        """Disconnect from the Rail"""
        try:
            self.rail.myMqttClient.loop_stop()
            self.rail.myMqttClient.disconnect()
            print("Disconnected from the Rail")
        except Exception as e:
            print(f"Failed to disconnect: {e}")

    def initialize(self):
        """Initialize the Rail system (configurations or setup)."""
        try:
            # Placeholder for any initialization logic
            self.rail.emitSpeed(speed=self.speed)
            self.rail.emitAcceleration(acceleration=self.acceleration)
            print("Initialization complete.")
        except Exception as e:
            print(f"Initialization failed: {e}")

    def home(self):
        """Home the rail."""
        try:
            self.rail.emitHome(axis=1)
            self.rail.waitForMotionCompletion()
            print("Rail Homed.")
        except Exception as e:
            print(f"Failed to home axes: {e}")

    def get_position(self):
        """Gets the current position of the rail"""
        try:
            cur_pos = self.rail.getActualPositions(axis=1)
            return cur_pos
        except Exception as er:
            print(f"Failed to get the current position: {er}")

    def move(self, position: float, speed: int = None, acceleration: int = None):
        """Move the rail to a desired position."""
        try:
            if speed or acceleration:
                self.speed = speed
                self.acceleration = acceleration
                self.initialize()
            if position < 0 or position > self.rail_span:
                print("Position must be in 0-500 range")
                return
            self.rail.moveToPosition(axis=1, position=position)
            self.rail.waitForMotionCompletion()
            print(f"Rail moved to position the {position}.")
        except Exception as e:
            print(f"Failed to move the rail: {e}")

    def move_relative(self, distance, speed: int = None, acceleration: int = None):
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
            print(er)

    def stop(self):
        """Stop all motion."""
        try:
            self.rail.stopAllMotion()
            print("All motion stopped.")
        except Exception as e:
            print(f"Failed to stop motion: {e}")

    def estop(self):
        """Trigger emergency stop."""
        try:
            self.rail.triggerEstop()
            print("Emergency stop triggered.")
        except Exception as e:
            print(f"Failed to trigger emergency stop: {e}")

    def release_estop(self):
        """Release emergency stop."""
        try:
            self.rail.releaseEstop()
            print("Emergency stop released.")
        except Exception as e:
            print(f"Failed to release emergency stop: {e}")


# Example of usage
if __name__ == "__main__":
    rail = RailInterface()
    rail.home()
    rail.move(position=100)
    rail.stop()
    rail.estop()
    rail.release_estop()
    rail.disconnect()
