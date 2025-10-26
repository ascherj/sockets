import socket

def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8080))
    server.listen(128)

    print("Chat server listening on port 8080")

    try:
        while True:
            conn, addr = server.accept()
            print(f"Connection object: {conn}")
            print(f"New connection from {addr}")
            data = conn.recv(1024)
            print(f"Received data: {data}")
            print(f"Decoded data: {data.decode()}")
            conn.sendall(b"Echo: " + data)
            conn.close()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.close()


if __name__ == "__main__":
    tcp_server()
