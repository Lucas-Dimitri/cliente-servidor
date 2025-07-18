import socket
import time
import os
import random
import struct
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        return ProtocolMessage(MSG_CLIENT_REQUEST, json.dumps(data).encode("utf-8"))


class ServerResponse:
    def __init__(self, server_id, processing_time, data=""):
        self.server_id = server_id
        self.processing_time = processing_time
        self.data = data

    @classmethod
    def deserialize(cls, payload):
        data = json.loads(payload.decode("utf-8"))
        return cls(data["server_id"], data["processing_time"], data.get("data", ""))


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


class CustomProtocolClient:
    def __init__(self, server_host, server_port=5000):
        self.server_host = server_host
        self.server_port = server_port
        self.client_id = self.generate_client_id()

    def generate_client_id(self, suffix=""):
        """Generate unique client ID"""
        base_id = f"client_{os.getpid()}_{random.randint(1000, 9999)}"
        return f"{base_id}_{suffix}" if suffix else base_id

    def send_messages_with_pipelining(
        self, message_ids, message_contents, custom_client_id=None
    ):
        """Send multiple messages using TCP pipelining"""
        try:
            # Use custom client_id if provided, otherwise use default
            client_id = custom_client_id if custom_client_id else self.client_id
            # Create single TCP connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(60)  # Longer timeout for pipelining

            # Enable TCP_NODELAY to reduce latency in pipelining
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            start_time = time.time()

            # Connect to server
            client_socket.connect((self.server_host, self.server_port))

            # Phase 1: Send all requests without waiting for responses (PIPELINING)
            print(f"📤 Enviando {len(message_ids)} mensagens via TCP pipelining...")

            for i, message_id in enumerate(message_ids):
                request = ClientRequest(
                    client_id,
                    message_id,
                    time.time(),
                    (
                        message_contents[i]
                        if i < len(message_contents)
                        else f"Message {message_id}"
                    ),
                )
                send_message(client_socket, request.serialize())

            pipeline_send_time = time.time()
            print(
                f"⚡ Todas as mensagens enviadas em {pipeline_send_time - start_time:.3f}s"
            )

            # Phase 2: Receive all responses
            print(f"📥 Recebendo respostas...")
            results = []

            for message_id in message_ids:
                response_msg = receive_message(client_socket)

                if response_msg and response_msg.msg_type == MSG_SERVER_RESPONSE:
                    response = ServerResponse.deserialize(response_msg.payload)

                    results.append(
                        {
                            "message_id": message_id,
                            "server_id": response.server_id,
                            "server_processing_time": response.processing_time,
                            "response_data": response.data,
                        }
                    )
                else:
                    results.append(
                        {
                            "message_id": message_id,
                            "error": "Failed to receive response",
                        }
                    )

            end_time = time.time()

            # Send close connection message
            close_msg = ProtocolMessage(MSG_CLOSE_CONNECTION, b"")
            send_message(client_socket, close_msg)

            total_time = end_time - start_time
            pipeline_advantage = pipeline_send_time - start_time

            print(f"🏁 Pipelining concluído em {total_time:.3f}s")
            print(
                f"⚡ Vantagem do pipelining: enviou todas em {pipeline_advantage:.3f}s"
            )

            return {
                "results": results,
                "total_time": total_time,
                "pipeline_send_time": pipeline_advantage,
                "successful_count": len([r for r in results if "error" not in r]),
            }

        except Exception as e:
            print(f"❌ Erro no TCP pipelining: {e}")
            return None
        finally:
            try:
                client_socket.close()
            except:
                pass

    def send_message_to_server(
        self, message_id, message_content="Hello from custom protocol"
    ):
        """Send a single message to server using custom protocol (fallback method)"""
        try:
            # Create TCP connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30)  # 30 second timeout

            start_time = time.time()

            # Connect to server
            client_socket.connect((self.server_host, self.server_port))

            # Create client request
            request = ClientRequest(
                self.client_id, message_id, time.time(), message_content
            )

            # Send request
            send_message(client_socket, request.serialize())

            # Receive response
            response_msg = receive_message(client_socket)

            end_time = time.time()

            if response_msg:
                response = ServerResponse.deserialize(response_msg.payload)

                # Send close connection message
                close_msg = ProtocolMessage(MSG_CLOSE_CONNECTION, b"")
                send_message(client_socket, close_msg)

                return {
                    "message_id": message_id,
                    "response_time": end_time - start_time,
                    "server_id": response.server_id,
                    "server_processing_time": response.processing_time,
                    "response_data": response.data,
                }
            else:
                return None

        except Exception as e:
            print(f"❌ Erro enviando mensagem {message_id}: {e}")
            return None
        finally:
            try:
                client_socket.close()
            except:
                pass


def run_client():
    # Get environment variables
    server_host = os.getenv("SERVER_HOST", "server-python-service")
    num_messages = int(os.getenv("NUM_MENSAGENS", "5"))
    use_pipelining = os.getenv("USE_PIPELINING", "true").lower() == "true"
    max_workers = int(os.getenv("MAX_WORKERS", "10"))
    pipeline_batch_size = int(
        os.getenv("PIPELINE_BATCH_SIZE", "10")
    )  # Mensagens por thread

    print(f"🚀 Iniciando cliente de protocolo customizado")
    print(f"📡 Servidor: {server_host}:5000")
    print(f"📊 Número de mensagens: {num_messages}")
    print(f"⚡ TCP Pipelining: {'ATIVADO' if use_pipelining else 'DESATIVADO'}")
    print(f"🧵 Workers: {max_workers}")
    if use_pipelining:
        print(f"📦 Batch size por thread: {pipeline_batch_size}")
    print("-" * 60)

    client = CustomProtocolClient(server_host)

    # Track timing
    overall_start = time.time()

    if use_pipelining and num_messages > 1:
        # Always use simple TCP Pipelining for all messages in a single connection
        print(f"🔄 Usando TCP Pipelining simples para {num_messages} mensagens")

        message_ids = list(range(1, num_messages + 1))
        message_contents = [f"Message {i}" for i in message_ids]

        result = client.send_messages_with_pipelining(message_ids, message_contents)

        overall_end = time.time()
        total_time = overall_end - overall_start

        if result:
            successful_requests = result["successful_count"]
            failed_requests = num_messages - successful_requests

            print("\n" + "=" * 60)
            print("📊 RELATÓRIO FINAL - TCP PIPELINING SIMPLES")
            print("=" * 60)
            print(f"⏱️  Tempo total de execução: {total_time:.3f} segundos")
            print(
                f"📤 Tempo para enviar todas as mensagens: {result['pipeline_send_time']:.3f}s"
            )
            print(f"✅ Requisições bem-sucedidas: {successful_requests}")
            print(f"❌ Requisições falharam: {failed_requests}")
            print(f"📈 Taxa de sucesso: {successful_requests/num_messages*100:.1f}%")
            print(
                f"📊 Throughput: {successful_requests/total_time:.2f} mensagens/segundo"
            )
            print(
                f"⚡ Taxa de envio: {successful_requests/result['pipeline_send_time']:.2f} msg/s"
            )
        else:
            print("❌ Falha no TCP Pipelining")

    else:
        # Use traditional approach or single message
        print(f"🔄 Usando abordagem tradicional (uma conexão por mensagem)")

        successful_requests = 0
        failed_requests = 0
        response_times = []

        # Send messages using thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_message = {
                executor.submit(client.send_message_to_server, i, f"Message {i}"): i
                for i in range(1, num_messages + 1)
            }

            # Process completed tasks
            for future in as_completed(future_to_message):
                message_id = future_to_message[future]

                try:
                    result = future.result()
                    if result:
                        successful_requests += 1
                        response_time = result["response_time"]
                        response_times.append(response_time)

                        print(
                            f"✅ Mensagem {message_id}: {response_time:.3f}s "
                            f"(Server: {result['server_id']}, "
                            f"Processing: {result['server_processing_time']:.3f}s)"
                        )
                    else:
                        failed_requests += 1
                        print(f"❌ Mensagem {message_id}: Falhou")

                except Exception as e:
                    failed_requests += 1
                    print(f"❌ Mensagem {message_id}: Exceção - {e}")

        overall_end = time.time()
        total_time = overall_end - overall_start

        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - ABORDAGEM TRADICIONAL")
        print("=" * 60)
        print(f"⏱️  Tempo total de execução: {total_time:.3f} segundos")
        print(f"🧵 Threads utilizadas: {max_workers}")
        print(f"✅ Requisições bem-sucedidas: {successful_requests}")
        print(f"❌ Requisições falharam: {failed_requests}")
        print(
            f"📈 Taxa de sucesso: {successful_requests/(successful_requests+failed_requests)*100:.1f}%"
        )

        if response_times:
            print(
                f"⚡ Tempo médio de resposta: {sum(response_times)/len(response_times):.3f}s"
            )
            print(f"🚀 Menor tempo de resposta: {min(response_times):.3f}s")
            print(f"🐌 Maior tempo de resposta: {max(response_times):.3f}s")
            print(
                f"📊 Throughput: {successful_requests/total_time:.2f} mensagens/segundo"
            )

    print(f"🏁 Cliente finalizado com sucesso!")


if __name__ == "__main__":
    run_client()
