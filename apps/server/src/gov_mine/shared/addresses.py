"""The network addresses a host name stands for, and which of them the crawler must never reach:
anything not globally routable, such as private, loopback and link-local addresses (SSRF)."""

import asyncio
import socket
from ipaddress import IPv4Address, IPv6Address, ip_address

type IPAddress = IPv4Address | IPv6Address


def literal_address(host: str) -> IPAddress | None:
    """The address `host` is written as, or None when it is a name."""
    try:
        return ip_address(host)
    except ValueError:
        return None


def is_public(address: IPAddress) -> bool:
    """Whether `address` is globally routable: not private, loopback, link-local, unspecified,
    shared (100.64.0.0/10) or kept for documentation, its IPv4-mapped form included."""
    return address.is_global


async def resolve(host: str) -> list[IPAddress]:
    """Every address the system resolver gives for `host`. Raises `OSError` when there is
    none."""
    infos = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return [ip_address(info[4][0]) for info in infos]


__all__ = ["IPAddress", "is_public", "literal_address", "resolve"]
