import requests
import time
import sys
import os
import json


def make_request(client_id, message_id, server_service):
    """Faz uma única requisição e retorna o tempo de resposta"""
    try:
        # Timestamp when client sends the request
        client_send_time = time.time()

        # Send request with client and message metadata
        payload = {
            "client_id": client_id,
            "message_id": message_id,
            "client_send_time": client_send_time,
        }

        response = requests.post(f"http://{server_service}/", json=payload, timeout=10)

        # Timestamp when client receives the response
        client_receive_time = time.time()

        # Calculate total response time
        response_time = client_receive_time - client_send_time

        print(f"Cliente {client_id}, Mensagem {message_id}: {response.text.strip()} | Tempo: {response_time:.4f}s")

        return response_time

    except Exception as e:
        print(f"Cliente {client_id}, Mensagem {message_id} erro: {str(e)}")
        return None


if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    num_messages = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    server_service = os.getenv("SERVER_SERVICE", "server-service")
    
    # 🎯 MEDIÇÃO REAL DE TEMPO - Início do processamento real
    app_start_time = time.time()
    print(f"⏱️  Cliente {client_id} iniciando {num_messages} mensagens às {app_start_time:.3f}")

    response_times = []
    successful_requests = 0
    failed_requests = 0

    # Processar todas as mensagens sequencialmente
    for message_id in range(1, num_messages + 1):
        response_time = make_request(client_id, message_id, server_service)
        
        if response_time is not None:
            response_times.append(response_time)
            successful_requests += 1
        else:
            failed_requests += 1
            # Small delay before retrying in case of errors
            time.sleep(0.01)

    # 🎯 MEDIÇÃO REAL DE TEMPO - Fim do processamento real  
    app_end_time = time.time()
    total_app_time = app_end_time - app_start_time
    
    # Relatório final com métricas reais
    print(f"\n📊 RELATÓRIO DO CLIENTE {client_id}:")
    print(f"⏱️  Tempo total real de processamento: {total_app_time:.4f}s")
    print(f"✅ Requisições bem-sucedidas: {successful_requests}")
    print(f"❌ Requisições falhadas: {failed_requests}")
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        print(f"📈 Tempo médio por requisição: {avg_response_time:.4f}s")
        print(f"⚡ Tempo mínimo: {min_response_time:.4f}s")
        print(f"🐌 Tempo máximo: {max_response_time:.4f}s")
        print(f"🔥 Taxa de throughput: {successful_requests/total_app_time:.2f} req/s")
    
    print(f"🎯 Cliente {client_id} concluído em {total_app_time:.4f}s")
    def __init__(self, server_service, max_workers=20):
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
            pool_maxsize=100,     # Larger pool for concurrent requests
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Keep-alive and pipelining headers
        self.session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=30, max=1000'
        })
        
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
                timeout=10  # Reasonable timeout for pipelining
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
        print(f"🚀 Enviando {num_messages} mensagens com TCP pipelining...")
        start_time = time.time()
        
        futures = []
        
        # Submit all requests concurrently for pipelining
        for message_id in range(1, num_messages + 1):
            future = self.executor.submit(self.make_single_request, client_id, message_id)
            futures.append(future)
        
        # Collect results as they complete
        response_times = []
        completed = 0
        for future in as_completed(futures):
            response_time = future.result()
            if response_time is not None:
                response_times.append(response_time)
            completed += 1
            
            # Progress feedback for large batches
            if completed % 100 == 0 or completed == num_messages:
                elapsed = time.time() - start_time
                print(f"  ✅ Completadas {completed}/{num_messages} mensagens em {elapsed:.2f}s")
        
        total_time = time.time() - start_time
        print(f"🎯 Total: {len(response_times)} mensagens processadas em {total_time:.4f}s")
        print(f"📊 Taxa: {len(response_times)/total_time:.2f} mensagens/segundo")
        
        return response_times

    def close(self):
        self.executor.shutdown(wait=True)
        self.session.close()


def make_request(client_id, message_id):
    """Legacy function for single requests"""
    server_service = os.getenv("SERVER_SERVICE", "server-service")
    client = PipelinedClient(server_service, max_workers=1)
    try:
        return client.make_single_request(client_id, message_id)
    finally:
        client.close()


if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    num_messages = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    print(f"Cliente {client_id} iniciando com {num_messages} mensagens (TCP Pipelining)")

    server_service = os.getenv("SERVER_SERVICE", "server-service")
    
    # Use pipelined client for better performance
    max_workers = min(num_messages, 50)  # Limit workers but allow more for high message counts
    client = PipelinedClient(server_service, max_workers=max_workers)
    
    try:
        if num_messages > 1:
            # Use pipelining for multiple messages - THIS IS THE KEY DIFFERENCE
            response_times = client.make_pipelined_requests(client_id, num_messages)
            avg_time = sum(response_times) / len(response_times) if response_times else 0
            print(f"Cliente {client_id} concluído - {len(response_times)} requisições pipelined")
            print(f"Tempo médio por mensagem: {avg_time:.4f}s")
        else:
            # Single request
            response_time = client.make_single_request(client_id, 1)
            if response_time is None:
                time.sleep(0.001)  # Minimal delay on error
            print(f"Cliente {client_id} concluído - 1 mensagem")
    finally:
        client.close()
