import socket
import threading
import time
import os
import csv
import signal
import sys
import struct

# Protocol constants
MAGIC_NUMBER = 0x12345678
MSG_CLIENT_REQUEST = 1
MSG_SERVER_RESPONSE = 2
MSG_CLOSE_CONNECTION = 4


class ProtocolMessage:
    def __init__(self, msg_type, payload):
        self.magic = MAGIC_NUMBER
        self.msg_type = msg_type
        self.payload_length = len(payload)
        self.payload = payload


class ClientRequest:
    def __init__(self, client_id, message_id, timestamp, data=""):
        self.client_id = client_id
        self.message_id = message_id
        self.timestamp = timestamp
        self.data = data

    def serialize(self):
        data = {
            "client_id": self.client_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        import json

        return ProtocolMessage(MSG_CLIENT_REQUEST, json.dumps(data).encode("utf-8"))

    @classmethod
    def deserialize(cls, payload):
        import json

        data = json.loads(payload.decode("utf-8"))
        return cls(
            data["client_id"],
            data["message_id"],
            data["timestamp"],
            data.get("data", ""),
        )


class ServerResponse:
    def __init__(self, server_id, processing_time, data=""):
        self.server_id = server_id
        self.processing_time = processing_time
        self.data = data

    def serialize(self):
        data = {
            "server_id": self.server_id,
            "processing_time": self.processing_time,
            "data": self.data,
        }
        import json

        return ProtocolMessage(MSG_SERVER_RESPONSE, json.dumps(data).encode("utf-8"))


def send_message(sock, message):
    # Pack header: magic (4 bytes), type (4 bytes), length (4 bytes)
    header = struct.pack(
        "!III", message.magic, message.msg_type, message.payload_length
    )
    sock.sendall(header + message.payload)


def receive_message(sock):
    try:
        # Receive header (12 bytes)
        header_data = b""
        while len(header_data) < 12:
            chunk = sock.recv(12 - len(header_data))
            if not chunk:
                return None
            header_data += chunk

        magic, msg_type, payload_length = struct.unpack("!III", header_data)

        if magic != MAGIC_NUMBER:
            return None

        # Receive payload
        payload = b""
        while len(payload) < payload_length:
            chunk = sock.recv(payload_length - len(payload))
            if not chunk:
                return None
            payload += chunk

        return ProtocolMessage(msg_type, payload)
    except:
        return None


class CustomProtocolServer:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.server_id = socket.gethostname()
        self.running = False
        self.socket = None
        self.csv_file = "/data/requests.csv"
        self.csv_lock = threading.Lock()

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)

        # Initialize CSV file
        self.init_csv()

    def init_csv(self):
        """Initialize CSV file with headers"""
        with self.csv_lock:
            if not os.path.exists(self.csv_file) or os.path.getsize(self.csv_file) == 0:
                with open(self.csv_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "client_id",
                            "messages_processed",
                            "server_id",
                            "session_start_time",
                            "avg_processing_time",
                            "session_end_time",
                            "session_duration",
                            "num_servers",
                            "num_clients",
                            "num_messages",
                        ]
                    )

    def log_client_session(
        self,
        client_id,
        messages_processed,
        total_processing_time,
        first_message_time,
        last_message_time,
    ):
        """Log consolidated client session to CSV file"""
        with self.csv_lock:
            try:
                with open(self.csv_file, "a", newline="") as f:
                    writer = csv.writer(f)

                    # Calculate session response time
                    session_duration = last_message_time - first_message_time
                    avg_processing_time = (
                        total_processing_time / messages_processed
                        if messages_processed > 0
                        else 0
                    )

                    # Get environment variables for scenario parameters
                    num_servers = os.getenv("NUM_SERVERS", "unknown")
                    num_clients = os.getenv("NUM_CLIENTES", "unknown")
                    num_messages = os.getenv("NUM_MENSAGENS", "unknown")

                    # Log one row per client with consolidated data
                    writer.writerow(
                        [
                            client_id,
                            messages_processed,  # Total messages processed for this client
                            self.server_id,
                            f"{first_message_time:.6f}",
                            f"{avg_processing_time:.6f}",  # Average processing time
                            f"{last_message_time:.6f}",
                            f"{session_duration:.6f}",  # Total session duration
                            num_servers,
                            num_clients,
                            num_messages,
                        ]
                    )
            except Exception as e:
                print(f"Error logging client session: {e}")

    def handle_client(self, client_socket, client_address):
        """Handle individual client connection"""
        print(f"Cliente conectado: {client_address}")

        # Session statistics
        client_id = None
        messages_processed = 0
        total_processing_time = 0
        first_message_time = None
        last_message_time = None

        try:
            while self.running:
                # Receive message from client
                message = receive_message(client_socket)

                if message is None:
                    break

                if message.msg_type == MSG_CLIENT_REQUEST:
                    # Process client request
                    start_time = time.time()

                    client_request = ClientRequest.deserialize(message.payload)

                    # Simulate some processing work
                    time.sleep(0.001)  # 1ms processing time

                    processing_time = time.time() - start_time

                    # Update session statistics
                    if client_id is None:
                        client_id = client_request.client_id
                        first_message_time = client_request.timestamp

                    messages_processed += 1
                    total_processing_time += processing_time
                    last_message_time = time.time()

                    # Send response back to client
                    response = ServerResponse(
                        self.server_id,
                        processing_time,
                        f"Processed message {client_request.message_id} from {client_request.client_id}",
                    )

                    send_message(client_socket, response.serialize())

                    print(
                        f"Processed: Client {client_request.client_id}, Message {client_request.message_id}"
                    )

                elif message.msg_type == MSG_CLOSE_CONNECTION:
                    print(f"Cliente {client_address} solicitou fechamento da conexão")
                    break

        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Log this session directly to CSV
            if client_id is not None and messages_processed > 0:
                self.log_client_session(
                    client_id,
                    messages_processed,
                    total_processing_time,
                    first_message_time,
                    last_message_time,
                )

            client_socket.close()
            print(f"Cliente {client_address} desconectado")

    def start(self):
        """Start the server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(100)  # Allow up to 100 queued connections
            self.running = True

            print(
                f"🚀 Servidor de protocolo customizado iniciado em {self.host}:{self.port}"
            )
            print(f"📊 Logs serão salvos em: {self.csv_file}")
            print(f"🔧 Server ID: {self.server_id}")

            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()

                    # Create thread to handle client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True,
                    )
                    client_thread.start()

                except OSError:
                    if self.running:
                        print("Error accepting connections")
                    break

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the server"""
        print("🛑 Parando servidor...")

        # Write consolidated statistics before stopping
        print("📊 Escrevendo estatísticas consolidadas...")
        self.write_consolidated_stats()

        self.running = False
        if self.socket:
            self.socket.close()
        print("✅ Servidor parado")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n📡 Sinal de parada recebido")
    server.stop()
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    server = CustomProtocolServer()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
