#!/usr/bin/env python
from dataclasses import dataclass, field, make_dataclass
from enum import Enum
from typing import Optional
import time

from SCPI import SCPI
from SCPI.device import SerialDevice

INF = float("9.9E+37")


class HP54600(SCPI):
    BAUDRATE = 9600  # default baudrate
    CHANNELS = 2
    ERRORS = {
        -100: "Command error (unknown command)",
        -101: "Invalid character",
        -102: "Syntax error",
        -103: "Invalid separator",
        -104: "Data type error",
        -105: "GET not allowed",
        -108: "Parameter not allowed",
        -109: "Missing parameter",
        -112: "Program mnemonic too long",
        -113: "Undefined header",
        -121: "Invalid character in number",
        -123: "Numeric overflow",
        -124: "Too many digits",
        -128: "Numeric data not allowed",
        -130: "Suffix error",
        -131: "Invalid suffix",
        -138: "Suffix not allowed",
        -140: "Character data error",
        -141: "Invalid character data",
        -144: "Character data too long",
        -148: "Character data not allowed",
        -150: "String data error",
        -151: "Invalid string data",
        -158: "String data not allowed",
        -160: "Block data error",
        -161: "Invalid block data",
        -168: "Block data not allowed",
        -170: "Expression error",
        -171: "Invalid expression",
        -178: "Expression data not allowed",
        -200: "Execution error",
        -211: "Trigger ignored",
        -221: "Settings conflict",
        -222: "Data out of range",
        -223: "Too much data",
        -310: "System error",
        -350: "Too many errors",
        -400: "Query error",
        -410: "Query INTERRUPTED",
        -420: "Query UNTERMINATED",
        -430: "Query DEADLOCKED",
        -440: "Query UNTERMINATED after indefinite response",
    }

    def __init__(self, device: SerialDevice | str):
        super().__init__(device, baudrate=self.BAUDRATE)

    @staticmethod
    def _bool_state(state: bool):
        return "ON" if state else "OFF"

    @staticmethod
    def _bool(state: str):
        return {"ON": True, "OFF": False}[state]

    def learn(self):
        self._info("learn")
        self.device.write(b"*LRN?")
        return self.device.read_binary_block()

    def options(self):
        self._info("options")
        self.device.write(b"*OPT?")
        return self.device.readline()

    def recall(self, reg: int):
        if not 1 <= reg <= 16:
            raise ValueError(f"register {reg} invalid")

        self._info("recall from register %s", reg)
        self.device.write(f"*RCL {reg}")

    def save(self, reg: int):
        if not 1 <= reg <= 16:
            raise ValueError(f"register {reg} invalid")

        self._info("save to register %s", reg)
        self.device.write(f"*SAV {reg}")

    # Root commands
    def astore(self):
        self._info("astore")
        self.device.write(b":AST")

    def autoscale(self):
        self._info("autoscale")
        self.device.write(b":AUT")

    def blank(self, disp: str):
        self._info("blank")
        self.device.write(f":BLAN {disp}")

    def digitize(self, channels: list[int]):
        self._info("digitize %s", channels)
        self.device.write(f':DIG CHAN{",CHAN".join(channels)}')

    def dither(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(":DITH?")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":DITH {self._bool_state(state)}")
        self._info("dither %s", state)
        return state

    def erase(self, pmem: Optional[int] = None):
        if pmem is None:
            self.device.write(b":ERAS")
        else:
            if not 1 <= pmem <= 2:
                raise ValueError(f"pixel memory does not exist: {pmem}")
            self.device.write(f":ERAS PMEM{pmem}")
        self._info("Erase pixel memory %s", pmem or "")
        return pmem

    def menu(self, menu: Optional[int] = None):
        if menu is None:
            self.device.write(b":MENU?")
            menu = self.device.read_int()
        else:
            if not 0 <= menu <= 16:
                raise ValueError(f"menu does not exist: {menu}")
            self.device.write(f":MENU {menu}")
        self._info("menu page: %d", menu)
        return menu

    def merge(self, val: int):
        self.device.write(f":MERG PMEM{val}")
        self._info("store pixel memory %d", val)

    def print(self, highres: bool = False):
        self._info("printscreen (may take several minutes!)")
        self.device.write(f':PRIN?{"HIR" if highres else ""}')

        time.sleep(1)

        data = self.device.read_raw(223048 if highres else 19767)

        # discard final newline
        self.device.readline()

        return data

    # gpcl6 -dSAFER -dBATCH -dNOPAUSE -dNOOUTERSAVE -sDEVICE=pngmonod -r720 -sOutputFile=%.png %.pcl
    def print_to_file(self, filename, highres: bool = False, chunksize: int = 4096):
        self._info("printscreen to file (may take several minutes!)")
        self.device.write(f':PRIN?{" HIR" if highres else ""}')

        time.sleep(1)

        length = 223048 if highres else 19767
        with open(filename, mode="wb") as f:
            while length > 0:
                length -= f.write(self.device.read_raw(min(length, chunksize)))

        # discard final newline
        self.device.readline()

        self._info("wrote %s", filename)

    def run(self):
        self._info("run")
        self.device.write(b":RUN")

    def status(self):
        self._info("status")

    def stop(self):
        self._info("stop")
        self.device.write(b":STOP")

    def ter(self):
        self._info("ter")
        self.device.write(b":TER")
        return self.device.read_bool()

    def vautoscale(self):
        self._info("TV trigger autoscale")
        self.device.write(b":VAUT")

    def view(self, channel: Optional[int] = None, pmem: Optional[int] = None):
        if channel is not None:
            self._assert_channel(channel)
            self.device.write(f":VIEW CHAN{channel}")
            self._info("displaying channel %d", channel)
        elif pmem is not None:
            if not 1 <= pmem <= 2:
                raise ValueError(f"pixel memory does not exist: {pmem}")
            self.device.write(f":VIEW PMEM{channel}")
            self._info("displaying pixel memory %d", pmem)
        else:
            raise TypeError("specify channel or pmem")

    # ACQuire commands
    def acquire_complete(self, crit: Optional[int] = None):
        if crit is None:
            self.device.write(b":ACQ:COMP?")
            crit = self.device.read_int()
        else:
            if not 0 <= crit <= 100:
                raise ValueError("invalid completion criteria")
            self.device.write(f":ACQ:COMP {crit}")
        self._info("acquire criteria: %d", crit)
        return crit

    def acquire_count(self, count: Optional[int] = None):
        if count is None:
            self.device.write(b":ACQ:COUN?")
            count = self.device.read_int()
        else:
            if count not in (8, 64, 256):
                raise ValueError("invalid acquire count")
            self.device.write(f":ACQ:COUN {count}")
        self._info("acquire count: %d", count)
        return count

    def acquire_points(self):
        self._info("acquire points?")
        self.device.write(b":ACQ:POIN?")
        return self.device.read_int()

    def acquire_setup(self):
        self._info("acquire setup?")
        self.device.write(b":ACQ:SET?")
        return self.device.readline()
        # ACQuire:TYPE{NORM | AVER | PEAK}; COUNt<count_argument>; POINts<points_argument>; COMPlete<complete_argument><NL>

    class AcquireType(Enum):
        Normal = "NORM"
        Peak = "PEAK"
        Average = "AVER"

    def acquire_type(self, t: Optional[AcquireType] = None):
        if t is None:
            self.device.write(b":ACQ:TYPE?")
            t = self.AcquireType(self.device.readline())
        else:
            self.device.write(f":ACQ:TYPE {t.value}")
        self._info("acquire type: %s", t.name)
        return t

    # MEASure commands
    def measure_all(self):
        self.device.write(b":MEAS:ALL?")

        @dataclass(frozen=True)
        class Measurments:
            frequency: float
            period: float
            nwidth: float
            pwidth: float
            risetime: float
            falltime: float
            Vpp: float
            dutycycle: float
            Vrms: float
            Vmax: float
            Vmin: float
            Vtop: float
            Vbase: float
            Vavg: float
            Vamp: float
            Vovershoot: float
            Vpreshoot: float

        return Measurments(*[float(i) for i in self.device.readline().split(",")])

    class Slope(Enum):
        Positive = "+"
        Negative = "-"

    DelayParameter = make_dataclass(
        "DelayParameter",
        [
            ("edge", int, field(default=1)),
            ("slope", Slope, field(default=Slope.Positive)),
        ],
        namespace={
            "__str__": lambda self: f"{self.edge if self.slope.value == '+' else -self.edge}"
        },
    )

    def measurment_delay_parameters(
        self, edges: Optional[list[DelayParameter, DelayParameter]] = None
    ):
        if edges is None:
            self.device.write(b":MEAS:DEF? DEL")
            edges = list(float(i) for i in self.device.readline().split(","))
        else:
            self.device.write(f":MEAS:DEF DEL,{edges[0]},{edges[1]}")
        self._info("measurment delay parameters: %s,%s", *edges)
        return edges

    class Thresholds(Enum):
        T1090 = "T1090"
        T2080 = "T2080"
        Voltage = "VOLTage"

    def measurment_thresholds(self, thresholds: Optional[Thresholds] = None):
        if thresholds is None:
            self.device.write(b":MEAS:THR?")
            thresholds = self.Thresholds(self.device.readline())
        else:
            self.device.write(f":MEAS:THR {thresholds.value}")
        self._info("measurment thresholds: %s", thresholds.name)
        return thresholds

    def measurment_voltage_thresholds(
        self, lower: Optional[float] = None, upper: Optional[float] = None
    ):
        if lower is None:
            self.device.write(b":MEAS:LOW")
            lower = self.device.read_float()
        else:
            self.device.write(f":MEAS:LOW {lower}")

        if upper is None:
            self.device.write(b":MEAS:UPP")
            upper = self.device.read_float()
        else:
            self.device.write(f":MEAS:UPP {upper}")

        self._info("measurment voltage thresholds: %g, %g", lower, upper)
        return lower, upper

    class Marker(Enum):
        TimeStart = "TSTA"
        TimeStop = "TSTO"
        PhaseStart = "PSTA"
        PhaseStop = "PSTO"
        VoltageStart = "VSTA"
        VoltageStop = "VSTO"
        VoltagePercentageStart = "VPSTA"
        VoltagePercentageStop = "VPSTO"

    def measurment_marker(self, marker: Marker, position: Optional[float] = None):
        if position is None:
            self.device.write(f":MEAS:{marker.value}?")
            position = self.device.read_float()
        else:
            _position = position
            if marker in (self.Marker.TimeStart, self.Marker.TimeStop):
                # TODO: needs M/U/N/P prefixes?
                _position = f"{position}S"
            self.device.write(f":MEAS:{marker.value} {_position}")
        self._info("marker %s at position: %g", marker.name, position)
        return position

    def measure_voltage_at(self, t: float):
        self._info("measure voltage at: %gs", t)
        self.device.write(f":MEAS:VTIM? {t}")
        return self.device.read_float()

    def measure_voltage_transition(
        self, voltage: float, slope: Slope, occurrence: int = 1
    ):
        self.device.write(f":MEAS:TVOL? {voltage},{slope.value}{occurrence}")
        val = self.device.read_float()
        self._info(
            "voltage transition %d %s at %gV: %g", occurrence, slope.name, voltage, val
        )
        return val

    def measurement_scratch(self):
        self._info("measurements scratch")
        self.device.write(b":MEAS:SCR")

    def measurement_set100(self):
        self._info("measurements set 100%")
        self.device.write(b":MEAS:SET100")

    def measurement_set360(self):
        self._info("measurements set 360°")
        self.device.write(b":MEAS:SET360")

    def measurment_show(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":MEAS:SHOW?")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":MEAS:SHOW {self._bool_state(state)}")
        self._info("measurment show: %s", state)
        return state

    def measurment_source(self, channel: Optional[int] = None):
        if channel is None:
            self.device.write(b":MEAS:SOUR?")
            channel = self.device.read_int()
        else:
            self._assert_channel(channel)
            self.device.write(f":MEAS:SOUR CHAN {channel}")
        self._info("measurment source: %d", channel)
        return channel

    class Measurement(Enum):
        Delay = "DEL"  # Settings conflict
        DutyCycle = "DUTY"
        FallTime = "FALL"
        Frequency = "FREQ"
        NegativeWidth = "NWID"
        Overshoot = "OVER"
        Period = "PER"
        Phase = "PHAS"  # Settings conflict
        PostiveWidth = "PWID"
        Preshoot = "PRES"
        RiseTime = "RIS"
        TimeDelta = "TDEL"
        VAmplitude = "VAMP"
        VAverage = "VAV"
        VBase = "VBAS"
        VDelta = "VDEL"
        VMax = "VMAX"
        VMin = "VMIN"
        VTop = "VTOP"
        Vpp = "VPP"
        Vrms = "VRMS"

    def measurement_enable(self, measurement: Measurement):
        self._info(f"enable {measurement.name} measurement")
        self.device.write(f":MEAS:{measurement.value}")

    def measure(self, measurement: Measurement):
        self._info(f"measure {measurement.name}")
        self.device.write(f":MEAS:{measurement.value}?")
        return self.device.read_float()

    # SYSTem commands
    def system_display(self, text: str):
        self._info("display %s", text)
        self.device.write(f':SYST:DSP "{text}"')

    def system_error(self):
        self._info("error?")
        self.device.write(b":SYST:ERR?")
        return self.device.read_int()

    # CHANnel commands
    @classmethod
    def _assert_channel(cls, channel: int, max_channel=None):
        if not 1 <= channel <= (max_channel or cls.CHANNELS):
            raise ValueError(f"channel {channel} invalid for selected function")

    def channel_BWlimit(self, channel: int, state: Optional[bool] = None):
        # The bandwidth limit filter can be used on channels 1 and 2.
        self._assert_channel(channel, 2)

        if state is None:
            self.device.write(f":CHAN{channel}:BWL?")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":CHAN{channel}:BWL {self._bool_state(state)}")
        self._info("channel %d bandwidth limit: %s", channel, state)
        return state

    class ChannelCoupling(Enum):
        AC = "AC"
        DC = "DC"
        GND = "GND"

    def channel_coupling(
        self, channel: int, coupling: Optional[ChannelCoupling] = None
    ):
        self._assert_channel(channel)

        if coupling is None:
            self.device.write(f":CHAN{channel}:COUP?")
            coupling = self.ChannelCoupling(self.device.readline())
        else:
            self.device.write(f":CHAN{channel}:COUP {coupling.value}")
        self._info("channel %d coupling: %s", channel, coupling.name)
        return coupling

    def channel_invert(self, channel: int, state: Optional[bool] = None):
        # You can set the inversion for channels 1 and 2.
        self._assert_channel(channel, 2)

        if state is None:
            self.device.write(f":CHAN{channel}:INV?")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":CHAN{channel}:INV {self._bool_state(state)}")
        self._info("channel %d invert: %s", channel, state)
        return state

    class MathMode(Enum):
        Off = "OFF"
        Plus = "PLUS"
        Subtract = "SUBT"

    def channel_math(self, math: Optional[MathMode] = None):
        if math is None:
            self.device.write(b":CHAN:MATH?")
            math = self.MathMode(self.device.readline())
        else:
            self.device.write(f":CHAN:MATH {math.value}")
        self._info("channel math: %s", math.name)
        return math

    def channel_offset(self, channel: int, offset: Optional[float] = None):
        self._assert_channel(channel)

        if offset is None:
            self.device.write(f":CHAN{channel}:OFFS?")
            offset = self.device.read_float()
        else:
            self.device.write(f":CHAN{channel}:OFFS {offset}")
        self._info("channel %d offset: %g", channel, offset)
        return offset

    class ProbeAttenuation(Enum):
        X1 = "X1"
        X10 = "X10"
        X100 = "X100"

    def channel_probe(
        self, channel: int, attenuation: Optional[ProbeAttenuation] = None
    ):
        self._assert_channel(channel)

        if attenuation is None:
            self.device.write(f":CHAN{channel}:PROB?")
            attenuation = self.ProbeAttenuation(self.device.readline())
        else:
            self.device.write(f":CHAN{channel}:PROB {attenuation.value}")
        self._info("channel %d attenuation: %s", channel, attenuation.name)
        return attenuation

    def channel_range(self, channel: int, r: Optional[float] = None):
        self._assert_channel(channel)

        if r is None:
            self.device.write(f":CHAN{channel}:RANG?")
            r = self.device.read_float()
        else:
            self.device.write(f":CHAN{channel}:RANG {r}")
        self._info("channel %d range: %g", channel, r)
        return r

    def channel_setup(self, channel: int):
        self._assert_channel(channel)

        self._info("channel setup?")
        self.device.write(f":CHAN{channel}:SET?")
        return self.device.readline()

    def channel_vernier(self, channel: int, state: Optional[bool] = None):
        # You may select VERNier for channels 1 and 2.
        self._assert_channel(channel, 2)

        if state is None:
            self.device.write(f":CHAN{channel}:VERN?")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":CHAN{channel}:VENR {self._bool_state(state)}")
        self._info("channel %d vernier: %s", channel, state)
        return state

    # TIMebase commands
    def timebase_delay(self, delay: Optional[float] = None):
        if delay is None:
            self.device.write(b":TIM:DEL?")
            delay = self.device.read_float()
        else:
            self.device.write(f":TIM:DEL {delay}")
        self._info("timebase delay: %g", delay)
        return delay

    class TimebaseMode(Enum):
        Normal = "NORM"
        Delayed = "DEL"
        XY = "XY"
        Rolling = "ROLL"

    def timebase_mode(self, mode: Optional[TimebaseMode] = None):
        if mode is None:
            self.device.write(b":TIM:MODE?")
            mode = self.TimebaseMode(self.device.readline())
        else:
            self.device.write(f":TIM:MODE {mode.value}")
        self._info("timebase mode: %s", mode.name)
        return mode

    def timebase_range(self, r: Optional[float] = None):
        if r is None:
            self.device.write(b":TIM:RANG?")
            r = self.device.read_float()
        else:
            self.device.write(f":TIM:RANG {r}")
        self._info("timebase delay: %g", r)
        return r

    class TimebaseReference(Enum):
        Left = "LEFT"
        Center = "CENT"
        Right = "RIGH"

    def timebase_reference(self, ref: Optional[TimebaseReference] = None):
        if ref is None:
            self.device.write(b":TIM:REF?")
            ref = self.TimebaseReference(self.device.readline())
        else:
            self.device.write(f":TIM:REF {ref.value}")
        self._info("timebase reference: %s", ref.name)
        return ref

    def timebase_setup(self):
        self._info("timebase setup?")
        self.device.write(b":TIM:SET?")
        # 'TIMEBASE:MODE NORM;RANGE +1.52000000E-003;DELAY +0.00000000E+000;REF CENT;VERN OFF'
        return self.device.readline()

    def timebase_vernier(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":TIM:VERN?")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":TIM:VERN {self._bool_state(state)}")
        self._info("timebase vernier: %s", state)
        return state

    # TRACe commands
    @classmethod
    def _assert_trace(cls, trace: int):
        if not 1 <= trace <= 100:
            raise ValueError(f"trace {trace} does not exist")

    def trace_clear(self, trace: int):
        self._assert_trace(trace)

        self._info("trace clear %s", trace)
        self.device.write(f":TRAC:CLEAR {trace}")

    def trace_data(self, trace: int, data: Optional[bytes] = None):
        self._assert_trace(trace)

        if data is None:
            self.device.write(f":TRAC:DATA? {trace}")
            data = self.device.read_binary_block()
            self._debug("received %d bytes of data", len(data))
        else:
            self.device.write(f":TRAC:DATA {trace},")
            self.device.write_binary_block(data)
        self._info("trace data %s", trace)
        return data

    def trace_mode(self, trace: int, state: Optional[bool] = None):
        self._assert_trace(trace)

        if state is None:
            self.device.write(f":TRAC:MODE? {trace}")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":TRAC:MODE {trace},{self._bool_state(state)}")
        self._info("trace mode %s: %s", trace, state)
        return state

    def trace_save(self, trace: int):
        self._assert_trace(trace)

        self._info("trace save %s", trace)
        self.device.write(f":TRAC:SAVE {trace}")

    # DISPlay commands
    def display_connect(self, state: Optional[bool] = None):
        if state is None:
            self.device.write(b":DISP:CONN?")
            state = self._bool(self.device.readline())
        else:
            self.device.write(f":DISP:CONN {self._bool_state(state)}")
        self._info("display connect: %s", state)
        return state

    def display_data(self, data: Optional[bytes] = None):
        if data is None:
            self.device.write(b":DISP:DATA?")
            data = self.device.read_binary_block()
            self._debug("received %d bytes of display data", len(data))
        else:
            if len(data) != 16256:
                raise ValueError("display data must be 16256 bytes")
            self._debug("writing %d bytes of display data", len(data))
            self.device.write(b":DISP:DATA ", end=None)
            self.device.write_binary_block(data)
        self._info("display data")
        return data

    def display_row(self, row: Optional[int] = None):
        if row is None:
            self.device.write(b":DISP:ROW?")
            row = self.device.read_int()
        else:
            if not 1 <= row <= 20:
                raise ValueError(f"1 <= row <=  20 (got {row})")
            self.device.write(f":DISP:ROW {row}")
        self._info("display row: %s", row)
        return row

    def display_column(self, col: Optional[int] = None):
        if col is None:
            self.device.write(b":DISP:COL?")
            col = self.device.read_int()
        else:
            if not 0 <= col <= 63:
                raise ValueError(f"0 <= col <=  63 (got {col})")
            self.device.write(f":DISP:COL {col}")
        self._info("display column: %s", col)
        return col

    def display_clear(self):
        self._info("clear user text area")
        self.device.write(b":DISP:TEXT BLAN")

    def display_line(self, text: str):
        self.device.write(f':DISP:LINE "{text}"')
        self._info("display text: %s", text)

    def display_lines(self, text: str):
        for line in text.splitlines():
            self.display_line(line)

    class GridType(Enum):
        On = "ON"
        Off = "OFF"
        Simple = "SIMP"
        TV = "TV"

    def display_grid(self, grid: Optional[GridType] = None):
        if grid is None:
            self.device.write(b":DISP:GRID?")
            grid = self.GridType(self.device.readline())
        else:
            self.device.write(f":DISP:GRID {grid.value}")
        self._info("display grid type: %s", grid.name)
        return grid

    def display_inverse(self, inverse: Optional[bool] = None):
        if inverse is None:
            self.device.write(b":DISP:INV?")
            inverse = self.device.read_bool()
        else:
            self.device.write(f":DISP:INV {int(inverse)}")
        self._info("display inverse: %s", inverse)
        return inverse

    def display_pixel(self, xy: tuple[int, int], intensity: Optional[int] = None):
        if intensity is None:
            self.device.write(f":DISP:PIX? {xy[0]},{xy[0]}")
            intensity = self.device.read_int()
        else:
            self.device.write(f":DISP:PIX {xy[0]},{xy[0]},{intensity}")
        self._info("display pixel intensity: %s,%s: %s", xy[0], xy[1], intensity)
        return intensity

    # WAVeform commands
    class ByteOrder:
        LSBfirst = "LSB"
        MSBfirst = "MSB"

    def waveform_byteorder(self, order: Optional[ByteOrder] = None):
        if order is None:
            self.device.write(b":WAV:BYT?")
            order = self.ByteOrder(self.device.readline())
        else:
            self.device.write(f":WAV:BYT {order.value}")
        self._info("waveform byteorder: %s", order.name)
        return order

    def waveform_data(self, data: Optional[bytes] = None):
        if data is None:
            self.device.write(b":WAV:DATA?")
            data = self.device.read_binary_block()
        else:
            self.device.write(f":WAV:DATA {data}")
        self._info("waveform data %d bytes", len(data))
        return data

    class WaveformFormat(Enum):
        Ascii = "ASC"
        Word = "WORD"
        Byte = "BYTE"

    def waveform_format(self, form: Optional[WaveformFormat] = None):
        if form is None:
            self.device.write(b":WAV:FORM?")
            form = self.WaveformFormat(self.device.readline())
        else:
            self.device.write(f":WAV:FORM {form.value}")
        self._info("waveform format: %s", form.name)
        return form

    def waveform_points(self, points: Optional[int] = None):
        if points is None:
            self.device.write(b":WAV:POIN?")
            points = self.device.read_int()
        else:
            self.device.write(f":WAV:POIN {points}")
        self._info("waveform points: %d", points)
        return points

    def waveform_preamble(self):
        self.device.write(b":WAV:PRE?")

        F = self.WaveformFormat
        T = self.AcquireType

        @dataclass(frozen=True)
        class Preamble:
            format: F
            type: T
            points: int
            xincrement: float
            xorigin: float
            xreference: int
            yincrement: float
            yorigin: float
            yreference: int

        data = self.device.readline().split(",")

        return Preamble(
            {0: F.Ascii, 1: F.Byte, 2: F.Word}[int(data[0])],
            {0: T.Average, 1: T.Normal, 2: T.Peak}[int(data[1])],
            int(data[2]),
            float(data[4]),
            float(data[5]),
            int(data[6]),
            float(data[7]),
            float(data[8]),
            int(data[9]),
        )

    def waveform_source(self, source: Optional[int] = None, function: bool = False):
        if source is None:
            self.device.write(f':WAV:SOUR{":FUNC" if function else ""}?')
            source = int(self.device.readline().strip()[4:])
        else:
            self.device.write(f':WAV:SOUR{":FUNC " if function else " CHAN"}{source}')
        self._info("waveform source: %d", source)
        return source

    def waveform_type(self):
        self.device.write(b":WAV:TYPE?")
        t = self.AcquireType(self.device.readline())
        self._info("waveform type: %s", t.name)
        return t

    def waveform_xincrement(self, val: Optional[float] = None):
        if val is None:
            self.device.write(b":WAV:XINC?")
            val = self.device.read_float()
        else:
            self.device.write(f":WAV:XINC {val}")
        self._info("waveform X increment: %g", val)
        return val

    def waveform_xorigin(self, val: Optional[float] = None):
        if val is None:
            self.device.write(b":WAV:XOR?")
            val = self.device.read_float()
        else:
            self.device.write(f":WAV:XOR {val}")
        self._info("waveform X origin: %g", val)
        return val

    def waveform_xreference(self, val: Optional[int] = None):
        if val is None:
            self.device.write(b":WAV:XREF?")
            val = self.device.read_int()
        else:
            self.device.write(f":WAV:XREF {val}")
        self._info("waveform X reference: %d", val)
        return val

    def waveform_yincrement(self, val: Optional[float] = None):
        if val is None:
            self.device.write(b":WAV:YINC?")
            val = self.device.read_float()
        else:
            self.device.write(f":WAV:YINC {val}")
        self._info("waveform Y increment: %g", val)
        return val

    def waveform_yorigin(self, val: Optional[float] = None):
        if val is None:
            self.device.write(b":WAV:YOR?")
            val = self.device.read_float()
        else:
            self.device.write(f":WAV:YOR {val}")
        self._info("waveform Y origin: %g", val)
        return val

    def waveform_yreference(self, val: Optional[int] = None):
        if val is None:
            self.device.write(b":WAV:YREF?")
            val = self.device.read_int()
        else:
            self.device.write(f":WAV:YREF {val}")
        self._info("waveform Y reference: %d", val)
        return val


class HP54601(HP54600):
    CHANNELS = 4

    class ChannelRange(Enum):
        Low = "LOW"
        High = "HIGH"

    def channel_range(self, channel: int, r: Optional[float | ChannelRange] = None):
        self._assert_channel(channel)

        if channel <= 2:
            if r is None:
                self.device.write(f":CHAN{channel}:RANG?")
                r = self.device.read_float()
            else:
                self.device.write(f":CHAN{channel}:RANG {r}")
            self._info("channel %d range: %g", channel, r)
        else:
            if r is None:
                self.device.write(f":CHAN{channel}:RANG?")
                r = self.ChannelRange(self.device.readline())
            else:
                self.device.write(f":CHAN{channel}:RANG {r.value}")
            self._info("channel %d range: %g", channel, r.value)
        return r


class HP54602(HP54601):
    pass


class HP54610(HP54600):
    class Impedance(Enum):
        Fifty = "FIFT"
        High = "ONEM"

    def channel_input(self, channel: int, impedance: Optional[Impedance] = None):
        self._assert_channel(channel)

        if impedance is None:
            self.device.write(f":CHAN{channel}:INP?")
            impedance = self.Impedance(self.device.readline())
        else:
            self.device.write(f":CHAN{channel}:INP {impedance.value}")
        self._info("channel %d input impedance: %s", channel, impedance.name)
        return impedance

    class PMode(Enum):
        Manual = "MAN"
        Auto = "AUT"

    # For the 54610, 54615 and 54616 oscilloscopes
    def probe_mode(self, channel: int, mode: Optional[PMode] = None):
        self._assert_channel(channel)

        if mode is None:
            self.device.write(f":CHAN{channel}:PROB?")
            mode = self.PMode(self.device.readline())
        else:
            self.device.write(f":CHAN{channel}:PROB {mode.value}")
        self._info("channel %d probe mode: %s", channel, mode.name)
        return mode

    # For the 54610, 54615 and 54616
    class ProbeAttenuation(Enum):
        X1 = "X1"
        X10 = "X10"
        X20 = "X20"
        X100 = "X100"

    # For the 54610, 54615 and 54616 oscilloscopes
    def channel_protect(self, channel: int, state: Optional[bool] = None):
        self._assert_channel(channel)

        if state is None:
            self.device.write(f":CHAN{channel}:PROT?")
            state = self.device.readline()
        else:
            self.device.write(f":CHAN{channel}:PROT {self._bool_state(state)}")
        self._info("channel %d protection: %s", channel, state)
        return state

    # For the 54610, 54615 and 54616 oscilloscopes
    def channel_skew(self, channel: int, skew: Optional[float] = None):
        if channel != 2:
            raise ValueError("channel skew only applicable to channel 2")

        if skew is None:
            self.device.write(b":CHAN2:SKEW?")
            skew = self.device.read_float()
        else:
            self.device.write(f":CHAN2:SKEW {skew}")
        self._info("channel skew: %g", skew)
        return skew


class HP54616C(HP54610):
    class Palette(Enum):
        Default = 0
        Alternate1 = 1
        Alternate2 = 2
        Alternate3 = 3
        Inverse1 = 4
        Inverse2 = 5
        Monochrome = 6

    # This command is only valid for 54616C
    def display_palette(self, palette: Optional[Palette] = None):
        if palette is None:
            self.device.write(b":DISP:PAL?")
            palette = self.Palette(self.device.readline())
        else:
            self.device.write(f":DISP:PAL {palette.value}")
        self._info("display palette: %s", palette.name)
        return palette
