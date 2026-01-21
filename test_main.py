"""Tests for pui - Process Port Manager."""

import socket
import subprocess
import sys
import time

import psutil
import pytest

from main import get_port_processes


def can_list_connections() -> bool:
    """Check if we have permission to list network connections."""
    try:
        psutil.net_connections(kind="tcp")
        return True
    except psutil.AccessDenied:
        return False


requires_net_permissions = pytest.mark.skipif(
    not can_list_connections(),
    reason="Requires elevated privileges to list network connections",
)


def get_free_port() -> int:
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
def http_server():
    """Start a Python HTTP server and yield its port and process."""
    port = get_free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for server to start listening
    for _ in range(50):
        try:
            with socket.create_connection(("localhost", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail(f"Server failed to start on port {port}")

    yield port, proc

    # Cleanup
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=5)


@requires_net_permissions
def test_get_port_processes_finds_server(http_server: tuple[int, subprocess.Popen]):
    """Test that get_port_processes() finds a running server."""
    port, proc = http_server

    processes = get_port_processes()
    ports_found = [p[0] for p in processes]

    assert port in ports_found, f"Expected port {port} in {ports_found}"

    # Verify the PID matches
    matching = [p for p in processes if p[0] == port]
    assert len(matching) == 1
    assert matching[0][1] == proc.pid


@requires_net_permissions
def test_kill_process_from_port_list(http_server: tuple[int, subprocess.Popen]):
    """Test that we can find and kill a process using get_port_processes()."""
    port, proc = http_server

    # Find the process using our interface
    processes = get_port_processes()
    matching = [p for p in processes if p[0] == port]
    assert len(matching) == 1

    pid = matching[0][1]

    # Kill using psutil (same as pui does)
    process = psutil.Process(pid)
    process.terminate()
    process.wait(timeout=5)

    # Verify process is gone
    assert proc.poll() is not None, "Process should have terminated"

    # Verify it no longer appears in port list
    processes_after = get_port_processes()
    ports_after = [p[0] for p in processes_after]
    assert port not in ports_after, f"Port {port} should no longer be listening"
