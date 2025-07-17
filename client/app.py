import requests
import time
import sys
import os
import json


def make_request(client_id, message_id):
    try:
        # Timestamp when client sends the request
        client_send_time = time.time()

        server_service = os.getenv("SERVER_SERVICE", "server-service")

        # Send request with client and message metadata
        payload = {
            "client_id": client_id,
            "message_id": message_id,
            "client_send_time": client_send_time,
        }

        response = requests.post(f"http://{server_service}/", json=payload, timeout=30)

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


if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    num_messages = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    print(f"Cliente {client_id} iniciando com {num_messages} mensagens")

    for message_id in range(1, num_messages + 1):
        response_time = make_request(client_id, message_id)
        if response_time is None:
            # Small delay before retrying in case of errors
            time.sleep(0.1)

    print(f"Cliente {client_id} concluído")
