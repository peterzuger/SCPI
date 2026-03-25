#!/usr/bin/env python
from typing import Optional

from SCPI import SCPI
from SCPI.device import SerialDevice


class MP711127(SCPI):
    BAUDRATE = 4_000_000  # USB device use max speed
    MAX_VOLTAGE = 30.0
    MAX_CURRENT = 5.0
    MAX_POWER = 150.0

    def __init__(self, device: SerialDevice | str, baudrate=BAUDRATE):
        super().__init__(device, baudrate=baudrate)

    # Measurment Commands
    def measure_voltage(self):
        self.device.write(b"MEAS:VOLT?")
        value = self.device.read_float()
        self._info("Measure Voltage: %g", value)
        return value

    def measure_current(self):
        self.device.write(b"MEAS:CURR?")
        value = self.device.read_float()
        self._info(f"Measure Current: %g", value)
        return value

    def measure_power(self):
        self.device.write(b"MEAS:POW?")
        value = self.device.read_float()
        self._info(f"Measure Power: %g", value)
        return value

    def measure_all(self, info: bool = False):
        self.device.write(f'MEAS:ALL{":INFO" if info else ""}?')
        value = self.device.readline()
        self._info(f"Measure ALL: %s", value)

        if info:
            u, i, p, overvoltage, overcurrent, overtemp, mode = value.split(",")
            return {
                "voltage": float(u),
                "current": float(i),
                "power": float(p),
                "overvoltage": True if overvoltage == "ON" else False,
                "overcurrent": True if overcurrent == "ON" else False,
                "overtemperature": True if overtemp == "ON" else False,
                "mode": {0: "STDBY", 1: "CV", 2: "CC", 3: "fail"}[int(mode)],
            }
        else:
            u, i = value.split(",")
            return {"voltage": float(u), "current": float(i)}

    # Output Commands
    def output(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b"OUTP?")
            state = self.device.read_bool()
        else:
            self.device.write(f'OUTP {"ON" if state else "OFF"}')
        self._info("output %s", state)
        return state

    @classmethod
    def _assert_current(cls, current):
        if not 0.0 <= current <= cls.MAX_CURRENT:
            raise ValueError(f"0.0 <= current <= {cls.MAX_CURRENT} (got {current})")

    @classmethod
    def _assert_voltage(cls, voltage):
        if not 0.0 <= voltage <= cls.MAX_VOLTAGE:
            raise ValueError(f"0.0 <= voltage <= {cls.MAX_VOLTAGE} (got {voltage})")

    @classmethod
    def _assert_current_limit(cls, current):
        if not 0.0 <= current <= (cls.MAX_CURRENT + 0.1):
            raise ValueError(
                f"0.0 <= current <= {cls.MAX_CURRENT + 0.1} (got {current})"
            )

    @classmethod
    def _assert_voltage_limit(cls, voltage):
        if not 0.0 <= voltage <= (cls.MAX_VOLTAGE + 1.0):
            raise ValueError(
                f"0.0 <= voltage <= {cls.MAX_VOLTAGE + 1.0} (got {voltage})"
            )

    def current(self, value: Optional[float] = None):
        if value is None:
            self.device.write(b"CURR?")
            value = self.device.read_float()
        else:
            self._assert_current(value)
            self.device.write(f"CURR {value}")
        self._info("Current: %s", value)
        return value

    def current_limit(self, value: Optional[float] = None):
        if value is None:
            self.device.write(b"CURR:LIM?")
            value = self.device.read_float()
        else:
            self._assert_current_limit(value)
            self.device.write(f"CURR:LIM {value}")
        self._info("Current Limit: %s", value)
        return value

    def voltage(self, value: Optional[float] = None):
        if value is None:
            self.device.write(b"VOLT?")
            value = self.device.read_float()
        else:
            self._assert_voltage(value)
            self.device.write(f"VOLT {value}")
        self._info("Voltage: %s", value)
        return value

    def voltage_limit(self, value: Optional[float] = None):
        if value is None:
            self.device.write(b"VOLT:LIM?")
            value = self.device.read_float()
        else:
            self._assert_voltage_limit(value)
            self.device.write(f"VOLT:LIM {value}")
        self._info("Voltage Limit: %s", value)
        return value

    # System Commands
    def system_local(self):
        self._info("local mode")
        self.device.write(":SYST:LOC")

    def system_remote(self):
        self._info("remote mode")
        self.device.write(":SYST:REM")


class MP711128(MP711127):
    MAX_VOLTAGE = 30.0
    MAX_CURRENT = 10.0
    MAX_POWER = 200.0


class MP711129(MP711127):
    MAX_VOLTAGE = 60.0
    MAX_CURRENT = 10.0
    MAX_POWER = 200.0


class MP711130(MP711127):
    MAX_VOLTAGE = 60.0
    MAX_CURRENT = 5.0
    MAX_POWER = 300.0


class MP711131(MP711127):
    MAX_VOLTAGE = 60.0
    MAX_CURRENT = 10.0
    MAX_POWER = 300.0


# Multimeter not implemented
class MP711132(MP711127):
    MAX_VOLTAGE = 30.0
    MAX_CURRENT = 5.0
    MAX_POWER = 150.0


class MP711133(MP711127):
    MAX_VOLTAGE = 60.0
    MAX_CURRENT = 5.0
    MAX_POWER = 300.0


class MP711134(MP711127):
    MAX_VOLTAGE = 30.0
    MAX_CURRENT = 10.0
    MAX_POWER = 300.0


class MP711135(MP711127):
    MAX_VOLTAGE = 60.0
    MAX_CURRENT = 10.0
    MAX_POWER = 300.0
