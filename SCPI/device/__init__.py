#!/usr/bin/env python
from .util import Device
from .serial import SerialDevice
from .socket import SocketDevice


def make_device(dev, **kwargs):
    if isinstance(dev, Device):
        return dev

    if "/dev/" in dev:
        return SerialDevice(dev, baudrate=kwargs.get("baudrate"))

    if "." in dev:
        return SocketDevice(dev, kwargs.get("port"))

    raise ValueError("invalid device config")


__all__ = [
    "make_device",
    "Device",
    "SerialDevice",
    "SocketDevice",
]
