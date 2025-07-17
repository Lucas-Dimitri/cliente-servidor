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

# Configurations that will be exported to the main deploy script
export QUICK_TEST=true
export SERVERS_CONFIG="2 10"
export CLIENTS_CONFIG="10 20 30 40 50 60 70 80 90 100"
export MESSAGES_CONFIG="1 10 100 500 1000"
export ITERATIONS_CONFIG="1"

# Call the main deploy script with the same parameters
exec $(dirname "$0")/deploy.sh "$@"
