"""Regression coverage for the web-grounding SSRF boundary, without LLM calls."""

import configparser
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket
import ssl
import threading
from unittest.mock import Mock

import pytest

from tinytroupe import ConfigManager, config_manager
from tinytroupe.agent.grounding import WebPagesGroundingConnector
from tinytroupe.utils import config as config_utils
from tinytroupe.utils import web
from tinytroupe.utils.json import JsonSerializableRegistry

pytestmark = pytest.mark.core

# Mock DNS response only; the test server binds exclusively to loopback.
_UNSPECIFIED_IPV4 = "0.0.0.0"  # nosec B104


@pytest.fixture(autouse=True)
def secure_config(monkeypatch):
    """Isolate policy from local configuration and other tests."""
    for key, value in {
        "web_grounding_enforce_security": True,
        "web_grounding_allowed_hosts": "",
        "web_grounding_allow_localhost": False,
        "web_grounding_allow_private_networks": False,
    }.items():
        monkeypatch.setitem(config_manager._config, key, value)


def address(ip="93.184.216.34", port=80):
    """Build a getaddrinfo result for deterministic DNS tests."""
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    sockaddr = (ip, port, 0, 0) if family == socket.AF_INET6 else (ip, port)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)


def response(status=200, content=b"<p>Hello</p>", location=None):
    """Build an HTTP response with real charset header parsing."""
    result = Mock(status=status)
    result.headers = Message()
    result.read.return_value = content
    result.getheader.return_value = location
    return result


@pytest.fixture
def network(monkeypatch):
    """Capture all resolution/connection attempts without external requests."""
    dns = Mock(return_value=[address()])
    connect = Mock()
    connection = Mock()
    connection.getresponse.return_value = response()
    factory = Mock(return_value=connection)
    monkeypatch.setattr(web.socket, "getaddrinfo", dns)
    monkeypatch.setattr(web, "_connect", connect)
    monkeypatch.setattr(web.http.client, "HTTPConnection", factory)
    return dns, connect, connection


def test_empty_allowlist_blocks_before_dns(network):
    dns, connect, _ = network
    with pytest.raises(PermissionError, match="ALLOWED_HOSTS"):
        web.fetch_web_page("https://example.com")
    dns.assert_not_called()
    connect.assert_not_called()


@pytest.mark.parametrize("host", ["example.com.evil.test", "sub.example.com", "evil.test"])
def test_host_allowlist_is_exact(host, network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    with pytest.raises(PermissionError):
        web.fetch_web_page(f"http://{host}")
    network[0].assert_not_called()


@pytest.mark.parametrize("host", ["EXAMPLE.COM", "example.com."])
def test_host_normalization(host, network):
    config_manager.update("web_grounding_allowed_hosts", " Example.COM. ")
    assert web.fetch_web_page(f"http://{host}/page?q=1") == "<p>Hello</p>"
    network[0].assert_called_once_with(
        "example.com", 80, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
    )
    network[2].request.assert_called_once_with(
        "GET", "/page?q=1", headers={"User-Agent": "TinyTroupe"}
    )
    network[2].close.assert_called_once()


def test_unicode_url_preserves_escaped_path_and_query(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    web.fetch_web_page("http://example.com/caf\u00e9?q=%2F\u00e9#fragment")
    network[2].request.assert_called_once_with(
        "GET", "/caf%C3%A9?q=%2F%C3%A9", headers={"User-Agent": "TinyTroupe"}
    )


@pytest.mark.parametrize("host", ["*.example.com", "https://example.com", "example.com:80"])
def test_invalid_allowlist_entries_fail_closed(host, network):
    config_manager.update("web_grounding_allowed_hosts", host)
    with pytest.raises(ValueError):
        web.fetch_web_page("http://example.com")
    network[1].assert_not_called()


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "ftp://example.com", "http://user:pass@example.com",
    "http://example.com/\r\nHeader:value", "http://example.com:bad", "http://[::1",
    "http://[fe80::1%25eth0]", "http://example.com/a b", "http://example.com:0",
])
def test_malformed_or_unsupported_urls(url, network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    with pytest.raises(ValueError):
        web.fetch_web_page(url)
    network[1].assert_not_called()


@pytest.mark.parametrize("ip", [
    "127.0.0.1",
    _UNSPECIFIED_IPV4,
    "10.1.2.3", "172.16.1.1", "192.168.1.1",
    "169.254.169.254", "168.63.129.16", "100.100.100.200", "192.0.2.1", "224.0.0.1",
    "::1", "::", "fc00::1", "fd00:ec2::254", "fe80::1", "ff02::1", "2001:db8::1",
    "::ffff:127.0.0.1", "::ffff:10.0.0.1", "64:ff9b::a00:1", "2002:a00:1::1",
])
def test_non_public_dns_results_are_blocked(ip, network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    network[0].return_value = [address(ip)]
    with pytest.raises(PermissionError, match="prohibited address"):
        web.fetch_web_page("http://example.com")
    network[1].assert_not_called()


def test_mixed_public_and_private_dns_is_blocked(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    network[0].return_value = [address(), address("127.0.0.1")]
    with pytest.raises(PermissionError):
        web.fetch_web_page("http://example.com")
    network[1].assert_not_called()


@pytest.mark.parametrize("host,url", [
    ("127.0.0.1", "http://127.0.0.1"),
    ("::1", "http://[::1]"),
])
def test_allowlisted_loopback_literals_are_still_blocked(host, url, network):
    config_manager.update("web_grounding_allowed_hosts", host)
    network[0].return_value = [address(host)]
    with pytest.raises(PermissionError, match="prohibited address"):
        web.fetch_web_page(url)
    network[1].assert_not_called()


@pytest.mark.parametrize("ip,key", [
    ("127.0.0.1", "web_grounding_allow_localhost"),
    ("::1", "web_grounding_allow_localhost"),
    ("10.0.0.1", "web_grounding_allow_private_networks"),
    ("fd00::1", "web_grounding_allow_private_networks"),
])
def test_local_permissions_still_require_allowlist(ip, key, network):
    config_manager.update(key, True)
    network[0].return_value = [address(ip)]
    with pytest.raises(PermissionError, match="ALLOWED_HOSTS"):
        web.fetch_web_page("http://example.com")
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    assert web.fetch_web_page("http://example.com") == "<p>Hello</p>"


def test_private_permission_does_not_enable_loopback_or_metadata(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    config_manager.update("web_grounding_allow_private_networks", True)
    for ip in ("127.0.0.1", "169.254.169.254", "fd00:ec2::254", "168.63.129.16"):
        network[0].return_value = [address(ip)]
        with pytest.raises(PermissionError):
            web.fetch_web_page("http://example.com")
    network[1].assert_not_called()


def test_https_preserves_certificate_verification_and_hostname(network, monkeypatch):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    context = ssl.create_default_context()
    wrap_socket = Mock()
    monkeypatch.setattr(context, "wrap_socket", wrap_socket)
    create_context = Mock(return_value=context)
    monkeypatch.setattr(web.ssl, "create_default_context", create_context)
    assert web.fetch_web_page("https://example.com") == "<p>Hello</p>"
    create_context.assert_called_once_with()
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    wrap_socket.assert_called_once_with(
        network[1].return_value, server_hostname="example.com"
    )


def test_https_explicitly_sets_minimum_tls_version(network, monkeypatch):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    context = Mock()
    monkeypatch.setattr(web.ssl, "create_default_context", Mock(return_value=context))
    web.fetch_web_page("https://example.com")
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2


def test_tls_failure_is_not_suppressed(network, monkeypatch):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    context = Mock()
    context.wrap_socket.side_effect = ssl.SSLCertVerificationError("invalid certificate")
    monkeypatch.setattr(web.ssl, "create_default_context", Mock(return_value=context))
    with pytest.raises(ssl.SSLCertVerificationError):
        web.fetch_web_page("https://example.com")
    network[2].close.assert_called_once()


@pytest.mark.parametrize("location", ["http://evil.test", "http://127.0.0.1", "//evil.test"])
def test_redirect_destination_must_be_allowlisted(location, network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    network[2].getresponse.return_value = response(302, location=location)
    with pytest.raises(PermissionError, match="ALLOWED_HOSTS"):
        web.fetch_web_page("http://example.com")
    assert network[1].call_count == 1
    network[2].close.assert_called_once()


def test_dns_is_rechecked_on_same_host_redirect(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    network[0].side_effect = [[address()], [address("127.0.0.1")]]
    network[2].getresponse.return_value = response(302, location="/next")
    with pytest.raises(PermissionError, match="prohibited address"):
        web.fetch_web_page("http://example.com")
    assert network[1].call_count == 1


def test_allowed_redirect_and_charset(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com,other.test")
    final = response(content="caf\u00e9".encode("latin-1"))
    final.headers["Content-Type"] = "text/plain; charset=iso-8859-1"
    network[2].getresponse.side_effect = [
        response(302, location="http://other.test/result"), final
    ]
    assert web.fetch_web_page("http://example.com") == "caf\u00e9"
    assert network[1].call_count == 2
    assert network[2].close.call_count == 2


def test_redirect_limit(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    network[2].getresponse.return_value = response(302, location="/loop")
    with pytest.raises(ValueError, match="redirect limit"):
        web.fetch_web_page("http://example.com")
    assert network[1].call_count == web._MAX_REDIRECTS + 1


def test_exact_redirect_limit_is_allowed(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    network[2].getresponse.side_effect = [
        response(302, location="/next") for _ in range(web._MAX_REDIRECTS)
    ] + [response()]
    assert web.fetch_web_page("http://example.com") == "<p>Hello</p>"


@pytest.mark.parametrize("reply,error,match", [
    (response(302), ValueError, "Location"),
    (response(404), OSError, "HTTP 404"),
])
def test_http_failures_are_explicit(reply, error, match, network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    network[2].getresponse.return_value = reply
    with pytest.raises(error, match=match):
        web.fetch_web_page("http://example.com")
    network[2].close.assert_called_once()


def test_response_size_limit(network, monkeypatch):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    monkeypatch.setattr(web, "_MAX_RESPONSE_BYTES", 10)
    reply = response(content=b"x" * 11)
    network[2].getresponse.return_value = reply
    with pytest.raises(ValueError, match="response exceeds"):
        web.fetch_web_page("http://example.com")
    reply.read.assert_called_once_with(11)
    reply.close.assert_called_once()


def test_exact_response_size_limit_is_allowed(network, monkeypatch):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    monkeypatch.setattr(web, "_MAX_RESPONSE_BYTES", 10)
    network[2].getresponse.return_value = response(content=b"x" * 10)
    assert web.fetch_web_page("http://example.com") == "x" * 10


def test_response_and_connection_are_closed_after_read_failure(network):
    config_manager.update("web_grounding_allowed_hosts", "example.com")
    reply = response()
    reply.read.side_effect = TimeoutError("Read timed out")
    network[2].getresponse.return_value = reply
    with pytest.raises(TimeoutError):
        web.fetch_web_page("http://example.com")
    reply.close.assert_called_once()
    network[2].close.assert_called_once()


def test_connect_uses_checked_sockaddr_without_dns(monkeypatch):
    sock = Mock()
    factory = Mock(return_value=sock)
    dns = Mock(side_effect=AssertionError("Unexpected second DNS lookup"))
    monkeypatch.setattr(web.socket, "socket", factory)
    monkeypatch.setattr(web.socket, "getaddrinfo", dns)
    resolved = [address()]
    assert web._connect(resolved) is sock
    sock.connect.assert_called_once_with(("93.184.216.34", 80))
    sock.settimeout.assert_called_once_with(web._TIMEOUT)
    dns.assert_not_called()


def test_failed_connection_closes_socket_and_tries_next_address(monkeypatch):
    failed, success = Mock(), Mock()
    failed.connect.side_effect = TimeoutError("timed out")
    monkeypatch.setattr(web.socket, "socket", Mock(side_effect=[failed, success]))
    assert web._connect([address(), address("1.1.1.1")]) is success
    failed.close.assert_called_once()
    with pytest.raises(OSError, match="No addresses"):
        web._connect([])


def test_opt_out_warns_and_allows_non_allowlisted_internal_address(network, caplog):
    config_manager.update("web_grounding_enforce_security", "False")
    network[0].return_value = [address("127.0.0.1")]
    assert web.fetch_web_page("http://localhost") == "<p>Hello</p>"
    assert "security enforcement is disabled" in caplog.text
    config_manager.update("web_grounding_enforce_security", True)
    with pytest.raises(PermissionError):
        web.fetch_web_page("http://localhost")


@pytest.mark.parametrize("value", ["perhaps", "", 1, None])
def test_invalid_boolean_updates_do_not_disable_security(value):
    with pytest.raises(ValueError):
        config_manager.update("web_grounding_enforce_security", value)
    assert config_manager.get("web_grounding_enforce_security") is True


def test_shipped_defaults_and_local_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_utils, "_config", None)
    defaults = ConfigManager()
    assert defaults.get("web_grounding_enforce_security") is True
    assert set(defaults.get("web_grounding_allowed_hosts").split(",")) == {
        "microsoft.com", "www.microsoft.com",
        "google.com", "www.google.com",
        "wikipedia.org", "www.wikipedia.org", "en.wikipedia.org",
        "python.org", "www.python.org", "docs.python.org",
    }
    assert defaults.get("web_grounding_allow_localhost") is False
    assert defaults.get("web_grounding_allow_private_networks") is False
    (tmp_path / "config.ini").write_text(
        "[WebGrounding]\nALLOWED_HOSTS=example.com\nENFORCE_SECURITY=False\n",
        encoding="utf-8",
    )
    config_utils._config = None
    overrides = ConfigManager()
    assert overrides.get("web_grounding_allowed_hosts") == "example.com"
    assert overrides.get("web_grounding_enforce_security") is False


def test_missing_security_section_fails_closed(monkeypatch):
    original = config_utils.read_config_file()
    config = configparser.ConfigParser()
    config.read_dict({section: dict(original[section]) for section in original if section != "WebGrounding"})
    monkeypatch.setattr(config_utils, "_config", config)
    manager = ConfigManager()
    assert manager.get("web_grounding_enforce_security") is True
    assert manager.get("web_grounding_allowed_hosts") == ""


def test_shipped_allowlist_preserves_destination_restrictions(tmp_path, monkeypatch, network):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_utils, "_config", None)
    defaults = ConfigManager()
    config_manager.update("web_grounding_allowed_hosts", defaults.get("web_grounding_allowed_hosts"))
    assert web.fetch_web_page("http://microsoft.com") == "<p>Hello</p>"
    with pytest.raises(PermissionError, match="ALLOWED_HOSTS"):
        web.fetch_web_page("http://unlisted.example")
    with pytest.raises(PermissionError, match="ALLOWED_HOSTS"):
        web.fetch_web_page("http://unlisted.microsoft.com")
    network[0].return_value = [address("127.0.0.1")]
    with pytest.raises(PermissionError, match="prohibited address"):
        web.fetch_web_page("http://microsoft.com")
    assert network[1].call_count == 1


@pytest.mark.parametrize("loader", [
    WebPagesGroundingConnector.from_json, JsonSerializableRegistry.from_json,
])
@pytest.mark.parametrize("type_field", ["type", "json_serializable_class_name"])
def test_deserialization_cannot_override_policy(loader, type_field, network):
    data = {
        type_field: "WebPagesGroundingConnector",
        "name": "untrusted",
        "web_urls": ["http://127.0.0.1"],
        "web_grounding_enforce_security": False,
        "enforce_security": False,
    }
    with pytest.raises(PermissionError, match="ALLOWED_HOSTS"):
        loader(data, serialization_type_field_name=type_field)
    network[0].assert_not_called()
    assert config_manager.get("web_grounding_enforce_security") is True


def test_failed_fetch_is_not_marked_loaded_and_can_be_retried(monkeypatch):
    import tinytroupe.agent.grounding as grounding

    connector = WebPagesGroundingConnector()
    url = "http://example.com"
    with pytest.raises(PermissionError):
        connector.add_web_url(url)
    assert connector.loaded_web_urls == connector.web_urls == []
    fetch = Mock(return_value="<p>Grounding text</p>")
    add_documents = Mock()
    monkeypatch.setattr(grounding, "fetch_web_page", fetch)
    monkeypatch.setattr(connector, "add_documents", add_documents)
    connector.add_web_url(url)
    connector.add_web_url(url)
    fetch.assert_called_once_with(url)
    document = add_documents.call_args[0][0][0]
    assert document.id_ == url
    assert document.metadata["semantic_memory_id"] == url
    assert "Grounding text" in document.text
    assert connector.loaded_web_urls == connector.web_urls == [url]


@pytest.fixture
def local_web_server():
    """Serve harmless fixture content on an ephemeral loopback port."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.path, self.headers.get("Host")))
            if self.path in ("/redirect", "/external-redirect"):
                self.send_response(302)
                location = (
                    "/page?q=1" if self.path == "/redirect"
                    else f"http://localhost:{self.server.server_port}/secret"
                )
                self.send_header("Location", location)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><p>Local fixture content</p></html>")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("disable_security", [False, True])
def test_real_http_fetch_requires_explicit_permission(local_web_server, disable_security):
    url, requests = local_web_server
    with pytest.raises(PermissionError):
        web.fetch_web_page(url)
    assert requests == []
    if disable_security:
        config_manager.update("web_grounding_enforce_security", False)
    else:
        config_manager.update("web_grounding_allowed_hosts", "127.0.0.1")
        with pytest.raises(PermissionError):
            web.fetch_web_page(url)
        assert requests == []
        config_manager.update("web_grounding_allow_localhost", True)
    assert "Local fixture content" in web.fetch_web_page(url + "/page?q=1")
    assert requests == [("/page?q=1", url.removeprefix("http://"))]


def test_real_redirects_are_checked_before_following(local_web_server):
    url, requests = local_web_server
    config_manager.update("web_grounding_allowed_hosts", "127.0.0.1")
    config_manager.update("web_grounding_allow_localhost", True)
    assert "Local fixture content" in web.fetch_web_page(url + "/redirect")
    assert [path for path, _ in requests] == ["/redirect", "/page?q=1"]
    requests.clear()
    with pytest.raises(PermissionError, match="ALLOWED_HOSTS"):
        web.fetch_web_page(url + "/external-redirect")
    assert [path for path, _ in requests] == ["/external-redirect"]
