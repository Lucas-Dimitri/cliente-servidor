#!/bin/bash

# Quick test script - reduced scenarios for development and debugging
# Usage: ./deploy-quick.sh [python|go]

# Check for server type argument
if [ -z "$1" ] || ( [ "$1" != "python" ] && [ "$1" != "go" ] ); then
  echo "Uso: $0 [python|go]"
  echo "Exemplo: $0 python"
  exit 1
fi

SERVER_TYPE=$1
echo "--- Executando testes RÁPIDOS para o servidor: $SERVER_TYPE ---"

# Quick test configurations (much smaller for development)
# Now using emptyDir, so we can test multiple servers
SERVERS=(2 4)  
CLIENTS=(10 20)
MESSAGES=(1 10)
ITERATIONS=2  # Only 2 iterations for quick testing

# Calculate and display total number of executions
TOTAL_SCENARIOS=$((${#SERVERS[@]} * ${#CLIENTS[@]} * ${#MESSAGES[@]} * ITERATIONS))
echo "Total de execuções (teste rápido): $TOTAL_SCENARIOS"
echo "Configurações: ${#SERVERS[@]} servidores × ${#CLIENTS[@]} clientes × ${#MESSAGES[@]} mensagens × $ITERATIONS iterações"
echo "Tempo estimado: ~$((TOTAL_SCENARIOS / 6)) minutos"
echo ""

# Export variables for use in main script
export QUICK_TEST=true
export SERVERS_CONFIG="2 4"
export CLIENTS_CONFIG="10 20"
export MESSAGES_CONFIG="1 10"
export ITERATIONS_CONFIG="2"

# Call the main deploy script with the same parameters
exec $(dirname "$0")/deploy.sh "$@"
