# OpenThread Testing Framework

A Python-based framework for testing OpenThread devices.

## Overview

This project provides tools and utilities for testing OpenThread devices connected to a host computer. It allows:

- Managing multiple OpenThread devices
- Creating and joining Thread networks
- Scanning for Thread networks
- Running automated tests on OpenThread devices

## Installation

First, follow [Zephyr Getting Started Guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)
to setup a working environment for Zephyr.

Then, setup a test environment using `west`:
```bash
# Clone the repository
mkdir openthread-test-workspace
cd openthread-test-workspace
west init -m https://github.com/anobli/openthread-tests.git
cd openthread-tests.git

# Activate zephyr a virtual environment and install dependencies (recommended)
source /path/to/zephyr/venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Running Tests

Tests are implemented using pytest:

```bash
# Set the devices to use for testing (optional)
export OPENTHREAD_TEST_DEVICES="/dev/ttyUSB0,/dev/ttyUSB1"

# Run all tests
pytest

# Run a specific test
pytest tests/test_network_scan.py

# Run a test with verbose output
pytest -v tests/test_network_scan.py
```

### Running Tests using twister

Twister tests will build and flash one device and run test using it.
We need to configure the DUT using an hardware map and to configure
using the OT hardware map information about other devices that will
interact with the DUT.

First, have a look to [twister documentation](https://docs.zephyrproject.org/latest/develop/test/twister.html#running-tests-on-hardware)
and then create a hardware map file for your device. Here is an example for a cc1352p7-lp board:
```yaml
- connected: true
  id: L450020B
  platform: cc1352p7_lp/cc1352p7
  product: XDS110 (03.00.00.38) Embed with CMSIS-DAP
  runner: openocd
  runner_params:
    - --openocd=/usr/bin/openocd
    - --openocd-search=/usr/share/openocd/
  serial: /dev/ttyACM0
```

Then, create a second file that defines some data used by tests.
As example, this defines information about the OTBR device dedicated for testing:
```yaml
- id: L450020B
  eui64: 00124b0029495aa3
  otbr:
    network_name: OT-BayLibre-CI
    network_key: ff00112233445566778899aabbccddee
    pandid: 0x4123
    extpanid: 1111111122222222
    channel: 17
```

Then, run test using twister (replace `cc1352p7_lp` by any other supported platform):
```bash
west twister -p cc1352p7_lp --testsuite-root tests/openthread_shell/ --device-testing --hardware-map map.yml \
  --pytest-args=--ot-hardware-map=ot-test.yml
```

This will take care of building the firmware, running it, and then execute tests.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.