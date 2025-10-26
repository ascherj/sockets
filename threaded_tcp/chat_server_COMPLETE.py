import socket
import threading

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL STATE (shared across threads)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
clients = {}  # {socket: username}
clients_lock = threading.Lock()  # Prevents race conditions

# WHY A LOCK?
# Thread A: clients[sock1] = "Alice"
# Thread B: del clients[sock2]  # Happens simultaneously!
# Result: Dictionary corrupted (rare but catastrophic)
#
# With lock:
# Thread A: lock.acquire() → modify → lock.release()
# Thread B: waits... → then modifies safely


def broadcast(message, sender_sock=None):
    """
    Send message to all connected clients (except sender)

    Args:
        message: bytes to send
        sender_sock: socket of sender (skip this one)
    """
    dead_clients = []

    with clients_lock:  # Acquire lock, auto-release when done
        for client_sock in clients:
            # Don't echo back to sender
            if client_sock == sender_sock:
                continue

            try:
                client_sock.send(message)
            except:
                # Client disconnected mid-send
                dead_clients.append(client_sock)

    # Remove dead clients OUTSIDE lock to avoid nested locking
    for sock in dead_clients:
        with clients_lock:
            remove_client(sock)


def remove_client(sock):
    """Remove client from tracking (must hold lock!)"""
    username = None
    if sock in clients:
        username = clients[sock]
        del clients[sock]
        print(f"{username} left ({len(clients)} clients)")

    # Broadcast OUTSIDE the lock to avoid deadlock
    # (broadcast acquires its own lock)
    return username


def handle_client(conn, addr):
    """Handle one client connection (runs in thread)"""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 1: Get username
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    conn.send(b"Enter your name: ")
    username = conn.recv(1024).decode().strip()

    with clients_lock:
        clients[conn] = username

    print(f"{username} joined from {addr} ({len(clients)} clients)")

    # Announce to everyone
    broadcast(f"[Server] {username} joined the chat!\n".encode())


    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 2: Message loop
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    try:
        while True:
            data = conn.recv(1024)

            if not data:
                # Client disconnected
                break

            message = data.decode().strip()
            print(f"[{username}] {message}")

            # Broadcast to everyone else
            formatted = f"[{username}] {message}\n".encode()
            broadcast(formatted, sender_sock=conn)

    except Exception as e:
        print(f"Error with {username}: {e}")

    finally:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 3: Cleanup
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        with clients_lock:
            username = remove_client(conn)

        # Notify others AFTER releasing lock (avoid deadlock)
        if username:
            broadcast(f"[Server] {username} left the chat\n".encode())

        conn.close()


def chat_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8080))
    server.listen(128)

    print("Chat server listening on port 8080")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.close()

if __name__ == "__main__":
    chat_server()
