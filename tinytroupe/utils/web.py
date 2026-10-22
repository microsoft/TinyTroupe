"""HTTP fetching for webpage grounding with an opt-out, deny-by-default SSRF policy."""

import http.client
import ipaddress
import logging
import re
import socket
import ssl
from urllib.parse import quote, urljoin, urlsplit

from tinytroupe import config_manager

logger = logging.getLogger("tinytroupe")

_TIMEOUT = 30
_MAX_REDIRECTS = 5
_MAX_RESPONSE_BYTES = 10 * 1024 * 1024
_PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
)
_TRANSITION_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/32")
)
# Cloud platform endpoints that are not classified as link-local by ipaddress.
_CLOUD_PLATFORM_ADDRESSES = {
    ipaddress.ip_address("168.63.129.16"),
    ipaddress.ip_address("fd00:ec2::254"),
}


def _normalize_host(host: str) -> str:
    """Normalize exact hostnames/IP literals, rejecting patterns and URL syntax."""
    if not host or "%" in host:
        raise ValueError("Web grounding requires a hostname or an unscoped IP address")
    try:
        return ipaddress.ip_address(host).compressed
    except ValueError:
        host = host.removesuffix(".").encode("idna").decode("ascii").lower()
        if len(host) > 253 or not all(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in host.split(".")
        ):
            raise ValueError("Web grounding hosts must be exact hostnames, not URLs or patterns")
        return host


def _address_allowed(address: str, allow_localhost: bool, allow_private: bool) -> bool:
    """Classify resolved addresses; local permissions do not permit link-local/metadata IPs."""
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        elif any(ip in network for network in _TRANSITION_NETWORKS):
            return False
    if ip in _CLOUD_PLATFORM_ADDRESSES:
        return False
    if ip.is_loopback:
        return allow_localhost
    if any(ip in network for network in _PRIVATE_NETWORKS):
        return allow_private
    return ip.is_global and not ip.is_multicast


def _connect(addresses: list) -> socket.socket:
    """Connect to an already checked sockaddr without resolving the hostname again."""
    last_error = None
    for family, socktype, proto, _, sockaddr in addresses:
        sock = socket.socket(family, socktype, proto)
        try:
            sock.settimeout(_TIMEOUT)
            sock.connect(sockaddr)
            return sock
        except OSError as error:
            sock.close()
            last_error = error
    if last_error is not None:
        raise last_error
    raise OSError("No addresses resolved for web grounding")


def fetch_web_page(url: str) -> str:
    """Fetch HTTP(S) text, validating each redirect and pinning connections to checked IPs.

    Policy comes only from application configuration, never serialized connectors.
    TLS certificates and SNI use the original hostname. Environment proxies are not
    used, because they could resolve destinations outside this validation boundary.
    """
    enforce = config_manager.get("web_grounding_enforce_security", True)
    allow_localhost = config_manager.get("web_grounding_allow_localhost", False)
    allow_private = config_manager.get("web_grounding_allow_private_networks", False)
    if any(not isinstance(value, bool) for value in (enforce, allow_localhost, allow_private)):
        raise ValueError("Web grounding security settings must be booleans")
    allowed_hosts = set()
    if enforce:
        hosts = config_manager.get("web_grounding_allowed_hosts", "")
        if not isinstance(hosts, str):
            raise ValueError("Web grounding ALLOWED_HOSTS must be a comma-separated string")
        allowed_hosts = {_normalize_host(host.strip()) for host in hosts.split(",") if host.strip()}
    else:
        logger.warning(
            "Web grounding security enforcement is disabled; internal destinations are accessible."
        )

    for redirect in range(_MAX_REDIRECTS + 1):
        if not isinstance(url, str) or any(ord(char) <= 32 or ord(char) == 127 for char in url):
            raise ValueError("Web grounding requires a URL without whitespace or control characters")
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Web grounding only supports HTTP/HTTPS URLs with a hostname")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Web grounding does not support credentials in URLs")
        host = _normalize_host(parsed.hostname)
        if enforce and host not in allowed_hosts:
            raise PermissionError(f"Web grounding host '{host}' is not in ALLOWED_HOSTS")
        port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
        if port == 0:
            raise ValueError("Web grounding requires a nonzero port")
        addresses = socket.getaddrinfo(
            host, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        if enforce and any(
            not _address_allowed(address[4][0], allow_localhost, allow_private)
            for address in addresses
        ):
            raise PermissionError(f"Web grounding host '{host}' resolves to a prohibited address")

        connection = http.client.HTTPConnection(host, port, timeout=_TIMEOUT)
        response = None
        try:
            connection.sock = _connect(addresses)
            if parsed.scheme == "https":
                connection.sock = ssl.create_default_context().wrap_socket(
                    connection.sock, server_hostname=host
                )
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            path = quote(path, safe="/?:@!$&'()*+,;=%[]~")
            connection.request("GET", path, headers={"User-Agent": "TinyTroupe"})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    raise ValueError("Web grounding redirect is missing its Location header")
                if redirect == _MAX_REDIRECTS:
                    raise ValueError("Web grounding exceeded the redirect limit")
                url = urljoin(url, location)
                continue
            if not 200 <= response.status < 300:
                raise OSError(f"Web grounding request failed with HTTP {response.status}")
            content = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(content) > _MAX_RESPONSE_BYTES:
                raise ValueError("Web grounding response exceeds the 10 MiB limit")
            return content.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        finally:
            if response is not None:
                response.close()
            connection.close()
    raise ValueError("Web grounding exceeded the redirect limit")
