import requests
import time
import sys

def make_request(client_id):
    try:
        start = time.time()
        response = requests.get('http://server-service/')
        end = time.time()
        print(f"Cliente {client_id}: {response.text.strip()} | Tempo: {(end-start):.4f}s")
    except Exception as e:
        print(f"Cliente {client_id} erro: {str(e)}")

if __name__ == '__main__':
    client_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    num_messages = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    for _ in range(num_messages): make_request(client_id)
