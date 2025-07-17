#!/bin/bash

# Quick test script - reduced scenarios for development and debugging
# Usage: ./deploy-quick.sh [python|go]

# 🚀 OTIMIZAÇÕES DE PERFORMANCE AUTOMÁTICAS
echo "🚀 Deploy Rápido Otimizado - Verificando cluster para máxima performance"

# Função para otimizar cluster se necessário
optimize_cluster() {
    echo "🔧 Verificando se cluster precisa de otimização..."
    
    # Verificar se cluster existe e tem as otimizações
    if kind get clusters | grep -q "cliente-servidor"; then
        # Verificar se tem nó worker (indicador de cluster otimizado)
        WORKER_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | grep -c worker 2>/dev/null || echo "0")
        WORKER_COUNT=$(echo "$WORKER_COUNT" | tr -d '\n')
        if [ "$WORKER_COUNT" -eq "0" ]; then
            echo "📋 Cluster existente não está otimizado. Recriando..."
            kind delete cluster --name cliente-servidor
            create_optimized_cluster
        else
            echo "✅ Cluster já otimizado com $WORKER_COUNT nó(s) worker"
        fi
    else
        echo "📋 Cluster não existe. Criando cluster otimizado..."
        create_optimized_cluster
    fi
}

# Função para criar cluster otimizado
create_optimized_cluster() {
    echo "🔧 Criando cluster Kind otimizado para máxima performance..."
    kind create cluster --config=kind-config.yaml --name cliente-servidor
    
    echo "⏳ Aguardando cluster ficar completamente pronto..."
    kubectl wait --for=condition=Ready nodes --all --timeout=60s
    
    # Mostrar recursos disponíveis
    echo "📊 Recursos disponíveis no cluster:"
    kubectl describe nodes | grep -E "(cpu|memory):" | head -4
    
    CPU_CORES=$(nproc)
    TOTAL_RAM=$(free -g | awk 'NR==2{print $2}')
    echo "💻 Sistema: $CPU_CORES threads CPU, ${TOTAL_RAM}GB RAM"
    echo "⚡ Configuração otimizada: até $((CPU_CORES * 4)) clientes simultâneos (4 por thread I/O bound)"
    
    echo "✅ Cluster otimizado criado com sucesso!"
}

# Check for server type argument
if [ -z "$1" ] || ( [ "$1" != "python" ] && [ "$1" != "go" ] ); then
  echo "Uso: $0 [python|go]"
  echo "Exemplo: $0 python"
  exit 1
fi

# Executar otimização automática
optimize_cluster

SERVER_TYPE=$1
echo "--- Executando testes RÁPIDOS para o servidor: $SERVER_TYPE ---"

# Configurations that will be exported to the main deploy script
export QUICK_TEST=true
export SERVERS_CONFIG="2"
export CLIENTS_CONFIG="10 20 30 40 50 60 70 80 90 100"
export MESSAGES_CONFIG="1 10 100 500 1000"
export ITERATIONS_CONFIG="1"

# Call the main deploy script with the same parameters
exec $(dirname "$0")/deploy.sh "$@"
