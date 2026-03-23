#!/usr/bin/env python
import logging

logger = logging.getLogger(__name__)


class _Missing:
    pass


Missing = _Missing()


class BaseDevice:
    def open(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _read(self, _):
        raise NotImplementedError()

    def _readline(self):
        raise NotImplementedError()

    def _write(self, _):
        raise NotImplementedError()


class Device(BaseDevice):
    def __init__(self, name, end):
        self.name = name
        self.end = end

    def _log(self, level, msg, *args):
        logger.log(level, "%s %s", self.name, msg % args)

    def _debug(self, msg, *args):
        self._log(logging.DEBUG, msg, *args)

    def _info(self, msg, *args):
        self._log(logging.INFO, msg, *args)

    def readline(self, decode: bool = True):
        data = self._readline()
        self._debug("readline: %.60s", data)
        if decode:
            return data.decode("utf-8")
        return data

    def write(self, buf=None, end=Missing):
        if buf:
            if isinstance(buf, str):
                self._debug('write: "%.60s"', buf[:60])
                buf = buf.encode("utf-8")
            else:
                self._debug(
                    'write: "%.60s"', buf[:60].decode("utf-8", errors="replace")
                )

            self._write(buf)

        if end:
            self._write(self.end if end is Missing else end)

    def read_int(self) -> int:
        data = self._readline()
        self._debug("read int: %s", data)
        return int(data)

    def read_float(self) -> float:
        data = self._readline()
        self._debug("read float: %s", data)
        return float(data)

    def read_bool(self) -> bool:
        data = self._readline()
        self._debug("read bool: %s", data)

        try:
            return bool(int(data))
        except ValueError:
            return True if data == b"ON" else False

    def read_string(self) -> str:
        data = self._readline().decode("utf-8")
        self._debug("read string: %s", data)
        if data[0] == '"':
            return data[1:-1]
        return data

    def write_binary_block(self, block: bytes, end=Missing):
        nb = str(len(block))
        self._write(f"#{len(nb)}{nb}".encode("utf-8"))
        self._write(block)
        if end:
            self._write(self.end if end is Missing else end)

        self._debug("write binary-block: %s bytes", nb)

    def _read_raw(self, size: int):
        read = bytearray()
        while len(read) < size:
            n = self._read(size - len(read))
            if not n:
                raise TimeoutError("read returned 0 bytes")
            read.extend(n)
        return bytes(read)

    def read_raw(self, length: int):
        self._debug("read raw %d", length)
        return self._read_raw(length)

    def read_binary_block(self) -> bytes:
        # d<length><data><\n>
        c = self._read(1)
        if c != b"#":
            self._log(logging.WARNING, f"binary block doesn't start with # ({c})")
        r = int(self._read(1))
        length = int(self._read(r))

        self._debug("read binary block length: %d", length)

        b = self._read_raw(length)

        self._read(1)
        return b
