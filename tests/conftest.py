"""Shared guard: no test may reach a non-local address (R22 in docs/01-traceability.md)."""

import socket

import pytest

_LOCAL = {"127.0.0.1", "::1", "localhost", "0.0.0.0", "::"}


class NetworkBlocked(OSError):
    pass


def _host(address) -> str | None:
    if isinstance(address, tuple) and address:
        return str(address[0])
    return None  # unix sockets and other families are local


@pytest.fixture(autouse=True)
def _block_network(monkeypatch):
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def connect(self, address):
        host = _host(address)
        if host is not None and host not in _LOCAL:
            raise NetworkBlocked(f"test tried to reach {host}")
        return real_connect(self, address)

    def connect_ex(self, address):
        host = _host(address)
        if host is not None and host not in _LOCAL:
            raise NetworkBlocked(f"test tried to reach {host}")
        return real_connect_ex(self, address)

    def getaddrinfo(host, *args, **kwargs):
        if host is not None and str(host) not in _LOCAL:
            raise NetworkBlocked(f"test tried to resolve {host}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
