# Copyright (c) 2025 Alexandre Bailon
#
# SPDX-License-Identifier: Apache-2.0

"""
Test version retrieval functionality.
"""
import re
import pytest
import otci


@pytest.mark.timeout(30)
def test_get_version(dut_node: otci.OTCI) -> None:
    """
    Test that we can retrieve the OpenThread version from a device.

    This test:
    1. Gets the version from the device
    2. Verifies that the version string matches the expected format
    """
    version = dut_node.version

    # Verify that we got a valid version string
    assert version is not None, "Failed to get version from device"

    # Check that the version follows one of the expected formats
    # Expected format: "OPENTHREAD/<build-version>; <platform>; <date> <time>"
    # Format: "OPENTHREAD/build; platform; date time"
    # Example 1: "OPENTHREAD/ncs-thread-reference-20241002; Zephyr; Mar 13 2025 15:17:47
    #              (build ID; platform; date and time)"
    # Example 2: "OPENTHREAD/20180926-01310-g9fdcef20; SIMULATION; Feb 11 2020 14:09:56"
    # Example 3: "OPENTHREAD/thread-reference-20230706-1276-g37b417a3e; POSIX; Apr  3 2025 15:06:04"
    version_regex = (
        r"OPENTHREAD\/[^;]+; [^;]+; [A-Z][a-z]{2}\s+[0-9]{1,2} [0-9]{4} "
        r"[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}"
    )
    error_msg = f"Version '{version}' does not match expected format"
    assert re.match(version_regex, version), error_msg
