"""Base module tests."""

import unittest


class TestModule_Base(unittest.TestCase):
    """Base test class for this module."""

    pass


class TestImports(TestModule_Base):
    """Test the imports of the module are working correctly"""

    # @patch("sys.argv", ["test", "--ur_ip", "164.54.116.129"])
    def test_driver_import(self):
        """Test the driver and rest node imports"""
        import rail_rest_node
        import vention_rail_driver

        assert vention_rail_driver
        assert rail_rest_node


if __name__ == "__main__":
    unittest.main()
