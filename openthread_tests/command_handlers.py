# Copyright (c) 2025 Alexandre Bailon
#
# SPDX-License-Identifier: Apache-2.0

import time
import re

from typing import Any, Optional, Callable, List
from otci.command_handlers import OTCommandHandler
from otci.connectors import OtCliHandler
from otci.errors import ExpectLineTimeoutError
from otci.utils import match_line

try:
    from twister_harness import DeviceAdapter
    from twister_harness.helpers.shell import Shell
    TWISTER = True
except:
    TWISTER = False


def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


class OtCliZephyr(OtCliHandler):
    """Connector for OT CLI SOC devices running Zephyr via Serial."""

    def __init__(self, dev: str, baudrate: int, timeout: float = 0.1):
        self.__dev = dev
        self.__baudrate = baudrate

        import serial
        self.__serial = serial.Serial(self.__dev, self.__baudrate, timeout=timeout, exclusive=True)
        self.writeline('\r\n')
        self.__linebuffer = b''

    def __repr__(self):
        return self.__dev

    def readline(self) -> Optional[str]:
        while self.__serial.is_open:
            line = self.__serial.readline()

            if not line.endswith(b'\n'):
                self.__linebuffer += line
            else:
                line = self.__linebuffer + line
                self.__linebuffer = b''
                return escape_ansi(line.decode('utf-8', errors='ignore').rstrip('\r\n')).replace("uart:~$ ", "").replace("ot ", "")

        return None

    def writeline(self, s: str):
        self.__serial.write(f"ot {s}\r\n".encode('utf-8'))

    def wait(self, duration: float, **kwargs):
        time.sleep(duration)

    def close(self):
        self.__serial.close()


if TWISTER:
    class OTTwisterCommandRunner(OTCommandHandler):
        __PATTERN_COMMAND_DONE_OR_ERROR = re.compile(
            r'(Done|Error|Error \d+:.*|.*: command not found)$')  # "Error" for spinel-cli.py

        __ASYNC_COMMANDS = {'scan', 'ping', 'discover'}

        def __init__(self, dut: DeviceAdapter, shell: Shell):
            self.__dut = dut
            self.__shell = shell
            self.__line_read_callback = None

        def __repr__(self):
            return f"twister: {self.__dut.device_config.id}"

        def execute_command(self, cmd: str, timeout: float) -> List[str]:
            zephyr_cmd = f'ot {cmd}'

            output = self.shell(zephyr_cmd, timeout=timeout)

            if self.__line_read_callback is not None:
                for line in output:
                    self.__line_read_callback(line)

            if cmd in ('reset', 'factoryreset'):
                self.wait(3)

            if match_line(output[-1], self.__PATTERN_COMMAND_DONE_OR_ERROR):
                return output[1:]

            done = False
            while not done and timeout > 0:
                self.wait(1)
                lines = [escape_ansi(l).replace("uart:~$ ", "").replace("ot ", "") for l in self.__dut.readlines()]
                timeout -= 1

                for line in lines:
                    output.append(line)

                    if match_line(line, self.__PATTERN_COMMAND_DONE_OR_ERROR):
                        done = True
                        break

            if not done:
                raise ExpectLineTimeoutError(self.__PATTERN_COMMAND_DONE_OR_ERROR)

            return output[1:]

        def execute_platform_command(self, cmd, timeout=10) -> List[str]:
            raise NotImplementedError(f'Platform command is not supported on {self.__class__.__name__}')

        def shell(self, cmd: str, timeout: float) -> List[str]:
            output = [escape_ansi(l).replace("uart:~$ ", "").replace("ot ", "") for l in self.__shell.exec_command(cmd)]
            post_output = []
            for l in output:
                if l:
                    post_output.append(l)
            return post_output

        def close(self):
            print("TODO: CLOSE")

        def wait(self, duration: float) -> List[str]:
            time.sleep(duration)
            return []

        def set_line_read_callback(self, callback: Optional[Callable[[str], Any]]):
            self.__line_read_callback = callback
