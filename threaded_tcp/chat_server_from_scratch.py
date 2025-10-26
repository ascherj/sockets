import socket
import threading

def handle_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received data: {data}")
            print(f"Decoded data: {data.decode()}")
            conn.sendall(b"Echo: " + data)
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    except KeyboardInterrupt:
        print(f"Client {addr} disconnected")
    finally:
        conn.close()
        print(f"Connection with client {addr} closed")

def tcp_server():
    server = socket.create_server(('localhost', 8080))
    server.listen(128)
    print("Server is listening on port 8080")
    try:
        while True:
            conn, addr = server.accept()
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
