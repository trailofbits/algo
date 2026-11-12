"""Send DNS replies through the real DNSCrypt proxy and production IP blocklist."""

import base64
import ipaddress
import os
import shutil
import socket
import ssl
import struct
import subprocess
import threading
import time
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest
from ansible.template import trust_as_template
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def dns_question(address):
    record_type = 1 if address.version == 4 else 28
    return b"\x05probe\x04test\x00" + struct.pack("!HH", record_type, 1)


def query(port, address):
    packet = struct.pack("!6H", 1234, 0x0100, 1, 0, 0, 0) + dns_question(address)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(0.2)
        client.sendto(packet, ("127.0.0.1", port))
        response, _ = client.recvfrom(4096)
    return response


def write_certificate(tmp_path):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "localhost")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    cert_file, key_file = tmp_path / "certificate.pem", tmp_path / "key.pem"
    cert_file.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_file.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    key_file.chmod(0o600)
    return cert_file, key_file


def dns_reply(packet, address):
    question_end = packet.index(b"\x00", 12) + 5
    question = packet[12:question_end]
    if question[:-4].lower() != b"\x05probe\x04test\x00":
        return packet[:2] + struct.pack("!5H", 0x8183, 1, 0, 0, 0) + question
    record_type = 1 if address.version == 4 else 28
    header = packet[:2] + struct.pack("!5H", 0x8180, 1, 1, 0, 0)
    record = struct.pack("!HHHIH", 0xC00C, record_type, 1, 60, len(address.packed))
    return header + question + record + address.packed


def doh_stamp(port):
    # DNSCrypt's documented DoH stamp format: protocol, properties, and length-prefixed fields.
    fields = [b"127.0.0.1", b"", f"localhost:{port}".encode(), b"/dns-query"]
    stamp = b"\x02" + b"\x00" * 8 + b"".join(bytes([len(field)]) + field for field in fields)
    return "sdns://" + base64.urlsafe_b64encode(stamp).decode().rstrip("=")


@pytest.fixture
def dns_proxy(network_runtime, ansible_templar, tmp_path):
    binary = shutil.which("dnscrypt-proxy")
    assert binary, "Install dnscrypt-proxy in the network test container"
    answer = {"address": ipaddress.ip_address("8.8.8.8")}

    class Resolver(BaseHTTPRequestHandler):
        def do_GET(self):
            encoded = parse_qs(urlparse(self.path).query)["dns"][0]
            self.respond(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))

        def do_POST(self):
            self.respond(self.rfile.read(int(self.headers["Content-Length"])))

        def respond(self, packet):
            reply = dns_reply(packet, answer["address"])
            self.send_response(200)
            self.send_header("Content-Type", "application/dns-message")
            self.send_header("Content-Length", str(len(reply)))
            self.end_headers()
            self.wfile.write(reply)

    template = "{{ lookup('template', 'roles/dns/templates/ip-blacklist.txt.j2') }}"
    (tmp_path / "blocked.txt").write_text(ansible_templar().template(trust_as_template(template)))
    cert_file, key_file = write_certificate(tmp_path)
    with HTTPServer(("127.0.0.1", 0), Resolver) as upstream:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(cert_file, key_file)
        upstream.socket = context.wrap_socket(upstream.socket, server_side=True)
        upstream_port = upstream.server_address[1]
        with socket.socket() as reserve:
            reserve.bind(("127.0.0.1", 0))
            port = reserve.getsockname()[1]
        config = tmp_path / "dnscrypt.toml"
        config.write_text(
            f"listen_addresses = ['127.0.0.1:{port}']\n"
            "server_names = ['test']\ncache = false\nnetprobe_timeout = 0\n"
            "blocked_query_response = 'refused'\n"
            "[blocked_ips]\nblocked_ips_file = 'blocked.txt'\n"
            f"[static.test]\nstamp = '{doh_stamp(upstream_port)}'\n"
        )
        thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        thread.start()
        with (tmp_path / "dnscrypt.log").open("w+") as log:
            process = subprocess.Popen(
                [binary, "-config", str(config)],
                stdout=log,
                stderr=log,
                env={**os.environ, "SSL_CERT_FILE": str(cert_file)},
            )
            try:
                wait_for_proxy(process, port, answer["address"], log)
                yield port, answer
            finally:
                process.terminate()
                process.wait(timeout=5)
                upstream.shutdown()
                thread.join(timeout=5)


def wait_for_proxy(process, port, address, log):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and process.poll() is None:
        try:
            query(port, address)
            return
        except TimeoutError:
            continue
    log.seek(0)
    pytest.fail(f"DNSCrypt proxy did not start: {log.read()}")


@pytest.mark.parametrize(
    "address",
    [
        "0.0.0.0",  # noqa: S104 -- DNS answer test data, not a listening address.
        "10.1.2.3",
        "127.0.0.1",
        "169.254.169.254",
        "172.16.0.1",
        "172.31.255.254",
        "192.168.1.1",
        "::",
        "::1",
        "fc00::1",
        "fcff::1",
        "fd00::1",
        "fdff:ffff::1",
        "fe80::1",
        "febf:ffff::1",
        "2001:db8::1",
        "::ffff:192.168.1.1",
    ],
)
def test_private_dns_answers_are_blocked(dns_proxy, address):
    port, answer = dns_proxy
    answer["address"] = ipaddress.ip_address(address)
    response = query(port, answer["address"])
    assert response[3] & 0x0F == 5, f"DNSCrypt allowed the rebinding address {address}"


@pytest.mark.parametrize(
    "address",
    ["8.8.8.8", "172.15.255.255", "172.32.0.1", "2606:4700::1111", "::ffff:8.8.8.8"],
)
def test_public_dns_answers_are_preserved(dns_proxy, address):
    port, answer = dns_proxy
    answer["address"] = ipaddress.ip_address(address)
    response = query(port, answer["address"])
    assert response[3] & 0x0F == 0
    assert response.endswith(answer["address"].packed)
