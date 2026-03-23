#!/usr/bin/env python
from enum import Enum
from typing import Optional

from SCPI import SCPI
from SCPI.device import SerialDevice


class AFG2005(SCPI):
    BAUDRATE = 4_000_000
    MAX_FREQUENCY = 5 * 10e5

    def __init__(self, device: SerialDevice | str):
        if isinstance(device, str):
            device = SerialDevice(device, self.BAUDRATE)
        super().__init__(device)

    # Apply Commands
    class Function(Enum):
        Sine = "SIN"
        Square = "SQU"
        Ramp = "RAMP"
        Noise = "NOIS"
        User = "USER"

    @classmethod
    def _assert_frequency(cls, frequency):
        if not 0.1 <= frequency <= cls.MAX_FREQUENCY:
            raise ValueError(
                f"0.1 <= frequency <= {cls.MAX_FREQUENCY} (got {frequency})"
            )

    @classmethod
    def _assert_amplitude(cls, amplitude):
        if not 0.001 <= amplitude <= 20.0:
            raise ValueError(f"0.001 <= amplitude <= 20.0 (got {amplitude})")

    @classmethod
    def _assert_offset(cls, offset):
        if not -10 <= offset <= 10:
            raise ValueError(f"-10 <= offset <= 10 (got {offset})")

    class Settings:
        def __init__(self, function, frequency=None, amplitude=None, offset=None):
            self.function = function
            self.frequency = frequency or ""
            self.amplitude = amplitude or ""
            self.offset = offset or ""

        def apply(self):
            return (
                f"{self.function.value} {self.frequency},{self.amplitude},{self.offset}"
            )

        @classmethod
        def from_APPL(cls, appl):
            "SIN +6.50000000E+01,+1.000E+01,+0.00E+00"
            function, parameters = appl.split(" ")
            frequency, amplitude, offset = parameters.split(",")

            return cls(
                AFG2005.Function(function),
                float(frequency),
                float(amplitude),
                float(offset),
            )

    def apply(self, function: Optional[Settings] = None):
        if function is None:
            self.device.write(b"SOUR:APPL?")
            function = self.Settings.from_APPL(self.device.read_string())
        else:
            self.device.write(f"SOUR:APPL:{function.apply()}")
        self._info("configured as %s", function)
        return function

    def function(self, function: Optional[Function] = None):
        if function is None:
            self.device.write(b"SOUR:FUNC?")
            function = self.Function(self.device.readline())
        else:
            self.device.write(f"SOUR:FUNC {function.value}")
        self._info("configured as %s", function.name)
        return function

    def frequency(self, frequency: Optional[float] = None):
        if frequency is None:
            self.device.write(b"SOUR:FREQ?")
            frequency = self.device.read_float()
        else:
            self._assert_frequency(frequency)
            self.device.write(f"SOUR:FREQ {frequency}")
        self._info("frequency %g", frequency)
        return frequency

    def amplitude(self, amplitude: Optional[float] = None):
        if amplitude is None:
            self.device.write(b"SOUR:AMPL?")
            amplitude = self.device.read_float()
        else:
            self._assert_amplitude(amplitude)
            self.device.write(f"SOUR:AMPL {amplitude}")
        self._info("amplitude %g", amplitude)
        return amplitude

    def offset(self, offset: Optional[float] = None):
        if offset is None:
            self.device.write(b"SOUR:DCO?")
            offset = self.device.read_float()
        else:
            self._assert_offset(offset)
            self.device.write(f"SOUR:DCO {offset}")
        self._info("offset %g", offset)
        return offset

    def duty(self, duty: Optional[float] = None):
        if duty is None:
            self.device.write(b"SOUR:SQU:DCYC?")
            duty = self.device.read_float()
        else:
            if not 1.0 <= duty <= 99.0:
                raise ValueError(f"1.0 <= duty <= 99.0 (got {duty})")
            self.device.write(f"SOUR:SQU:DCYC {duty}")
        self._info("duty cycle %g", duty)
        return duty

    def symmetry(self, symmetry: Optional[float] = None):
        if symmetry is None:
            self.device.write(b"SOUR:RAMP:SYMM?")
            symmetry = self.device.read_float()
        else:
            if not 0.0 <= symmetry <= 100.0:
                raise ValueError(f"0.0 <= symmetry <= 100.0 (got {symmetry})")
            self.device.write(f"SOUR:RAMP:SYMM {symmetry}")
        self._info("symmetry cycle %g", symmetry)
        return symmetry

    def output(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b"OUTP?")
            state = self.device.read_bool()
        else:
            self.device.write(f'OUTP {"ON" if state else "OFF"}')
        self._info("output %s", state)
        return state

    def load(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b"OUTP:LOAD?")
            state = self.device.readline() == "DEF"
        else:
            self.device.write(f'OUTP:LOAD {"DEF" if state else "INF"}')
        self._info("output load 50Ohms %s", state)
        return state

    class Unit(Enum):
        Vpp = "VPP"
        Vrms = "VRMS"
        dBm = "DBM"

    def unit(self, unit: Optional[Unit] = None):
        if unit is None:
            self.device.write(b"SOUR:VOLT:UNIT?")
            unit = self.Unit(self.device.readline())
        else:
            self.device.write(f"SOUR:VOLT:UNIT {unit.value}")
        self._info("voltage unit %s", unit.name)
        return unit

    @staticmethod
    def _assert_list_values(data: list[int]):
        if max(data) > 511 or min(data) < -511:
            raise ValueError("Data values out of range")

    @classmethod
    def list_to_bytes(cls, data: list[int]):
        cls._assert_list_values(data)
        b = b""
        for i in data:
            b += i.to_bytes(2, signed=True)
        return b

    def data(self, data: bytes | list[int]):
        if len(data) > 4096:
            raise ValueError("Too many points")

        if isinstance(data, bytes):
            self.device.write("DATA:DAC VOLATILE,0,", end=None)
            self.device.write_binary_block(data)

            length = len(data) / 2
        else:
            self._assert_list_values(data)
            self.device.write(f'DATA:DAC VOLATILE,0,{",".join(str(x) for x in data)}')
            length = len(data)
        self._info("wrote %s points of data to ARB waveform memory", length)

    def save(self, loc: int):
        if 0 <= loc <= 9:
            self._info("save instrument state to location %d", loc)
        elif 10 <= loc <= 19:
            self._info("save arbitrary waveform data to location %d", loc)
        else:
            raise ValueError("Invalid save location")
        self.device.write(f"*SAV {loc}")

    def recall(self, loc: int):
        if 0 <= loc <= 9:
            self._info("recall instrument state from location %d", loc)
        elif 10 <= loc <= 19:
            self._info("recall arbitrary waveform data from location %d", loc)
        else:
            raise ValueError("Invalid save location")
        self.device.write(f"*RCL {loc}")


class AFG2105(AFG2005):
    MAX_FREQUENCY = 5 * 10e5

    class Modulation(Enum):
        AM = "AM"
        FM = "FM"
        FSK = "FSK"
        Sweep = "SWE"

    def modulation_state(self, mod: Modulation, state: Optional[bool] = None):
        if state is None:
            self.device.write(f"SOUR:{mod.value}:STAT?")
            state = self.device.read_bool()
        else:
            self.device.write(f'SOUR:{mod.value}:STAT {"ON" if state else "OFF"}')
        self._info("%s modulation %s", mod.name, state)
        return state

    class ModulationSource(Enum):
        Internal = "INT"
        External = "EXT"

    def modulation_source(
        self, mod: Modulation, source: Optional[ModulationSource] = None
    ):
        if source is None:
            self.device.write(f"SOUR:{mod.value}:SOUR?")
            source = self.ModulationSource(self.device.readline())
        else:
            self.device.write(f"SOUR:{mod.value}:SOUR {source.value}")
        self._info("%s modulation source %s", mod.name, source.name)
        return source

    def _assert_mod_function(self, mod):
        if mod not in (self.Modulation.AM, self.Modulation.FM):
            raise ValueError(f"Modulation function not applicable to {mod.name}")

    def modulation_function(
        self, mod: Modulation, fun: Optional[AFG2005.Function] = None
    ):
        self._assert_mod_function(mod)

        if fun is None:
            self.device.write(f"SOUR:{mod.value}:INT:FUN?")
            fun = self.Function(self.device.readline())
        else:
            F = self.Function
            if fun not in (F.Sine, F.Square, F.Ramp):
                raise ValueError(f"Modulation function not applicable {fun.name}")
            self.device.write(f"SOUR:{mod.value}:INT:FUN {fun.value}")
        self._info("%s modulation function: %s", mod.name, fun.name)
        return fun

    def modulation_frequency(self, mod: Modulation, freq: Optional[float] = None):
        self._assert_mod_function(mod)

        if freq is None:
            self.device.write(f"SOUR:{mod.value}:INT:FREQ?")
            freq = self.device.read_float()
        else:
            self.device.write(f"SOUR:{mod.value}:INT:FREQ {freq}")
        self._info("%s modulation frequency: %g", mod.name, freq)
        return freq

    def modulation_depth(self, mod: Modulation, depth: Optional[float] = None):
        if mod is not self.Modulation.AM:
            raise ValueError("Modulation depth only applicable to AM")

        if depth is None:
            self.device.write(b"SOUR:AM:DEPT?")
            depth = self.device.read_float()
        else:
            if not 0 <= depth <= 120:
                raise ValueError(f"0 <= depth <= 120 (got {depth})")
            self.device.write(f"SOUR:AM:DEPT {depth}")
        self._info("AM modulation depth: %g", depth)
        return depth

    def modulation_deviation(self, mod: Modulation, dev: Optional[float] = None):
        if mod is not self.Modulation.FM:
            raise ValueError("Modulation deviation only applicable to FM")

        if dev is None:
            self.device.write(b"SOUR:FM:DEV?")
            dev = self.device.read_float()
        else:
            self.device.write(f"SOUR:FM:DEV {dev}")
        self._info("FM modulation deviation: %g", dev)
        return dev

    def modulation_hop_frequency(self, mod: Modulation, freq: Optional[float] = None):
        if mod is not self.Modulation.FSK:
            raise ValueError("Modulation hop frequency only applicable to FSK")

        if freq is None:
            self.device.write(b"SOUR:FSK:FREQ?")
            freq = self.device.read_float()
        else:
            self.device.write(f"SOUR:FSK:FREQ {freq}")
        self._info("FSK modulation hop frequency: %g", freq)
        return freq

    def modulation_rate(self, mod: Modulation, rate: Optional[float] = None):
        if mod not in (self.Modulation.FSK, self.Modulation.Sweep):
            raise ValueError(f"Modulation rate not applicable to {mod.name}")

        f = "FSK:INT" if mod is self.Modulation.FSK else "SWE"

        if rate is None:
            self.device.write(f"SOUR:{f}:RATE?")
            rate = self.device.read_float()
        else:
            self.device.write(f"SOUR:{f}:RATE {rate}")

        self._info("%s modulation rate: %g", mod.name, rate)
        return rate

    def modulation_startstop_frequency(
        self, mod: Modulation, freq: Optional[tuple[float, float]] = None
    ):
        if mod is not self.Modulation.Sweep:
            raise ValueError("Modulation start/stop frequency only applicable to Sweep")

        if freq is None:
            self.device.write(b"SOUR:SWE:FREQ:START?")
            start = self.device.read_float()
            self.device.write(b"SOUR:SWE:FREQ:STOP?")
            stop = self.device.read_float()
            freq = (start, stop)
        else:
            self.device.write(f"SOUR:SWE:FREQ:START {freq[0]}")
            self.device.write(f"SOUR:SWE:FREQ:STOP {freq[1]}")
        self._info("Sweep modulation start/stop frequency: %g/%g", *freq)
        return freq

    class ModulationSpacing(Enum):
        Linear = "LIN"
        Logarithmic = "LOG"

    def modulation_spacing(
        self, mod: Modulation, spac: Optional[ModulationSpacing] = None
    ):
        if mod is not self.Modulation.Sweep:
            raise ValueError("Modulation spacing only applicable to Sweep")

        if spac is None:
            self.device.write(b"SOUR:SWE:SPAC?")
            spac = self.ModulationSpacing(self.device.readline())
        else:
            self.device.write(f"SOUR:SWE:SPAC {spac.value}")
        self._info("Sweep modulation spacing: %s", spac.name)
        return spac

    def counter(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b"COUN:STAT?")
            state = bool(int(self.device.readline()))
        else:
            self.device.write(f'COUN:STAT {"ON" if state else "OFF"}')
        self._info("counter mode %s", state)
        return state

    def gate(self, t: Optional[float] = None):
        if t is None:
            self.device.write(b"COUN:GAT?")
            t = float(self.device.readline())
        else:
            self.device.write(f"COUN:GAT {t}")
        self._info("gate time %ss", t)
        return t

    def counter_value(self):
        self.device.write(b"COUN:VAL?")
        val = self.device.read_float()
        self._info("counter value %sHz", val)
        return val


class AFG2012(AFG2005):
    MAX_FREQUENCY = 12 * 10e5


class AFG2112(AFG2105):
    MAX_FREQUENCY = 12 * 10e5


class AFG2025(AFG2005):
    MAX_FREQUENCY = 25 * 10e5


class AFG2125(AFG2105):
    MAX_FREQUENCY = 25 * 10e5
