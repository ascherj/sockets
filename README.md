# TCP Socket Programming Examples

Python implementation of TCP socket-based chat servers demonstrating progression from basic echo server to multi-threaded chat application.

## Project Structure

```
sockets/
├── basic_tcp/          # Single-connection echo server
│   ├── chat_server.py  # Basic TCP server
│   ├── chat_client.py  # Basic TCP client
│   └── test_chat_server.py
├── threaded_tcp/       # Multi-client chat server
│   ├── chat_server.py  # Threaded chat server
│   └── test_chat_server.py
└── pyproject.toml
```

## Features

### Basic TCP (basic_tcp/)
- Simple echo server accepting one connection at a time
- Receives message, echoes it back, then closes connection
- Demonstrates fundamental socket operations

### Threaded TCP (threaded_tcp/)
- Multi-client chat server using threading
- Real-time message broadcasting to all connected clients
- Username registration and client management
- Commands:
  - `/list` - Show all connected clients
  - `/quit` - Disconnect from server
- Thread-safe client tracking with locks
- Join/leave notifications

## Setup

```bash
uv sync
```

## Usage

### Basic Echo Server

**Terminal 1 - Start server:**
```bash
cd basic_tcp
python chat_server.py
```

**Terminal 2 - Run client:**
```bash
cd basic_tcp
python chat_client.py
```

### Threaded Chat Server

**Terminal 1 - Start server:**
```bash
cd threaded_tcp
python chat_server.py
```

**Terminal 2+ - Connect clients using netcat:**
```bash
nc localhost 8080
```

Enter username when prompted, then send messages. Messages broadcast to all other connected clients.

## Running Tests

```bash
pytest basic_tcp/test_chat_server.py
pytest threaded_tcp/test_chat_server.py
```

### Test Coverage

**basic_tcp tests:**
- Single and multiple message echoing
- Large messages and binary data
- Unicode support
- Connection lifecycle
- Sequential connections

**threaded_tcp tests:**
- Multi-client connections
- Message broadcasting
- Client disconnection handling
- Commands (`/list`, `/quit`)
- Thread safety with concurrent connections
- Client removal and notifications

## Technical Details

- **Python Version:** 3.11+
- **Port:** 8080 (default)
- **Buffer Size:** 1024 bytes
- **Max Connections:** 128

### Threading Model
The threaded chat server uses:
- Daemon threads for each client connection
- Lock-based synchronization for shared client dictionary
- Graceful error handling for client disconnections
