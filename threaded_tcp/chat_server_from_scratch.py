import socket
import threading


clients = {}
clients_lock = threading.Lock()
server = None

def broadcast(message, sender_sock=None):
    dead_clients = []
    with clients_lock:
        for client_sock in clients:
            if client_sock == sender_sock or client_sock == server:
                continue
            try:
                client_sock.send(f"[{clients[sender_sock]}] {message.decode()}".encode())
            except Exception as e:
                print(f"Error sending message to {client_sock}: {e}")
                dead_clients.append(client_sock)
    for sock in dead_clients:
        with clients_lock:
            remove_client(sock)

def remove_client(sock):
    username = None
    if sock in clients:
        username = clients[sock]
        del clients[sock]
        print(f"{username} left ({len(clients)} clients)")
    return username

def handle_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"[{clients[conn]}] {data.decode().strip()}")
            broadcast(data, sender_sock=conn)
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        with clients_lock:
            username = remove_client(conn)
        broadcast(f"{username} left the chat!\n".encode(), sender_sock=server)
        conn.close()

def tcp_server():
    global server
    server = socket.create_server(('localhost', 8080))
    server.listen(128)
    print("Server is listening on port 8080")
    clients[server] = "Server"
    try:
        while True:
            conn, addr = server.accept()
            conn.send(b"Enter your name: ")
            username = conn.recv(1024).decode().strip()
            with clients_lock:
                clients[conn] = username
                print(f"{username} joined ({len(clients)} clients)")
            broadcast(f"{username} joined the chat!\n".encode(), sender_sock=server)
            print(f"New connection from {addr}")
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("Server is shutting down")
        server.close()

if __name__ == "__main__":
    tcp_server()
