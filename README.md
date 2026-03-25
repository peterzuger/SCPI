# SCPI in Python

A lightweight Python library for controlling scientific instruments via **SCPI**
(Standard Commands for Programmable Instruments). This library provides an
interface to communicate with test and measurement equipment such as
multimeters, oscilloscopes, and power supplies over Serial (RS-232/USB) or
TCP/IP.

It relies solely on `pyserial` and standard libraries.

## Usage

### Basic Connection

The library supports a context manager for easy resource handling (automatic
connection/cleanup). You can pass either a device path (Serial) or an
IP/hostname (TCP).

```python
from SCPI import Keithley2000

# Connect to a Multimeter via Serial (e.g., USB-TTL)
with Keithley2000('/dev/ttyUSB0') as dmm:
    print(dmm.identification())  # Get manufacturer and model

    # Configure for DC Voltage measurement
    dmm.configure(dmm.Function.Voltage)

    # Read voltage
    voltage = dmm.read()
    print(f"Voltage: {voltage} V")
```

## Supported Instruments

The `SCPI` directory contains specific implementations for the following hardware:

| Class                        | Device Type                  | File              |
|:-----------------------------|:-----------------------------|:------------------|
| `Keithley2000`               | Digital Multimeter           | `keithley2000.py` |
| `HP54600`, `HP54601`, etc.   | Oscilloscope                 | `hp54600.py`      |
| `MP711131`, `MP711128`, etc. | Programmable DC Supply       | `mp711100.py`     |
| `AFG2005`, `AFG2105`, etc.   | Arbitrary Waveform generator | `afg2000.py`      |

## Adding a New Instrument

To add support for a new device, subclass the main `SCPI` class and implement
the necessary commands using the underlying `device.write()` and
`device.read_*()` methods.

```python
from SCPI import SCPI

class MyNewInstrument(SCPI):
    BAUDRATE = 9600

    def __init__(self, device):
        super().__init__(device, baudrate=self.BAUDRATE)

    def get_temperature(self):
        self.device.write(b":TEMP?")
        return self.device.read_float()
```
