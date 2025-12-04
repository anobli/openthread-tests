# Copyright (c) 2025 Alexandre Bailon
#
# SPDX-License-Identifier: Apache-2.0

"""
Utility functions for OpenThread testing.
"""


def ot_helper_init_network(nodes: list,
                           network_name: str,
                           network_key: str,
                           panid: int,
                           channel: int,
                           factoryreset: bool):
    """
    Helper function to setup a Thread network for one or more nodes.

    :param nodes: Nodes to configure
    :type nodes: list
    :param network_name: Network name
    :type network_name: str
    :param network_key: Network key
    :type network_key: str
    :param panid: PanId
    :type panid: int
    :param channel: Network channel
    :type channel: int
    :param factoryreset: If set to True, perform a factoryreset before configuring the nodes
    :type factoryreset: bool
    """
    for node in nodes:
        if factoryreset:
            node.factory_reset()
            node.wait(5)
        else:
            node.thread_stop()
            node.ifconfig_down()

        node.dataset_init_buffer()
        node.dataset_set_buffer(
            network_name=network_name,
            network_key=network_key,
            panid=panid,
            channel=channel)
        node.dataset_commit_buffer('active')

        node.ifconfig_up()
        node.thread_start()
