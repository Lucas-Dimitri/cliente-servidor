#!/bin/bash

# Test configurations
SERVERS=(2 4 6 8 10)
CLIENTS=(10 20 30 40 50 60 70 80 90 100)
MESSAGES=(1 5 10)

# Garante que o PVC existe antes de tudo
if ! kubectl get pvc server-pvc > /dev/null 2>&1; then
  echo "Criando PersistentVolumeClaim 'server-pvc'..."
  kubectl apply -f server/k8s/pvc.yaml
  # Aguarda o PVC ficar Bound
  kubectl wait --for=condition=Bound --timeout=60s pvc/server-pvc || {
    echo "Erro: PVC 'server-pvc' não ficou Bound."
    kubectl describe pvc server-pvc
    exit 1
  }
fi

for servers in "${SERVERS[@]}"; do
  # Garante que o deployment existe antes de escalar
  if ! kubectl get deployment server-deployment > /dev/null 2>&1; then
    echo "Aviso: Deployment 'server-deployment' não encontrado. Tentando recriar..."
    kubectl apply -f server/k8s/deployment.yaml
    # Aguarda o deployment ser criado
    kubectl wait --for=condition=available --timeout=180s deployment/server-deployment || {
      echo "Erro: Falha ao criar o deployment do servidor."
      echo "Status do deployment:"
      kubectl describe deployment server-deployment
      echo "Eventos recentes dos pods:"
      kubectl get pods -l app=server
      kubectl describe pods -l app=server
      exit 1
    }
  fi

  kubectl scale deployment server-deployment --replicas=$servers

  # Aguarda todos os pods do servidor ficarem prontos
  kubectl wait --for=condition=available --timeout=180s deployment/server-deployment || {
    echo "Erro: Falha ao escalar o deployment do servidor para $servers réplicas."
    echo "Status do deployment:"
    kubectl describe deployment server-deployment
    echo "Eventos recentes dos pods:"
    kubectl get pods -l app=server
    kubectl describe pods -l app=server
    exit 1
  }

  for clients in "${CLIENTS[@]}"; do
    for msgs in "${MESSAGES[@]}"; do
      export NUM_MENSAGENS=$msgs
      export NUM_CLIENTES=$clients
      envsubst < client/k8s/job.yaml | kubectl apply -f -
      kubectl wait --for=condition=complete --timeout=300s job/client-load-test
      kubectl delete job client-load-test
    done
  done
done

# Extract data and generate graphs
SERVER_POD=$(kubectl get pods -l app=server -o jsonpath="{.items[0].metadata.name}")
kubectl wait --for=condition=ready pod/$SERVER_POD --timeout=60s
kubectl cp $SERVER_POD:/data/requests.csv ./requests.csv
python3 analyze.py