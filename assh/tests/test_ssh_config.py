"""Tests which conern SSHConfig"""
import io
from assh.ssh_config import SSHConfig


def test_host_line():
    hostname = "destination"
    conf = SSHConfig()
    conf.add_host(hostname)

    stream = io.StringIO()
    conf.write(stream)

    content = stream.getvalue()

    assert f"Host {hostname}" in content


def test_kv_pairs():
    hostname = "destination"
    conf = SSHConfig()
    conf.add_host(hostname, Key1="test", Key2="test-again")

    stream = io.StringIO()
    conf.write(stream)

    content = stream.getvalue()
    lines = content.split("\n")

    assert "\tKey1 test" in lines
    assert "\tKey2 test-again" in lines


def test_multiple_hosts():
    host_a = "host-a"
    host_b = "host-b"

    conf = SSHConfig()
    conf.add_host(host_a, HostAUnique="test")
    conf.add_host(host_b, HostBUnique="foobar")

    stream = io.StringIO()
    conf.write(stream)

    content = stream.getvalue()
    expected = f"""Host {host_a}
\tHostAUnique test
Host {host_b}
\tHostBUnique foobar
"""

    assert content == expected
