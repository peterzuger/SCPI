#!/usr/bin/env python
import logging
from enum import IntFlag
from typing import Optional

from .device import Device, make_device

logger = logging.getLogger(__name__)


class SCPI:
    """Implements the commands that *almost* all devices support. This includes:"""

    def __init__(self, device: Device, **kwargs):
        self.device = make_device(device, **kwargs)

    def _log(self, level, msg, *args):
        logger.log(level, "%s %s", self.device.name, msg % args)

    def _debug(self, msg, *args):
        self._log(logging.DEBUG, msg, *args)

    def _info(self, msg, *args):
        self._log(logging.INFO, msg, *args)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.device.close()

    # helper methods
    @staticmethod
    def _bool_state(state: bool):
        return "ON" if state else "OFF"

    # IEEE-488.2 common commands and queries
    def identification(self) -> str:
        self.device.write(b"*IDN?")
        identification = self.device.readline()
        self._info("identification code: %s", identification)
        return identification

    def reset(self):
        self._info("reset")
        # ensure previous commands are ignored with the initial newline
        self.device.write(b"\n*RST")

    def test(self):
        self._info("self test")
        self.device.write(b"*TST?")
        return not self.device.read_bool()

    def operation_complete(self):
        self._info("operation complete?")
        self.device.write(b"*OPC?")

        # TODO: timeout
        while True:
            ret = self.device.readline()
            if "1" in ret:
                return True
        return False

    def wait(self):
        self._info("wait")
        self.device.write(b"*WAI")

    def clear(self):
        self._info("clear")
        self.device.write(b"*CLS")

    class EventStatusRegister(IntFlag):
        OperationComplete = 1
        TriggerQuery = 2
        QueryError = 4
        DeviceDependentError = 8
        ExecutionError = 16
        CommandError = 32
        UserRequest = 64
        PowerON = 128

    def event_status_enable(self, mask: Optional[EventStatusRegister] = None):
        if mask is None:
            self.device.write(b"*ESE?")
            mask = self.EventStatusRegister(self.device.read_int())
        else:
            self.device.write(f"*ESE {mask.value}")
        self._info("Event Status Register mask %s", mask.name)
        return mask

    def event_status_register(self):
        self.device.write(b"*ESR?")
        val = self.EventStatusRegister(self.device.read_int())
        self._info("Event Status Register: %s", val.name)
        return val

    class ServiceRequestRegister(IntFlag):
        MeasurmentSummaryBit = 1
        ErrorAvailable = 4
        QuestionableSummaryBit = 8
        MessageAvailable = 16
        EventSummaryBit = 32
        RequestService = 64
        OperationSummaryBit = 128

    def service_request_enable(self, mask: Optional[ServiceRequestRegister] = None):
        if mask is None:
            self.device.write(b"*SRE?")
            mask = self.ServiceRequestRegister(self.device.read_int())
        else:
            self.device.write(f"*SRE {mask.value}")
        self._info("Service Request Register mask %s", mask.name)
        return mask

    def service_request_register(self):
        self.device.write(b"*STB?")
        val = self.ServiceRequestRegister(self.device.read_int())
        self._info("Service Request Register: %s", val.name)
        return val

    def trigger(self):
        self._info("trigger")
        self.device.write(b"*TRG")
