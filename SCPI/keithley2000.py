#!/usr/bin/env python
from enum import Enum, Flag, IntFlag
from typing import Optional

from SCPI import SCPI
from SCPI.device import SerialDevice

INF = float("9.9E+37")


class Keithley2000(SCPI):
    BAUDRATE = 4800  # factory baudrate

    def __init__(self, device: SerialDevice | str, baudrate=BAUDRATE):
        super().__init__(device, baudrate=baudrate)

        self._function = self.Function.Voltage

    # SCPI commands
    class Function(Enum):
        Current = "CURR:DC"
        CurrentAC = "CURR:AC"
        Voltage = "VOLT:DC"
        VoltageAC = "VOLT:AC"
        Resistance = "RES"
        FResistance = "FRES"
        Period = "PER"
        Frequency = "FREQ"
        Temperature = "TEMP"
        Diode = "DIOD"
        Continuity = "CONT"

    def configure(self, function: Optional[Function] = None):
        if function is None:
            self.device.write(b":CONF?")
            self._function = self.Function(self.device.read_string())
        else:
            self.device.write(f":CONF:{function.value}")
            self._function = function
            self.operation_complete()
        self._info("configured as %s", self._function.name)
        return self._function

    def fetch(self):
        self._info("fetch")
        self.device.write(b":FETC?")
        try:
            return self.device.read_float()
        except ValueError:
            return None

    def read(self):
        self._info("read")
        self.device.write(b":READ?")
        try:
            return self.device.read_float()
        except ValueError:
            return self.fetch()

    def measure(self, function: Function):
        self._info("measure %s", function.name)
        self.device.write(f":MEAS:{function.value}?")
        try:
            return self.device.read_float()
        except ValueError:
            return self.fetch()

    # CALCulate subsystem
    class CALC1Format(Enum):
        NONE = "NONE"
        MXB = "MXB"
        Percent = "PERC"

    class CALC2Format(Enum):
        NONE = "NONE"
        Mean = "MEAN"
        StandardDeviation = "SDEV"
        Max = "MAX"
        Min = "MIN"

    def calculate_format(
        self,
        calc: int,
        form: Optional[CALC1Format | CALC2Format] = None,
    ):
        if form is None:
            self.device.write(f":CALC{calc}:FORM?")
            _format = self.CALC1Format if calc == 1 else self.CALC2Format
            form = _format(self.device.readline())
        else:
            self.device.write(f":CALC{calc}:FORM {form.value}")
        self._info("calculate %d format %s", calc, form.name)
        return form

    def calculate_state(self, calc: int, state: Optional[bool] = None):
        if state is None:
            self.device.write(f":CALC{calc}:STAT?")
            state = self.device.read_bool()
        else:
            self.device.write(f":CALC{calc}:STAT {int(state)}")
        self._info("calculate %d state %s", calc, state)
        return state

    def calculate_data(self, calc: int):
        self.device.write(f":CALC{calc}:DATA?")
        self._info("calculate %d data", calc)
        try:
            return self.device.read_float()
        except ValueError:
            return None

    def calculate_immediate(self, calc: int, read: bool = False):
        val = None
        if read:
            self.device.write(f":CALC{calc}:IMM?")
            val = self.device.read_float()
        else:
            self.device.write(f":CALC{calc}:IMM")
        self._info("calculate %s immediate %s", calc, val)
        return val

    # KMATH
    def calculate_kmath_factors(
        self,
        calc: int,
        m: Optional[float] = None,
        b: Optional[float] = None,
    ):
        if m is None:
            self.device.write(f":CALC{calc}:KMAT:MMF?")
            m = self.device.read_float()
        else:
            self.device.write(f":CALC{calc}:KMAT:MMF {m}")

        if b is None:
            self.device.write(f":CALC{calc}:KMAT:MBF?")
            b = self.device.read_float()
        else:
            self.device.write(f":CALC{calc}:KMAT:MBF {b}")

        self._info("calculate %s mx+b factors: %gx+%g", calc, m, b)
        return m, b

    def calculate_kmath_units(self, calc: int, unit: Optional[str] = None):
        if unit is None:
            self.device.write(f":CALC{calc}:KMAT:MUN?")
            unit = self.device.read_string()
        else:
            if len(unit) != 3:
                raise ValueError(f"Unit must be 3 characters: {unit}")
            self.device.write(f':CALC{calc}:KMAT:MUN "{unit}"')
        self._info("calculate %s unit %s", calc, unit)
        return unit

    def calculate_kmath_percent(self, calc: int, target: Optional[float] = None):
        if target is None:
            self.device.write(f":CALC{calc}:KMAT:PERC?")
            target = self.device.read_float()
        else:
            self.device.write(f":CALC{calc}:KMAT:PERC {target}")
        self._info("calculate %s percentage target %g", calc, target)
        return target

    def calculate_kmath_aquire(self, calc: int):
        self._info("calculate %s aquire percentage target", calc)
        self.device.write(f":CALC{calc}:KMAT:PERC:ACQ")

    # LIMITS
    def calculate_limits(
        self,
        calc: int,
        lower: Optional[float] = None,
        upper: Optional[float] = None,
    ):
        if lower is None:
            self.device.write(f":CALC{calc}:LIM:LOW?")
            lower = self.device.read_float()
        else:
            self.device.write(f":CALC{calc}:LIM:LOW {lower}")

        if upper is None:
            self.device.write(f":CALC{calc}:LIM:UPP?")
            upper = self.device.read_float()
        else:
            self.device.write(f":CALC{calc}:LIM:UPP {upper}")

        self._info("calculate %s limits: lower: %g, upper: %g", calc, lower, upper)
        return lower, upper

    def calculate_limit_state(self, calc: int, state: Optional[bool] = None):
        if state is None:
            self.device.write(f":CALC{calc}:LIM:STAT?")
            state = self.device.read_bool()
        else:
            self.device.write(f":CALC{calc}:LIM:STAT {int(state)}")
        self._info("calculate %d limit state %s", calc, state)
        return state

    def calculate_limit_fail(self, calc: int):
        self._info("calculate %s fail?", calc)
        self.device.write(f":CALC{calc}:LIM:FAIL?")
        return self.device.read_bool()

    def calculate_limit_clear(self, calc: int):
        self._info("calculate %s clear", calc)
        self.device.write(f":CALC{calc}:LIM:CLE")

    def calculate_limit_clear_auto(self, calc: int, state: Optional[bool] = None):
        if state is None:
            self.device.write(f":CALC{calc}:LIM:CLE:AUTO?")
            state = self.device.read_bool()
        else:
            self.device.write(f":CALC{calc}:LIM:CLE:AUTO {int(state)}")
        self._info("calculate %s auto clear %s", calc, state)
        return state

    def calculate_limit_immediate(self, calc: int):
        self._info(
            "calculate %s limit immediate",
        )
        self.device.write(f":CALC{calc}:IMM")

    # DISPlay subsystem
    def display(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":DISP:ENAB?")
            state = self.device.read_bool()
        else:
            self.device.write(f":DISP:ENAB {int(state)}")
        self._info("display %s", state)
        return state

    def display_text(self, data: Optional[str] = None):
        if data is None:
            self.device.write(b":DISP:TEXT:DATA?")
            data = self.device.read_string()
        else:
            if len(data) > 12:
                raise ValueError(f"Text too long (max 12 characters)(got {len(data)})")
            self.device.write(f':DISP:TEXT:DATA "{data}"')
        self._info("text: %s", data)
        return data

    def text_state(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":DISP:TEXT:STAT?")
            state = self.device.read_bool()
        self.device.write(f":DISP:TEXT:STAT {int(state)}")
        self._info("text %s", state)
        return state

    # FORMat subsystem
    # :FORMat[:DATA] <type> -> ASCII only with RS-232
    # :FORMat:BORDer <name> -> ignored for ASCII

    class FormatElements(Flag):
        Reading = 1
        Channel = 2
        Unit = 4

        def to_elements(self):
            return (
                f'{"READ" if self.value & self.Reading else ""},'
                + f'{"CHAN" if self.value & self.Channel else ""},'
                + f'{"UNIT" if self.value & self.Unit else ""}'
            )

        @classmethod
        def from_elements(cls, val):
            reading = cls.Reading if "READ" in val else cls(0)
            channel = cls.Channel if "CHAN" in val else cls(0)
            unit = cls.Unit if "UNIT" in val else cls(0)
            return cls(reading | channel | unit)

    def format_elements(self, elements: Optional[FormatElements] = None):
        if elements is None:
            self.device.write(b":FORM:ELEM?")
            elements = self.FormatElements.from_elements(self.device.readline())
        else:
            self.device.write(f":FORM:ELEM {elements.to_elements()}")
        self._info("format elements: %s", elements.name)
        return elements

    # ROUTe subsystem
    def route_close(self, channel: int):
        self._info("route close %d", channel)
        self.device.write(f":ROUT:CLOS (@{channel})")

    def route_state(self):
        self._info("route state?")
        self.device.write(b":ROUT:CLOS:STAT?")
        return self.device.readline()

    def route_open_all(self):
        self._info("route open all")
        self.device.write(b":ROUT:OPEN:ALL")

    def route_multi_close(self, channels: list[int]):
        self._info("route multiple close %s", channels)
        self.device.write(f':ROUT:MULT:CLOS (@{",".join(str(x) for x in channels)})')

    def route_multi_state(self):
        self._info("route multiple state?")
        self.device.write(b":ROUT:MULT:CLOS:STAT?")
        return self.device.readline()

    def route_multi_open(self, channels: list[int]):
        self._info("route multiple close %s", channels)
        self.device.write(f':ROUT:MULT:CLOS (@{",".join(str(x) for x in channels)})')

    class Route(Enum):
        NONE = "NONE"
        Internal = "INT"
        External = "EXT"

    def route_scan(self, route: Route, channels: Optional[list[int]] = None):
        if route is self.Route.NONE:
            raise ValueError("scan route must be Internal or External")
        if channels is None:
            self.device.write(f":ROUT:SCAN:{route.value}?")
            channels = [int(x) for x in self.device.readline()[2:-1].split(":")]
        else:
            self.device.write(
                f':ROUT:SCAN:{route.value} (@{",".join(str(x) for x in channels)})'
            )
        self._info("route %s scan list %s", route.name, channels)
        return channels

    def route_select(self, route: Optional[Route] = None):
        if route is None:
            self.device.write(b":ROUT:SCAN:LSEL?")
            route = self.Route(self.device.readline())
        else:
            self.device.write(f":ROUT:SCAN:LSEL {route.value}")
        self._info("route selected: %s", route.name)
        return route

    # SENSe subsystem
    def function(self, function: Optional[Function] = None):
        if function is None:
            self.device.write(b":FUNC?")
            function = self.Function(self.device.readline()[1:-1])
        else:
            self.device.write(f":FUNC '{function.value}'")
        self._info("selected function: %s", function.name)
        return function

    def data(self):
        self._info("data")
        self.device.write(b":DATA?")
        try:
            return self.device.read_float()
        except ValueError:
            return None

    def hold_window(self, window: Optional[float] = None):
        if window is None:
            self.device.write(b":HOLD:WIND?")
            window = self.device.read_float()
        else:
            if not 0.01 <= window <= 20:
                raise ValueError(f"0.01 <= window <=  20 (got {window})")
            self.device.write(f":HOLD:WIND {window}")
        self._info("hold window: %g", window)
        return window

    def hold_count(self, count: Optional[int] = None):
        if count is None:
            self.device.write(b":HOLD:COUN?")
            count = self.device.read_int()
        else:
            if not 2 <= count <= 100:
                raise ValueError(f"2 <= count <=  100 (got {count})")
            self.device.write(f":HOLD:COUN {count}")
        self._info("hold count: %d", count)
        return count

    def hold_state(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":HOLD:STAT?")
            state = self.device.read_bool()
        else:
            self.device.write(f":HOLD:STAT {int(state)}")
        self._info("hold state: %s", state)
        return state

    def range(self, function: Function, upper: Optional[float] = None):
        if upper is None:
            self.device.write(f":{function.value}:RANG?")
            upper = self.device.read_float()
        else:
            self.device.write(f":{function.value}:RANG {upper}")
        self._info("range %s upper limit: %g", function.name, upper)
        return upper

    def autorange(self, function: Function, state: Optional[bool] = None):
        if state is None:
            self.device.write(f":{function.value}:RANG:AUTO?")
            state = self.device.read_bool()
        else:
            self.device.write(f":{function.value}:RANG:AUTO {int(state)}")
        self._info("autorange %s state: %s", function.name, state)
        return state

    def reference(self, function: Function, state: Optional[bool] = None):
        if state is None:
            self.device.write(f":{function.value}:STAT?")
            state = self.device.read_bool()
        else:
            self.device.write(f":{function.value}:STAT {int(state)}")
        self._info("reference mode %s: %s", function.name, state)
        return state

    def reference_value(self, function: Function, value: Optional[float] = None):
        if value is None:
            self.device.write(f":{function.value}:REF?")
            value = self.device.read_float()
        else:
            self.device.write(f":{function.value}:REF {value}")
        self._info("reference value %s: %g", function.name, value)
        return value

    def reference_aquire(self, function: Function):
        self._info("aquire reference value %s", function.name)
        self.device.write(f":{function.value}:ACQ")

    def digits(self, function: Function, digits: Optional[int] = None):
        if digits is None:
            self.device.write(f":{function.value}:DIG?")
            digits = self.device.read_int()
        else:
            if not 4 <= digits <= 7:
                raise ValueError(f"4 <= digits <=  7 (got {digits})")
            self.device.write(f":{function.value}:DIG {digits}")
        self._info("digits %s: %s", function.name, digits)
        return digits

    def _assert_sense_function(self, function: Function):
        F = self.Function
        if function not in (
            F.Current,
            F.CurrentAC,
            F.Voltage,
            F.VoltageAC,
            F.Resistance,
            F.FResistance,
            F.Temperature,
        ):
            raise ValueError(f"not applicable to {function.name}")

    def nplc(self, function: Function, cycles: Optional[float] = None):
        self._assert_sense_function(function)
        if cycles is None:
            self.device.write(f"{function.value}:NPLC?")
            cycles = self.device.read_float()
        else:
            if not 0.01 <= cycles <= 10:
                raise ValueError(f"0.01 <= cycles <= 10 (got {cycles})")
            self.device.write(f"{function.value}:NPLC {cycles}")
        self._info("Number of Power Line Cycles %s: %g", function.name, cycles)
        return cycles

    def average(self, function: Function, state: Optional[bool] = None):
        self._assert_sense_function(function)
        if state is None:
            self.device.write(f":{function.value}:AVER:STATE?")
            state = self.device.read_bool()
        else:
            self.device.write(f":{function.value}:AVER:STATE {int(state)}")
        self._info("sense average state %s: %s", function.name, state)
        return state

    class AverageType(Enum):
        Repeat = "REP"
        Moving = "MOV"

    def average_type(self, function: Function, t: Optional[AverageType] = None):
        self._assert_sense_function(function)
        if t is None:
            self.device.write(f":{function.value}:AVER:TCON?")
            t = self.AverageType(self.device.readline())
        else:
            self.device.write(f":{function.value}:AVER:TCON {t.value}")
        self._info("sense average type %s: %s", function.name, t.name)
        return t

    def average_count(self, function: Function, count: Optional[int] = None):
        self._assert_sense_function(function)
        if count is None:
            self.device.write(f":{function.value}:AVER:COUN?")
            count = self.device.read_int()
        else:
            if not 1 <= count <= 100:
                raise ValueError(f"1 <= count <=  100 (got {count})")
            self.device.write(f":{function.value}:AVER:COUN {count}")
        self._info("sense average count %s: %d", function.name, count)
        return count

    def bandwidth(self, function: Function, bw: Optional[float] = None):
        if function not in (self.Function.CurrentAC, self.Function.VoltageAC):
            raise ValueError(f"Bandwidth is not applicable to {function.name}")
        if bw is None:
            self.device.write(f":{function.value}:DET:BAND?")
            bw = self.device.read_float()
        else:
            self.device.write(f":{function.value}:DET:BAND {bw}")
        self._info("sense bandwidth %s: %gHz", function.name, bw)
        return bw

    def threshold(self, function: Function, voltage: int):
        if function not in (self.Function.Period, self.Function.Frequency):
            raise ValueError(f"Threshold is not applicable to {function.name}")
        if voltage is None:
            self.device.write(f":{function.value}:THR:VOLT:RANG?")
            voltage = self.device.read_int()
        else:
            self.device.write(f":{function.value}:THR:VOLT {voltage}")
        self._info("sense threshold %s: %gV", function.name, voltage)
        return voltage

    class Thermocouple(Enum):
        J = "J"
        K = "K"
        T = "T"

    def thermocouple(self, t: Optional[Thermocouple] = None):
        if t is None:
            self.device.write(b":TEMP:TC:TYPE?")
            t = self.Thermocouple(self.device.readline())
        else:
            self.device.write(f":TEMP:TC:TYPE {t.value}")
        self._info("Thermocouple type: %s", t.name)
        return t

    class ThermocoupleReference(Enum):
        Simulated = "SIM"
        Real = "REAL"

    def thermocouple_reference(self, ref: Optional[ThermocoupleReference] = None):
        if ref is None:
            self.device.write(b":TEMP:TC:RJUN:RSEL?")
            ref = self.ThermocoupleReference(self.device.readline())
        else:
            self.device.write(f":TEMP:TC:RJUN:RSEL{ref.value}")
        self._info("Thermocouple reference: %s", ref.name)
        return ref

    def thermocouple_simulated_reference(self, temp: Optional[float] = None):
        if temp is None:
            self.device.write(b":TEMP:TC:RJUN:SIM?")
            temp = self.device.read_float()
        else:
            self.device.write(f":TEMP:TC:RJUN:SIM {temp}")
        self._info("Thermocouple Simulated reference temperature %g", temp)
        return temp

    def thermocouple_real_reference(
        self,
        coeff: Optional[float] = None,
        offset: Optional[float] = None,
    ):
        if coeff is None:
            self.device.write(b":TEMP:TC:RJUN:REAL:TC?")
            coeff = self.device.read_float()
        else:
            self.device.write(f":TEMP:TC:RJUN:REAL:TC {coeff}")

        if offset is None:
            self.device.write(b":TEMP:TC:RJUN:REAL:OFFSET?")
            offset = self.device.read_float()
        else:
            self.device.write(f":TEMP:TC:RJUN:REAL:OFFSET {offset}")

        self._info("Thermocouple Real coefficient: %g, offset: %g", coeff, offset)
        return coeff, offset

    def diode_current(self, current: Optional[float] = None):
        if current is None:
            self.device.write(b":DIOD:CURR:RANG?")
            current = self.device.read_float()
        else:
            if not 0 <= current <= 1e-3:
                raise ValueError(f"0 <= current <=  1e-3 (got {current})")
            self.device.write(f":DIOD:CURR:RANG {current}")
        self._info("sense diode current: %g", current)
        return current

    def continuity_threshold(self, threshold: Optional[float] = None):
        if threshold is None:
            self.device.write(b":CONT:THR?")
            threshold = self.device.read_float()
        else:
            if not 1 <= threshold <= 1000:
                raise ValueError(f"1 <= threshold <= 1000 (got {threshold})")
            self.device.write(f":CONT:THR {threshold}")
        self._info("sense continuity threshold: %g", threshold)
        return threshold

    # STATus subsystem
    class MeasurmentRegister(IntFlag):
        ReadingOverflow = 1
        LowLimit = 2
        HighLimit = 4
        ReadingAvailable = 32
        BufferAvailable = 128
        BufferHalfFull = 256
        BufferFull = 512

    class QuestionableRegister(IntFlag):
        Temperature = 16
        Calibration = 256
        Warning = 16384

    class OperationRegister(IntFlag):
        Measuring = 16
        Triggering = 32
        Idle = 1024

    class Register(Enum):
        Measurment = ("MEAS", "MeasurmentRegister")
        Questionable = ("QUES", "QuestionableRegister")
        Operation = ("OPER", "OperationRegister")

        def get_type(self, other):
            return getattr(other, self.value[1])

    def status_register_event(self, register: Register):
        self.device.write(f":STAT:{register.value[0]}?")
        value = register.get_type(self)(self.device.read_int())
        self._info("register %s value: %s", register.name, value)
        return value

    def status_register_enable(self, register: Register, value: Optional[int] = None):
        if value is None:
            self.device.write(f":STAT:{register.value[0]}:ENAB?")
            value = register.get_type(self)(self.device.read_int())
        else:
            self.device.write(f":STAT:{register.value[0]}:ENAB {value}")
        self._info("enable register %s value: %s", register.name, value)
        return value

    def status_register_condition(self, register: Register):
        self.device.write(f":STAT:{register.value[0]}:COND?")
        value = register.get_type(self)(self.device.read_int())
        self._info("condition register %s value: %s", register.name, value)
        return value

    def status_preset(self):
        self._info("status preset")
        self.device.write(b":STAT:PRES")

    def status_queue_next(self):
        self._info("status queue next?")
        self.device.write(b":STAT:QUE?")
        return self.device.readline()

    def status_queue_clear(self):
        self._info("status queue clear")
        self.device.write(b":STAT:QUE:CLE")

    def status_queue_enable(self, errors: Optional[list[int]] = None):
        if errors is None:
            self.device.write(b":STAT:QUE:ENAB?")
            errors = [int(x) for x in self.device.readline().split(",")]
        else:
            self.device.write(f':STAT:QUE:ENAB ({",".join(str(x) for x in errors)})')
        self._info("status queue enabled errors: %s", errors)
        return errors

    def status_queue_disable(self, errors: Optional[list[int]] = None):
        if errors is None:
            self.device.write(b":STAT:QUE:DIS?")
            errors = [int(x) for x in self.device.readline().split(",")]
        else:
            self.device.write(f':STAT:QUE:DIS ({",".join(str(x) for x in errors)})')
        self._info("status queue disabled errors: %s", errors)
        return errors

    # SYSTem subsystem
    def system_beep(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":SYST:BEEP:STAT?")
            state = self.device.read_bool()
        else:
            self.device.write(f":SYST:BEEP:STAT {int(state)}")
        self._info("beep %s", state)
        return state

    def system_preset(self):
        self._info("preset")
        self.device.write(":SYST:PRES")

    def system_keyclick(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":SYST:KCL?")
            state = self.device.read_bool()
        else:
            self.device.write(f":SYST:KCL {int(state)}")
        self._info("keyclick %s", state)
        return state

    class PowerOnDefault(Enum):
        Reset = "RST"
        Presets = "PRES"
        Save = "SAV0"

    def system_power_on_defaults(self, default: Optional[PowerOnDefault] = None):
        if default is None:
            self.device.write(b":SYST:POS?")
            default = self.PowerOnDefault(self.device.readline())
        else:
            self.device.write(f":SYST:POS {default.value}")
        self._info("power on defaults: %s", default.name)
        return default

    def system_front_switch(self):
        self.device.write(b":SYST:FRSW?")
        val = self.device.read_bool()
        self._info("front panel switch: %s", val)
        return val

    def system_version(self):
        self.device.write(b":SYST:VERS?")
        ver = self.device.readline()
        self._info("version: %s", ver)
        return ver

    def system_error(self):
        self.device.write(b":SYST:ERR?")
        err, msg = self.device.readline().split(",")
        self._info("error: %s", msg)
        return err, msg[1:-1]

    def system_autozero(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":SYST:AZER:STAT?")
            state = self.device.read_bool()
        else:
            self.device.write(f":SYST:AZER:STAT {int(state)}")
        self._info("autozero %s", state)
        return state

    def system_clear(self):
        self._info("system clear")
        self.device.write(b":SYST:CLE")

    def system_key(self, key: int | str):
        self._info("key %s", key)

        if isinstance(key, str):
            key = {
                "SHIFT": 1,
                "DCV": 2,
                "ACV": 3,
                "DCI": 4,
                "ACI": 5,
                "R2": 6,
                "Ω2": 6,
                "R4": 7,
                "Ω4": 7,
                "FREQ": 8,
                "RANGE_UP": 11,
                "AUTO": 12,
                "RANGE_DOWN": 13,
                "ENTER": 14,
                "RIGHT": 15,
                "TEMP": 16,
                "LOCAL": 17,
                "EX_TRIG": 18,
                "TRIG": 19,
                "STORE": 20,
                "RECALL": 21,
                "FILTER": 22,
                "REL": 23,
                "LEFT": 24,
                "OPEN": 26,
                "CLOSE": 27,
                "STEP": 28,
                "SCAN": 29,
                "DIGITS": 30,
                "RATE": 31,
                "EXIT": 32,
            }[key]

        self.device.write(f":SYST:KEY {int(key)}")

    def system_local(self):
        self._info("system local")
        self.device.write(b":SYST:LOC")

    def system_remote(self):
        self._info("system remote")
        self.device.write(b":SYST:REM")

    def system_lock(self):
        self._info("system lock keys")
        self.device.write(b":SYST:RWL")

    def system_line_frequency(self):
        self.device.write(b":SYST:LFR?")
        freq = self.device.read_float()
        self._info("Line Frequency %s", freq)
        return freq

    # TRACE subsystem
    def trace_clear(self):
        self._info("trace clear")
        self.device.write(b":TRAC:CLE")

    def trace_free(self):
        self._info("trace free?")
        self.device.write(b":TRAC:FREE?")
        return [int(x) for x in self.device.readline().split(",")]

    def trace_points(self, points: Optional[int] = None):
        if points is None:
            self.device.write(b":TRAC:POIN?")
            points = self.device.read_int()
        else:
            if not 2 <= points <= 1024:
                raise ValueError(f"2 <= points <= 1024 (got {points})")
            self.device.write(f":TRAC:POIN {points}")
        self._info("trace points %d", points)
        return points

    class Feed(Enum):
        Sense = "SENS"
        Calculate = "CALC"
        NONE = "NONE"

    def trace_feed(self, feed: Optional[Feed] = None):
        if feed is None:
            self.device.write(b":TRAC:FEED?")
            feed = self.Feed(self.device.readline())
        else:
            self.device.write(f":TRAC:FEED {feed.value}")
        self._info("trace feed %s", feed.name)
        return feed

    class FeedControl(Enum):
        Never = "NEV"
        Next = "NEXT"

    def trace_feed_control(self, ctrl: Optional[FeedControl] = None):
        if ctrl is None:
            self.device.write(b":TRAC:FEED:CONT?")
            ctrl = self.FeedControl(self.device.readline())
        else:
            self.device.write(f":TRAC:FEED:CONT {ctrl.value}")
        self._info("trace feed control %s", ctrl.name)
        return ctrl

    def trace_data(self, raw: bool = False):
        self._info("trace data?")
        self.device.write(b":TRAC:DATA?")
        data = self.device.readline()
        if raw:
            return data
        try:
            return [float(x) for x in data.split(",")]
        except ValueError:
            return data

    # TRIGger subsystem
    def immediate(self):
        self._info("trigger init")
        self.device.write(b":INIT")

    def continuous(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":INIT:CONT?")
            state = self.device.read_bool()
        else:
            self.device.write(f":INIT:CONT {int(state)}")
        self._info("trigger continuous %s", state)
        return state

    def abort(self):
        self._info("trigger abort")
        self.device.write(b":ABOR")

    def trigger_count(self, count: Optional[int] = None):
        if count is None:
            self.device.write(b":TRIG:COUN?")
            count = self.device.read_int()
        else:
            if count == 0:
                self.device.write(b":TRIG:COUN INF")
            else:
                if not 1 <= count <= 9999:
                    raise ValueError(f"1 <= count <= 9999 (got {count})")
                self.device.write(f":TRIG:COUN {count}")
        self._info("trigger count %d", count)
        return count

    def trigger_delay(self, delay: Optional[float] = None):
        if delay is None:
            self.device.write(b":TRIG:DEL?")
            delay = self.device.read_float()
        else:
            if not 0 <= delay <= 999999.999:
                raise ValueError(f"0 <= delay <=  999999.999 (got {delay})")
            self.device.write(f":TRIG:DEL {delay}")
        self._info("trigger delay %g", delay)
        return delay

    class TriggerSource(Enum):
        Immediate = "IMM"
        Timer = "TIM"
        Manual = "MAN"
        Bus = "BUS"
        External = "EXT"

    def trigger_source(self, source: Optional[TriggerSource] = None):
        if source is None:
            self.device.write(b":TRIG:SOUR?")
            source = self.TriggerSource(self.device.readline())
        else:
            self.device.write(f":TRIG:SOUR {source.value}")
        self._info("trigger source %s", source.name)
        return source

    def trigger_timer(self, interval: Optional[float] = None):
        if interval is None:
            self.device.write(b":TRIG:TIM?")
            interval = self.device.read_float()
        else:
            if not 0.001 <= interval <= 999999.999:
                raise ValueError(f"0.001 <= interval <=  999999.999 (got {interval})")
            self.device.write(f":TRIG:TIM {interval:.3f}")
        self._info("trigger timer: %g", interval)
        return interval

    def trigger_signal(self):
        self._info("signal")
        self.device.write(b":TRIG:SIGN")

    def sample_count(self, samples: Optional[int] = None):
        if samples is None:
            self.device.write(b":SAMP:COUN?")
            samples = self.device.read_int()
        else:
            if not 1 <= samples <= 1024:
                raise ValueError(f"1 <= samples <= 1024 (got {samples})")
            self.device.write(f":SAMP:COUN {samples}")
        self._info("sample count %d", samples)
        return samples

    # UNIT subsystem
    class TempUnit(Enum):
        C = "C"
        F = "F"
        K = "K"

    def temperature_unit(self, unit: Optional[TempUnit] = None):
        if unit is None:
            self.device.write(b":UNIT:TEMP?")
            unit = self.TempUnit(self.device.readline())
        else:
            self.device.write(f":UNIT:TEMP {unit.value}")
        self._info("temperature unit: °%s", unit.name)
        return unit

    class VoltageType(Enum):
        AC = "AC"
        DC = "DC"

    class VoltageUnit(Enum):
        V = "V"
        dB = "DB"
        dBm = "DBM"

    def voltage_unit(self, t: VoltageType, unit: Optional[VoltageUnit] = None):
        if unit is None:
            self.device.write(f":UNIT:VOLT:{t.value}?")
            unit = self.VoltageUnit(self.device.readline())
        else:
            self.device.write(f":UNIT:VOLT:{t.value} {unit.value}")
        self._info("voltage %s unit: °%s", t.name, unit.name)
        return unit

    def dB_reference(self, t: VoltageType, reference: Optional[float] = None):
        if reference is None:
            self.device.write(f":UNIT:VOLT:{t.value}:DB:REF?")
            reference = self.device.read_float()
        else:
            if not 1e-7 <= reference <= 1000:
                raise ValueError(f"1e-7 <= reference <= 1000 (got {reference})")
            self.device.write(f":UNIT:VOLT:{t.value}:DB:REF {reference}")
        self._info("voltage %s dB reference: °%g", t.name, reference)
        return reference

    def dBm_impedance(self, t: VoltageType, impedance: Optional[float] = None):
        if impedance is None:
            self.device.write(f":UNIT:VOLT:{t.value}:DBM:IMP?")
            impedance = self.device.read_float()
        else:
            if not 1 <= impedance <= 9999:
                raise ValueError(f"1 <= impedance <= 9999 (got {impedance})")
            self.device.write(f":UNIT:VOLT:{t.value}:DBM:IMP {impedance}")
        self._info("Voltage %s dBm impedance: °%g", t.name, impedance)
        return impedance

    class Reader:
        def __init__(self, device):
            self.device = device

        def __next__(self):
            return self.device.fetch()

    def continous_reading(self):
        return self.Reader(self)
