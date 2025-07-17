#!/usr/bin/env python3
"""
Script para testar e medir tempos reais de execução
"""

import time
import subprocess
import sys
import os

def run_kubectl_job_and_measure(clients, messages):
    """Executa um job no Kubernetes e mede o tempo real de execução"""
    
    print(f"\n🧪 Testando: {clients} clientes, {messages} mensagens")
    
    # Preparar variáveis de ambiente
    env = os.environ.copy()
    env['NUM_CLIENTES'] = str(clients)
    env['NUM_MENSAGENS'] = str(messages)
    env['SERVER_SERVICE'] = 'server-service-python'
    
    # Remover job anterior se existir
    subprocess.run(['kubectl', 'delete', 'job', 'client-load-test', '--ignore-not-found=true'], 
                  capture_output=True)
    
    # Aplicar job
    start_time = time.time()
    
    result = subprocess.run(['sh', '-c', 'envsubst < client/k8s/job.yaml | kubectl apply -f -'], 
                           env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Erro ao criar job: {result.stderr}")
        return None
    
    # Aguardar conclusão com timeout realista
    timeout = max(30, messages * clients // 10)  # Timeout mais realista
    print(f"⏱️  Aguardando conclusão (timeout: {timeout}s)...")
    
    wait_result = subprocess.run(['kubectl', 'wait', '--for=condition=complete', 
                                 f'--timeout={timeout}s', 'job/client-load-test'], 
                                capture_output=True)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    if wait_result.returncode == 0:
        print(f"✅ Job concluído em {execution_time:.2f}s")
        
        # Verificar status dos pods
        pods_result = subprocess.run(['kubectl', 'get', 'pods', '-l', 'job-name=client-load-test', 
                                     '--no-headers'], capture_output=True, text=True)
        
        completed_pods = 0
        failed_pods = 0
        
        for line in pods_result.stdout.strip().split('\n'):
            if line:
                status = line.split()[2]
                if 'Completed' in status:
                    completed_pods += 1
                elif 'Error' in status or 'Failed' in status:
                    failed_pods += 1
        
        print(f"📊 Pods completados: {completed_pods}/{clients}")
        if failed_pods > 0:
            print(f"⚠️  Pods falhados: {failed_pods}")
        
        # Limpar
        subprocess.run(['kubectl', 'delete', 'job', 'client-load-test', '--ignore-not-found=true'], 
                      capture_output=True)
        
        return {
            'clients': clients,
            'messages': messages,
            'execution_time': execution_time,
            'completed_pods': completed_pods,
            'failed_pods': failed_pods,
            'expected_total_requests': clients * messages
        }
    else:
        print(f"❌ Job falhou ou expirou após {execution_time:.2f}s")
        
        # Verificar status dos pods mesmo em caso de falha
        pods_result = subprocess.run(['kubectl', 'get', 'pods', '-l', 'job-name=client-load-test', 
                                     '--no-headers'], capture_output=True, text=True)
        
        print("🔍 Status dos pods:")
        for line in pods_result.stdout.strip().split('\n'):
            if line:
                print(f"   {line}")
        
        subprocess.run(['kubectl', 'delete', 'job', 'client-load-test', '--ignore-not-found=true'], 
                      capture_output=True)
        
        return None

def main():
    """Executa testes comparativos"""
    
    print("🚀 Iniciando teste de timing para investigar performance...")
    
    # Verificar se cluster está ativo
    result = subprocess.run(['kubectl', 'get', 'nodes'], capture_output=True)
    if result.returncode != 0:
        print("❌ Cluster Kubernetes não está ativo. Execute o deploy primeiro.")
        sys.exit(1)
    
    # Verificar se servidor está rodando
    result = subprocess.run(['kubectl', 'get', 'deployment', 'server-deployment-python'], 
                           capture_output=True)
    if result.returncode != 0:
        print("❌ Servidor Python não está rodando. Execute ./deploy-quick.sh python primeiro.")
        sys.exit(1)
    
    # Testes progressivos
    test_cases = [
        (5, 1),      # 5 clientes, 1 mensagem cada
        (5, 10),     # 5 clientes, 10 mensagens cada  
        (5, 100),    # 5 clientes, 100 mensagens cada
        (5, 1000),   # 5 clientes, 1000 mensagens cada
        (10, 1),     # 10 clientes, 1 mensagem cada
        (10, 100),   # 10 clientes, 100 mensagens cada
    ]
    
    results = []
    
    for clients, messages in test_cases:
        result = run_kubectl_job_and_measure(clients, messages)
        if result:
            results.append(result)
        
        # Pequena pausa entre testes
        time.sleep(2)
    
    # Relatório final
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE TIMING")
    print("="*60)
    
    print(f"{'Clientes':<10} {'Mensagens':<10} {'Tempo (s)':<12} {'Req/Total':<12} {'Taxa (req/s)':<15}")
    print("-"*60)
    
    for result in results:
        total_requests = result['expected_total_requests']
        rate = total_requests / result['execution_time']
        
        print(f"{result['clients']:<10} {result['messages']:<10} "
              f"{result['execution_time']:<12.2f} {total_requests:<12} {rate:<15.2f}")
    
    # Análise de escalabilidade
    print("\n🔍 ANÁLISE:")
    
    if len(results) >= 2:
        # Comparar cenários similares
        single_msg_results = [r for r in results if r['messages'] == 1]
        multi_msg_results = [r for r in results if r['messages'] > 1]
        
        if single_msg_results and multi_msg_results:
            avg_single = sum(r['execution_time'] for r in single_msg_results) / len(single_msg_results)
            avg_multi = sum(r['execution_time'] for r in multi_msg_results) / len(multi_msg_results)
            
            print(f"⏱️  Tempo médio (1 mensagem): {avg_single:.2f}s")
            print(f"⏱️  Tempo médio (múltiplas): {avg_multi:.2f}s")
            print(f"📈 Diferença: {avg_multi/avg_single:.1f}x mais lento para múltiplas mensagens")
        
        # Verificar se há scaling linear
        same_client_results = {}
        for r in results:
            if r['clients'] not in same_client_results:
                same_client_results[r['clients']] = []
            same_client_results[r['clients']].append(r)
        
        for clients, client_results in same_client_results.items():
            if len(client_results) > 1:
                print(f"\n👥 {clients} clientes:")
                sorted_results = sorted(client_results, key=lambda x: x['messages'])
                for r in sorted_results:
                    rate = r['expected_total_requests'] / r['execution_time']
                    print(f"   {r['messages']} msgs: {r['execution_time']:.2f}s ({rate:.1f} req/s)")

if __name__ == "__main__":
    main()
