#!/usr/bin/env python
import logging

from .util import Device


class usbtmcDevice(Device):
    def __init__(self, port, name=None, end=b"\n"):
        super().__init__(name or port, end)

        self.port = port
        self._f = None

        self.open()

    def open(self):
        if self._f is None:
            self._f = open(self.port, "wb+")

    def close(self):
        if self._f:
            self._f.close()
            self._f = None

    def _read(self, n=1):
        return self._f.read(n)

    def _readline(self):
        return self._f.readline()

    def _write(self, buf):
        return self._f.write(buf)
