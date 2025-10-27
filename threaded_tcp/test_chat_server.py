import socket
import threading
import time
import pytest
from chat_server import tcp_server, broadcast, remove_client, handle_client, clients, clients_lock


@pytest.fixture
def reset_clients():
    with clients_lock:
        clients.clear()
    yield
    with clients_lock:
        clients.clear()


@pytest.fixture
def server_thread():
    server = None
    thread = None
    
    def start_server(port=8081):
        nonlocal server, thread
        thread = threading.Thread(
            target=tcp_server,
            kwargs={'port': port, 'host': '127.0.0.1'},
            daemon=True
        )
        thread.start()
        time.sleep(0.2)
        return thread
    
    yield start_server
    

class TestClientConnection:
    
    def test_single_client_connects(self, reset_clients, server_thread):
        server_thread(port=8082)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 8082))
        
        prompt = client.recv(1024)
        assert prompt == b"Enter your name: "
        
        client.send(b"Alice\n")
        time.sleep(0.1)
        
        with clients_lock:
            assert len(clients) == 1
            assert "Alice" in clients.values()
        
        client.close()
        time.sleep(0.1)
    
    def test_multiple_clients_connect(self, reset_clients, server_thread):
        server_thread(port=8083)
        
        clients_list = []
        usernames = ["Alice", "Bob", "Charlie"]
        
        for username in usernames:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', 8083))
            client.recv(1024)
            client.send(f"{username}\n".encode())
            time.sleep(0.1)
            clients_list.append(client)
        
        with clients_lock:
            assert len(clients) == 3
            for username in usernames:
                assert username in clients.values()
        
        for client in clients_list:
            client.close()
        time.sleep(0.1)


class TestBroadcasting:
    
    def test_message_broadcast_to_other_clients(self, reset_clients, server_thread):
        server_thread(port=8084)
        
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('127.0.0.1', 8084))
        client1.recv(1024)
        client1.send(b"Alice\n")
        time.sleep(0.2)
        
        client1.recv(1024)
        
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('127.0.0.1', 8084))
        client2.recv(1024)
        client2.send(b"Bob\n")
        time.sleep(0.2)
        
        join_msg = client1.recv(1024)
        assert b"Bob" in join_msg and b"joined" in join_msg
        
        client1.send(b"Hello everyone!\n")
        time.sleep(0.1)
        
        msg = client2.recv(1024)
        assert b"Alice" in msg
        assert b"Hello everyone!" in msg
        
        client1.close()
        client2.close()
        time.sleep(0.1)
    
    def test_sender_does_not_receive_own_message(self, reset_clients, server_thread):
        server_thread(port=8085)
        
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('127.0.0.1', 8085))
        client1.recv(1024)
        client1.send(b"Alice\n")
        time.sleep(0.2)
        
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('127.0.0.1', 8085))
        client2.recv(1024)
        client2.send(b"Bob\n")
        time.sleep(0.2)
        
        client1.recv(1024)
        
        client1.send(b"Test message\n")
        time.sleep(0.2)
        
        msg = client2.recv(1024)
        assert b"Alice" in msg
        assert b"Test message" in msg
        
        client1.settimeout(0.3)
        try:
            unexpected = client1.recv(1024)
            assert False, f"Client should not receive own message, got: {unexpected}"
        except socket.timeout:
            pass
        
        client1.close()
        client2.close()
        time.sleep(0.1)


class TestClientDisconnection:
    
    def test_client_removed_on_disconnect(self, reset_clients, server_thread):
        server_thread(port=8086)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 8086))
        client.recv(1024)
        client.send(b"Alice\n")
        time.sleep(0.1)
        
        with clients_lock:
            assert len(clients) == 1
        
        client.close()
        time.sleep(0.2)
        
        with clients_lock:
            assert len(clients) == 0
    
    def test_disconnect_notification_broadcast(self, reset_clients, server_thread):
        server_thread(port=8087)
        
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('127.0.0.1', 8087))
        client1.recv(1024)
        client1.send(b"Alice\n")
        time.sleep(0.1)
        
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('127.0.0.1', 8087))
        client2.recv(1024)
        client2.send(b"Bob\n")
        client1.recv(1024)
        time.sleep(0.1)
        
        client1.close()
        time.sleep(0.2)
        
        msg = client2.recv(1024)
        assert b"Alice" in msg
        assert b"left" in msg
        
        client2.close()
        time.sleep(0.1)


class TestCommands:
    
    def test_list_command_shows_clients(self, reset_clients, server_thread):
        server_thread(port=8088)
        
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('127.0.0.1', 8088))
        client1.recv(1024)
        client1.send(b"Alice\n")
        time.sleep(0.1)
        
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('127.0.0.1', 8088))
        client2.recv(1024)
        client2.send(b"Bob\n")
        client1.recv(1024)
        time.sleep(0.1)
        
        client1.send(b"/list\n")
        time.sleep(0.1)
        
        response = client1.recv(1024)
        assert b"Alice" in response
        assert b"Bob" in response
        
        client1.close()
        client2.close()
        time.sleep(0.1)
    
    def test_quit_command_disconnects_client(self, reset_clients, server_thread):
        server_thread(port=8089)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 8089))
        client.recv(1024)
        client.send(b"Alice\n")
        time.sleep(0.1)
        
        with clients_lock:
            assert len(clients) == 1
        
        client.send(b"/quit\n")
        time.sleep(0.2)
        
        with clients_lock:
            assert len(clients) == 0
        
        client.close()


class TestThreadSafety:
    
    def test_concurrent_connections(self, reset_clients, server_thread):
        server_thread(port=8090)
        
        def connect_client(username):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', 8090))
            client.recv(1024)
            client.send(f"{username}\n".encode())
            time.sleep(0.5)
            client.close()
        
        threads = []
        usernames = [f"User{i}" for i in range(10)]
        
        for username in usernames:
            thread = threading.Thread(target=connect_client, args=(username,))
            threads.append(thread)
            thread.start()
        
        time.sleep(0.3)
        
        for thread in threads:
            thread.join()
        
        time.sleep(0.3)
        
        with clients_lock:
            assert len(clients) == 0


class TestRemoveClient:
    
    def test_remove_client_function(self, reset_clients):
        mock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        with clients_lock:
            clients[mock_socket] = "TestUser"
        
        username = remove_client(mock_socket)
        
        assert username == "TestUser"
        with clients_lock:
            assert mock_socket not in clients
        
        mock_socket.close()
    
    def test_remove_nonexistent_client(self, reset_clients):
        mock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        username = remove_client(mock_socket)
        
        assert username is None
        
        mock_socket.close()
