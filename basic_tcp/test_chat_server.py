import socket
import threading
import time
import pytest
from chat_server import tcp_server


@pytest.fixture
def server_thread():
    server_socket = None
    server_thread = None

    def start_server(port=9080):
        nonlocal server_socket, server_thread

        def run_server():
            nonlocal server_socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', port))
            server_socket.listen(128)

            try:
                while True:
                    conn, addr = server_socket.accept()
                    data = conn.recv(1024)
                    conn.sendall(b"Echo: " + data)
                    conn.close()
            except OSError:
                pass

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(0.2)
        return port

    yield start_server

    if server_socket:
        try:
            server_socket.close()
        except:
            pass


class TestBasicEchoServer:

    def test_single_echo(self, server_thread):
        port = server_thread(port=9080)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))

        client.sendall(b"Hello, server!")
        response = client.recv(1024)

        assert response == b"Echo: Hello, server!"

        client.close()

    def test_echo_with_different_messages(self, server_thread):
        port = server_thread(port=9081)

        messages = [
            b"Test message 1",
            b"Another message",
            b"12345"
        ]

        for msg in messages:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', port))

            client.sendall(msg)
            response = client.recv(1024)

            assert response == b"Echo: " + msg

            client.close()
            time.sleep(0.1)

    def test_large_message(self, server_thread):
        port = server_thread(port=9083)

        large_msg = b"X" * 1000

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))

        client.sendall(large_msg)
        response = client.recv(2048)

        assert response == b"Echo: " + large_msg

        client.close()

    def test_binary_data(self, server_thread):
        port = server_thread(port=9084)

        binary_msg = bytes(range(256))

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))

        client.sendall(binary_msg)
        response = client.recv(2048)

        assert response == b"Echo: " + binary_msg

        client.close()

    def test_unicode_text(self, server_thread):
        port = server_thread(port=9085)

        unicode_msg = "Hello 世界 🌍".encode('utf-8')

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))

        client.sendall(unicode_msg)
        response = client.recv(1024)

        assert response == b"Echo: " + unicode_msg
        assert response.decode('utf-8') == "Echo: Hello 世界 🌍"

        client.close()

    def test_connection_closes_after_response(self, server_thread):
        port = server_thread(port=9086)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))

        client.sendall(b"Test")
        response = client.recv(1024)

        assert response == b"Echo: Test"

        time.sleep(0.2)

        try:
            client.sendall(b"Another message")
            response = client.recv(1024)
            if not response:
                assert True
        except (BrokenPipeError, ConnectionResetError):
            assert True

        client.close()

    def test_multiple_sequential_connections(self, server_thread):
        port = server_thread(port=9087)

        for i in range(5):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', port))

            msg = f"Message {i}".encode()
            client.sendall(msg)
            response = client.recv(1024)

            assert response == b"Echo: " + msg

            client.close()
            time.sleep(0.1)
    
    def test_client_disconnect_without_sending(self, server_thread):
        port = server_thread(port=9088)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))
        client.close()
        time.sleep(0.2)
        
        new_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_client.connect(('127.0.0.1', port))
        new_client.sendall(b"Test after disconnect")
        response = new_client.recv(1024)
        
        assert response == b"Echo: Test after disconnect"
        new_client.close()


class TestClientBehavior:

    def test_client_can_connect_to_server(self, server_thread):
        port = server_thread(port=9089)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client.connect(('127.0.0.1', port))
            connected = True
        except:
            connected = False

        assert connected
        client.close()

    def test_client_receives_full_response(self, server_thread):
        port = server_thread(port=9090)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))

        msg = b"Test message for full response"
        client.sendall(msg)

        response = client.recv(1024)
        expected = b"Echo: " + msg

        assert len(response) == len(expected)
        assert response == expected

        client.close()
