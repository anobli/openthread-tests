# Copyright (c) 2025 Alexandre Bailon
#
# SPDX-License-Identifier: Apache-2.0

"""
Test network scanning functionality.
"""
import pytest
import otci

from openthread_tests.utils import ot_helper_init_network


@pytest.mark.timeout(60)
def test_node_to_node_network_scan(dut_node: otci.OTCI, node1: otci.OTCI) -> None:
    """
    Test that one device can scan and find a network created by another device.

    This test:
    1. Creates a network with the coordinator device
    2. Scans for networks with the joiner device
    3. Verifies that the network is found
    """
    # Create a network with the coordinator device
    network_name = "TestNetwork"
    network_key = "00112233445566778899aabbccddeeff"
    network_channel = 15
    network_panid = 0xFACE

    ot_helper_init_network([node1], network_name, network_key,
                           network_panid, network_channel, False)
    # Give the network time to initialize
    node1.wait(30)

    # Scan for networks with the joiner device
    dut_node.ifconfig_up()
    networks = dut_node.discover()
    assert networks, "Failed to start network scan"

    # Verify that the network was found
    found = False
    for network in networks:
        if network["network_name"] == network_name:
            found = True
            break

    assert found, f"Network '{network_name}' was not found in scan results"


@pytest.mark.timeout(60)
def test_network_scan_otbr(dut_node: otci.OTCI, otbr_test_values) -> None:
    """
    Test that that DUT can scan and found the testing OTBR device.

    This test:
    1. Scans for networks with the DUT
    2. Verifies that the OTBR network is found
    """

    network_name = otbr_test_values["network_name"]

    # Scan for networks with the joiner device
    dut_node.ifconfig_up()
    networks = dut_node.discover()
    assert networks, "No network found"

    # Verify that the network was found
    found = False
    for network in networks:
        if network["network_name"] == network_name:
            found = True
            break

    assert found, f"Network '{network_name}' was not found in scan results"
