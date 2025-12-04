# Copyright (c) 2025 Alexandre Bailon
#
# SPDX-License-Identifier: Apache-2.0

"""
Test basic network connectivity between OpenThread devices.
"""
import pytest
import otci

from openthread_tests.utils import ot_helper_init_network


@pytest.mark.timeout(120)
def test_basic_connectivity(
        dut_node: otci.OTCI, node1: otci.OTCI) -> None:
    """
    Test basic connectivity between two devices on the same network.

    This test:
    1. Creates a network with the coordinator device
    2. Gets the joiner device to join the same network
    3. Verifies connectivity by having each device ping the other
    """
    # Create a network with the coordinator device
    network_name = "ConnectivityTest"
    network_key = "00112233445566778899aabbccddeeff"
    network_channel = 15
    network_panid = 0xABCD

    ot_helper_init_network([dut_node, node1], network_name, network_key,
                           network_panid, network_channel, False)
    # Give the network time to initialize
    dut_node.wait(30)

    # Verify joiner's state (should be router or child or leader)
    joiner_state = node1.get_state()
    assert joiner_state.strip() in ['router', 'child', 'leader'], (
        f"Joiner failed to join network, state: {joiner_state}"
    )

    # Get IP addresses from each device
    coordinator_addresses = dut_node.get_ipaddr_linklocal()
    joiner_addresses = node1.get_ipaddr_linklocal()

    # Verify mesh-local addresses were assigned
    assert coordinator_addresses, "Coordinator has no link local address"
    assert joiner_addresses, "Joiner has no link local address"

    # Test ping from coordinator to joiner
    ping_result = dut_node.ping(joiner_addresses, count=4, timeout=10)
    assert ping_result['transmitted_packets'] > 0, \
        "No ping sent from coordinator to joiner failed"
    assert ping_result['received_packets'] > 0, "No ping responses received from joiner"

    # Test ping from joiner to coordinator
    ping_result = node1.ping(coordinator_addresses, count=4, timeout=10)
    assert ping_result['transmitted_packets'] > 0, \
        "No ping sent from joiner to coordinator failed"
    assert ping_result['received_packets'] > 0, \
        "No ping responses received from coordinator"
