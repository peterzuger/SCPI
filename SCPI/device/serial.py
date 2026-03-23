#!/usr/bin/env python
import logging

import serial

from .util import Device


class SerialDevice(Device):
    def __init__(self, port, baudrate, name=None, end=b"\n"):
        super().__init__(name or port, end)

        self.port = port
        self.baudrate = baudrate
        self._ser = None

        self.open()

    def open(self):
        if self._ser is None:
            self._ser = serial.Serial(self.port, self.baudrate)

    def close(self):
        if self._ser:
            self._ser.close()
            self._ser = None

    def baudrate(self, baudrate):
        self._debug(f"changing baudrate from {self._ser.baudrate} to {baudrate}")
        self._ser.baudrate = baudrate

    def _read(self, n=1):
        return self._ser.read(n)

    def _readline(self):
        return self._ser.readline().strip()

    def _write(self, buf):
        return self._ser.write(buf)
