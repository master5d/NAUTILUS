import socket

import tunnel


def test_build_ssh_cmd_default_remote_port():
    cmd = tunnel.build_ssh_cmd(4002, "m4")
    assert cmd[0] == "ssh"
    assert "-N" in cmd
    assert "-L" in cmd
    assert "4002:localhost:4002" in cmd
    assert cmd[-1] == "m4"


def test_build_ssh_cmd_custom_ports():
    cmd = tunnel.build_ssh_cmd(5002, "m4", remote_host="127.0.0.1", remote_port=4002)
    assert "5002:127.0.0.1:4002" in cmd


def test_is_up_true_when_socket_listening():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    try:
        assert tunnel.is_up(port) is True
    finally:
        srv.close()


def test_is_up_false_on_closed_port():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.close()
    assert tunnel.is_up(port, timeout=0.3) is False
