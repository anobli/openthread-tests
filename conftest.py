# Copyright (c) 2025 Alexandre Bailon
#
# SPDX-License-Identifier: Apache-2.0

"""
Pytest configuration and fixtures for OpenThread testing.
"""
import logging
import os
from typing import List, Generator
import pytest
import otci

import yaml
try:
    # Use the C LibYAML parser if available, rather than the Python parser.
    # It's much faster.
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from otci.command_handlers import OtCliCommandRunner
from openthread_tests.otci import ZephyrOTCI
from openthread_tests.command_handlers import OtCliZephyr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Read device paths from environment or use defaults for testing
DEFAULT_DEVICES = ["/dev/ttyUSB0", "/dev/ttyUSB1"]


@pytest.fixture()
def ot_hardware_map(request):
    return request.config.getoption('--ot-hardware-map')


@pytest.fixture()
def otbr_test_values(ot_hardware_map):
    if ot_hardware_map:
        with open(ot_hardware_map) as yaml_file:
            hwm = yaml.load(yaml_file, Loader=SafeLoader)
            if hwm:
                hwm.sort(key=lambda x: x.get('id', ''))

            # FIXME: This returns the first one for the moment
            for h in hwm:
                return h['otbr']

    return None


def pytest_addoption(parser):
    """Add OpenThread specific command line options to pytest."""
    parser.addoption(
        "--ot-devices",
        action="store",
        default="",
        help="Comma-separated list of OpenThread RCP/NCP device paths (e.g. /dev/ttyUSB0,/dev/ttyUSB1)"
    )
    parser.addoption('--ot-hardware-map')


def get_test_devices(request) -> List[str]:
    """
    Get list of device paths from environment variable or command line.

    Args:
        request: Optional pytest request object
    """

    # First check command line argument (highest priority)
    devices_from_option = None
    if request is not None:
        try:
            devices_from_option = request.config.getoption("--ot-devices")
        except (AttributeError, RuntimeError):
            pass

    if devices_from_option:
        return [d.strip() for d in devices_from_option.split(",") if d.strip()]

    # Then check environment variable
    devices_str = os.environ.get("OPENTHREAD_TEST_DEVICES", "")
    if devices_str:
        return [d.strip() for d in devices_str.split(",") if d.strip()]

    # Fall back to defaults
    return DEFAULT_DEVICES


# List of all attached devices that could be used by the tests
# Only on device, the DUT is required. But many tests requires
# one or more devices to do more exhaustive tests.
# This provides a list of available devices.
# The first one is always considered as DUT which is important
# in the case of twister because that the one that has been flashed.
@pytest.fixture(scope="session")
def dut_nodes(request) -> Generator[list, None, None]:
    """Fixture providing a device manager for the test session."""

    # Add devices from command line, environment, or defaults
    nodes = []

    # Check if twister fixtures are available and then use the dedicated command handler
    try:
        dut = request.getfixturevalue("dut")
        shell = request.getfixturevalue("shell")
        if shell and dut:
            from openthread_tests.command_handlers import OTTwisterCommandRunner

            cmd_handler = OTTwisterCommandRunner(dut, shell)
            nodes.append(ZephyrOTCI(cmd_handler))
    except pytest.FixtureLookupError:
        dut = None

    device_paths = get_test_devices(request)
    for path in device_paths:
        try:
            if dut and dut.device_config.serial == path:
                print(f"Skiping {path} which is already used by twister")
                continue

            cli_handler = OtCliZephyr(path, 115200)
            cmd_handler = OtCliCommandRunner(cli_handler)
            nodes.append(ZephyrOTCI(cmd_handler))
        except:
            print(f"warning: Fail to open {path}")

    yield nodes

    # Cleanup: Disconnect all devices
    for node in nodes:
        node.close()


# Device under testing
# This return the main device, the one we are going to test.
# If we use twister, this means that this device is running the firmware
# to test and that any other devices are running firmware know to work.
@pytest.fixture
def dut_node(dut_nodes: list) -> Generator[otci.OTCI, None, None]:
    """Fixture providing a the DUT node"""
    devices = dut_nodes
    if not devices:
        pytest.skip("No devices available for testing")

    # Use the first device as dut node
    node = devices[0]

    yield node


# Second device
# Most tests will require a second device.
# This device will mostly act as a leader or router to create
# a known network and give possibiltiy to the DUT to perform
# on operation on this test network.
@pytest.fixture
def node1(dut_nodes: list) -> Generator[otci.OTCI, None, None]:
    """Fixture providing a the DUT node"""
    devices = dut_nodes
    if not devices:
        pytest.skip("No devices available for testing")

    # Use the first device as dut node
    if len(devices) >= 2:
        node = devices[1]
    else:
        node = None
    yield node


# We have a wide variety of tests that could run to test OpenThread.
# This depends a lot on the available hardware and the configuration.
# This makes sure that we run a test only if we have the required hardware
# and configuration for running it.
@pytest.fixture(autouse=True)
def skip_inapplicable_tests(request):
    if "node1" in request.fixturenames:
        if request.getfixturevalue("node1") is None:
            pytest.skip("Skipping test requiring a second node")
    if "otbr_test_values" in request.fixturenames:
        if request.getfixturevalue("otbr_test_values") is None:
            pytest.skip("Skipping test requiring an testing OTBR")
