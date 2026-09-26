"""Scenario 2 sentinel harness: network egress trap (SCENARIO2_DESIGN.md §8).

Loaded automatically by the site module when this directory is on PYTHONPATH of the app-under-test (never of the
runner). Any AF_INET/AF_INET6 connect / create_connection / getaddrinfo / sendto to a host other than loopback is
logged as a JSON line {host, port, ts, via} to $EGRESS_LOG and refused with OSError("egress blocked by harness").
AF_UNIX is always allowed. On import it writes "<EGRESS_LOG>.active" so the probe can tell the trap was loaded.
"""
import json
import os
import socket
import time

_LOCAL = {None, "", "localhost", "127.0.0.1", "::1", "0.0.0.0", "::", "ip6-localhost", "localhost.localdomain"}
_LOG = os.environ.get("EGRESS_LOG")


def _is_local(host):
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    if host in _LOCAL:
        return True
    h = str(host).strip("[]").lower()
    return h in _LOCAL or h.startswith("127.") or h.endswith(".localhost")


def _log(host, port, via):
    if not _LOG:
        return
    try:
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"host": host if not isinstance(host, bytes) else host.decode("ascii", "replace"),
                                 "port": port, "ts": time.time(), "via": via}) + "\n")
    except OSError:
        pass


def _blocked(host, port, via):
    _log(host, port, via)
    raise OSError("egress blocked by harness")


def _inet(sock):
    try:
        return sock.family in (socket.AF_INET, socket.AF_INET6)
    except Exception:
        return False


_orig_connect = socket.socket.connect
_orig_connect_ex = socket.socket.connect_ex
_orig_sendto = socket.socket.sendto
_orig_create_connection = socket.create_connection
_orig_getaddrinfo = socket.getaddrinfo


def _check_addr(sock, address, via):
    if _inet(sock) and isinstance(address, tuple) and address and not _is_local(address[0]):
        _blocked(address[0], address[1] if len(address) > 1 else None, via)


def connect(self, address):
    _check_addr(self, address, "connect")
    return _orig_connect(self, address)


def connect_ex(self, address):
    _check_addr(self, address, "connect_ex")
    return _orig_connect_ex(self, address)


def sendto(self, data, *args):
    address = args[-1] if args else None
    _check_addr(self, address, "sendto")
    return _orig_sendto(self, data, *args)


def create_connection(address, *a, **kw):
    host = address[0] if isinstance(address, tuple) and address else address
    if not _is_local(host):
        _blocked(host, address[1] if isinstance(address, tuple) and len(address) > 1 else None, "create_connection")
    return _orig_create_connection(address, *a, **kw)


def getaddrinfo(host, port, *a, **kw):
    if not _is_local(host):
        _blocked(host, port, "getaddrinfo")
    return _orig_getaddrinfo(host, port, *a, **kw)


socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
socket.socket.sendto = sendto
socket.create_connection = create_connection
socket.getaddrinfo = getaddrinfo

if _LOG:
    try:
        open(_LOG + ".active", "w").write(str(os.getpid()))
    except OSError:
        pass
