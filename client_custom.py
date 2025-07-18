import socket
import time
import os
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from protocol import (
    ProtocolMessage,
    ClientRequest,
    ServerResponse,
    send_message,
    receive_message,
    MSG_CLOSE_CONNECTION,
)


class CustomProtocolClient:
    def __init__(self, server_host, server_port=5000):
        self.server_host = server_host
        self.server_port = server_port
        self.client_id = self.generate_client_id()

    def generate_client_id(self):
        """Generate unique client ID"""
        return f"client_{os.getpid()}_{random.randint(1000, 9999)}"

    def send_message_to_server(
        self, message_id, message_content="Hello from custom protocol"
    ):
        """Send a single message to server using custom protocol"""
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
    max_workers = int(os.getenv("MAX_WORKERS", "10"))

    print(f"🚀 Iniciando cliente de protocolo customizado")
    print(f"📡 Servidor: {server_host}:5000")
    print(f"📊 Número de mensagens: {num_messages}")
    print(f"🧵 Workers: {max_workers}")
    print("-" * 60)

    client = CustomProtocolClient(server_host)

    # Track timing
    overall_start = time.time()
    successful_requests = 0
    failed_requests = 0
    total_response_time = 0
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
                    total_response_time += response_time
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
    print("📊 RELATÓRIO FINAL - PROTOCOLO CUSTOMIZADO")
    print("=" * 60)
    print(f"⏱️  Tempo total de execução: {total_time:.3f} segundos")
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
        print(f"📊 Throughput: {successful_requests/total_time:.2f} mensagens/segundo")

    print(f"🏁 Cliente finalizado com sucesso!")


if __name__ == "__main__":
    run_client()
