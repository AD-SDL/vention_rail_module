"""Node Config Class for the Vention Rail Node Module."""

from madsci.common.types.node_types import RestNodeConfig

from vention_rail_interface.MachineMotion import DEFAULT_IP


class VentionRailNodeConfig(RestNodeConfig):
    """Configuration for the pf400 node module."""

    rail_ip: str = DEFAULT_IP
    """The IP address of the Vention Rail Controller"""
    speed: float = 10
    """Default speed in mm/s, must be less than 100"""
    acceleration: float = 5
    """Default acceleration, in mm/s^2, must be less than 100"""
    rail_span: float = 1000
    """Default rail span in mm, must be half the true length (for some reason)"""
