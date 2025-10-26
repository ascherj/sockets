import socket

def tcp_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 8080))
    client.sendall(b"Hello, server!")
    response = client.recv(1024)
    print(f"Received response data: {response}")
    print(f"Decoded response data: {response.decode()}")
    client.close()

if __name__ == "__main__":
    tcp_client()
