"""The guard: may this server fetch the URL it was handed?

Session 13's rule: a server that fetches a URL it was given can be pointed at things
only it can reach (a cloud metadata address, a local validator, the office network).
So the URL is judged before any request is made, from the string and from what its
host name resolves to. Standard library only.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return (
        not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
        and ip.is_global
    )


def is_public_url(url: str) -> bool:
    """True only for an https URL whose host is, and resolves only to, public addresses."""
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return False
    if parts.scheme != "https" or not host:
        return False
    try:  # a literal IP address needs no DNS
        return _is_public(host)
    except ValueError:
        pass
    try:
        resolved = {info[4][0] for info in socket.getaddrinfo(host, parts.port or 443)}
    except (socket.gaierror, UnicodeError, OSError):
        # Decision: a name that does not resolve is refused. The server cannot say
        # where it points, and an address it cannot check is not an address it trusts.
        return False
    # Every address the name resolves to must be public: one private answer is enough
    # to point the fetch at the inside.
    return bool(resolved) and all(_is_public(address) for address in resolved)
