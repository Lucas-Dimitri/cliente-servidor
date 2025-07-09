#!/bin/bash

# Test configurations
SERVERS=(2 4 6 8 10)
CLIENTS=(10 20 30 40 50 60 70 80 90 100)
MESSAGES=(1 10 100)

for servers in "${SERVERS[@]}"; do
  kubectl scale deployment server-deployment --replicas=$servers

  # Aguarda todos os pods do servidor ficarem prontos
  kubectl wait --for=condition=available --timeout=180s deployment/server-deployment

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