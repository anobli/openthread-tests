# Copyright (c) 2025 Alexandre Bailon
#
# SPDX-License-Identifier: Apache-2.0
#

from typing import Any, Optional, List, Union, Dict
from otci.errors import UnexpectedCommandOutput
from otci.otci import OTCI

import logging


class ZephyrOTCI(OTCI):
    """
    This class represents an OpenThread Controller Interface instance that provides
    versatile interfaces to manipulate an OpenThread device.
    This override _OTCI__scan_networks in order to handle thr format used by zephyr.
    """

    def _OTCI__scan_networks(self, cmd: str, channel: Optional[int] = None) -> List[Dict[str, Any]]:
        if channel is not None:
            cmd += f' {channel}'

        output = self.execute_command(cmd, timeout=10)
        if len(output) < 2:
            raise UnexpectedCommandOutput(output)

        networks: List[Dict[str, Union[str, bool, int]]] = []
        for line in output[2:]:
            fields = line.strip().split('|')

            try:
                _, netname, extpanid, panid, extaddr, ch, dbm, lqi, _ = fields
            except Exception:
                logging.warning('ignored output: %r', line)
                continue

            networks.append({
                'network_name': netname.strip(),
                'extpanid': extpanid,
                'panid': int(panid, 16),
                'extaddr': extaddr,
                'channel': int(ch),
                'dbm': int(dbm),
                'lqi': int(lqi),
            })

        return networks
