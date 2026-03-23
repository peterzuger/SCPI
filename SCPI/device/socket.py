#!/usr/bin/env python
import logging
import socket

from .util import Device


class SocketDevice(Device):
    def __init__(self, host, port, name=None, end=b"\n"):
        super().__init__(name or f"{host}:{port}", end)

        self.host = host
        self.port = port
        self._sock = None

        self.open()

    def open(self):
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))

    def close(self):
        if self._sock:
            self._sock.close()
            self._sock = None

    def _read(self, n=1):
        return self._sock.recv(n)

    def _readline(self):
        with self._sock.makefile("rb") as f:
            return f.readline().strip()

    def _write(self, buf):
        return self._sock.send(buf)
