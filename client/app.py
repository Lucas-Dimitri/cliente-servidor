import requests
import time
import sys
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PipelinedClient:
    def __init__(self, server_service, max_workers=10):
        self.server_service = server_service
        self.session = requests.Session()

        # Configure session for better TCP pipelining and keep-alive
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.01,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=50,  # More connections for pipelining
            pool_maxsize=100,  # Larger pool for concurrent requests
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Keep-alive and pipelining headers
        self.session.headers.update(
            {"Connection": "keep-alive", "Keep-Alive": "timeout=30, max=1000"}
        )

        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def make_single_request(self, client_id, message_id):
        try:
            # Timestamp when client sends the request
            client_send_time = time.time()

            # Send request with client and message metadata
            payload = {
                "client_id": client_id,
                "message_id": message_id,
                "client_send_time": client_send_time,
            }

            response = self.session.post(
                f"http://{self.server_service}/",
                json=payload,
                timeout=5,  # Reduced timeout for pipelining
            )

            # Timestamp when client receives the response
            client_receive_time = time.time()

            # Calculate total response time
            response_time = client_receive_time - client_send_time

            print(
                f"Cliente {client_id}, Mensagem {message_id}: {response.text.strip()} | Tempo: {response_time:.4f}s"
            )

            return response_time

        except Exception as e:
            print(f"Cliente {client_id}, Mensagem {message_id} erro: {str(e)}")
            return None

    def make_pipelined_requests(self, client_id, num_messages):
        """Send multiple requests using TCP pipelining"""
        futures = []

        # Submit all requests concurrently for pipelining
        for message_id in range(1, num_messages + 1):
            future = self.executor.submit(
                self.make_single_request, client_id, message_id
            )
            futures.append(future)

        # Collect results as they complete
        response_times = []
        for future in as_completed(futures):
            response_time = future.result()
            if response_time is not None:
                response_times.append(response_time)

        return response_times

    def close(self):
        self.executor.shutdown(wait=True)
        self.session.close()


def make_request(client_id, message_id):
    """Legacy function for compatibility"""
    server_service = os.getenv("SERVER_SERVICE", "server-service")
    client = PipelinedClient(server_service, max_workers=1)
    try:
        return client.make_single_request(client_id, message_id)
    finally:
        client.close()


if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    num_messages = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    print(
        f"Cliente {client_id} iniciando com {num_messages} mensagens (TCP Pipelining)"
    )

    server_service = os.getenv("SERVER_SERVICE", "server-service")

    # Use pipelined client for better performance
    client = PipelinedClient(server_service, max_workers=min(num_messages, 20))

    try:
        if num_messages > 1:
            # Use pipelining for multiple messages
            response_times = client.make_pipelined_requests(client_id, num_messages)
            print(
                f"Cliente {client_id} concluído - {len(response_times)} requisições pipelined processadas"
            )
        else:
            # Single request
            response_time = client.make_single_request(client_id, 1)
            if response_time is None:
                time.sleep(0.001)  # Minimal delay on error
            print(f"Cliente {client_id} concluído")
    finally:
        client.close()
