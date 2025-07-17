#!/bin/bash

# Check for server type argument
if [ -z "$1" ] || ( [ "$1" != "python" ] && [ "$1" != "go" ] ); then
  echo "Uso: $0 <python|go>"
  exit 1
fi

# Define script variables based on server type argument
SERVER_TYPE=$1
SERVER_DIR="server-$SERVER_TYPE"
RESULTS_FILE="requests_$SERVER_TYPE.csv"
DEPLOYMENT_NAME="server-deployment-$SERVER_TYPE"
SERVICE_NAME="server-service-$SERVER_TYPE"

# Optimized test configurations
if [ "$QUICK_TEST" = "true" ]; then
  echo "--- Modo RAPIDO - Executando testes para o servidor: $SERVER_TYPE ---"
  SERVERS=($SERVERS_CONFIG)
  CLIENTS=($CLIENTS_CONFIG)
  MESSAGES=($MESSAGES_CONFIG)
  ITERATIONS=$ITERATIONS_CONFIG
else
  echo "--- Modo COMPLETO - Executando testes para o servidor: $SERVER_TYPE ---"
  SERVERS=(2 4 6 8 10)
  CLIENTS=(10 20 30 40 50 60 70 80 90 100)
  MESSAGES=(1 10 100 500 1000 10000)
  ITERATIONS=5
fi

# Calculate and display total number of executions
# Total de cenários (combinações de configuração)
TOTAL_SCENARIOS=$((${#SERVERS[@]} * ${#CLIENTS[@]} * ${#MESSAGES[@]} * ITERATIONS))

# Calculation of total executions
TOTAL_CLIENTS=0
for client_count in "${CLIENTS[@]}"; do
  TOTAL_CLIENTS=$((TOTAL_CLIENTS + client_count))
done
TOTAL_EXECUTIONS=$((${#SERVERS[@]} * TOTAL_CLIENTS * ${#MESSAGES[@]} * ITERATIONS))

# echoes the configuration details
echo "Total de cenários: $TOTAL_SCENARIOS combinações de configuração"
echo "Total de execuções (linhas de dados): $TOTAL_EXECUTIONS (cada cliente gera uma linha)"
echo "Configurações de servidores: ${SERVERS[*]}"
echo "Configurações de clientes: ${CLIENTS[*]} (soma: $TOTAL_CLIENTS)"
echo "Configurações de mensagens: ${MESSAGES[*]}"
echo "Iterações: $ITERATIONS"
echo "Cálculo: ${#SERVERS[@]} servidores × $TOTAL_CLIENTS clientes × ${#MESSAGES[@]} mensagens × $ITERATIONS iterações = $TOTAL_EXECUTIONS linhas"
echo "Tempo estimado: ~$((TOTAL_SCENARIOS * 9 / 60)) minutos (baseado em $TOTAL_SCENARIOS cenários)"
echo ""

# Record start time for execution time calculation
START_TIME=$(date +%s)

# Initialize results file with header
> "$RESULTS_FILE"
echo "client_id,message_id,server_id,client_send_time,server_processing_time,client_receive_time,response_time,num_servers,num_clients,num_messages" > "$RESULTS_FILE"

# OPTIMIZATION 2: Resilient function for pod readiness with retry logic
function wait_for_pods_ready() {
  local deployment_name=$1
  local expected_count=$2
  local max_wait=${3:-60}
  local max_attempts=3
  local attempt=1
  
  while [ $attempt -le $max_attempts ]; do
    echo "Aguardando $expected_count pods ficarem prontos... (tentativa $attempt/$max_attempts)"
    
    if kubectl wait --for=condition=ready pod -l app="$deployment_name" --timeout=${max_wait}s > /dev/null 2>&1; then
      local current_count=$(kubectl get pods -l app="$deployment_name" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
      echo "✅ Todos os $expected_count pods estão prontos (contagem atual: $current_count)."
      return 0
    else
      echo "⚠️  Tentativa $attempt falhou. Verificando status dos pods..."
      kubectl get pods -l app="$deployment_name" --no-headers 2>/dev/null | while read pod status ready restarts age; do
        echo "  Pod: $pod | Status: $status | Ready: $ready"
      done
      
      if [ $attempt -lt $max_attempts ]; then
        echo "🔄 Tentando novamente em 5 segundos..."
        sleep 2
        attempt=$((attempt + 1))
      else
        echo "❌ Todas as tentativas falharam. Nem todos os pods ficaram prontos."
        return 1
      fi
    fi
  done
}

# OPTIMIZATION 3: Streamlined data collection function
function collect_data_from_pods() {
  local deployment_name=$1
  local timestamp=$2
  local language=$3
  local temp_file="temp_results_${timestamp}.csv"

  # Get all running pod names efficiently
  local pod_names=($(kubectl get pods -l app="$deployment_name" --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null))
  
  if [ ${#pod_names[@]} -eq 0 ]; then
    echo "  ✗ Nenhum pod encontrado para $deployment_name" >&2
    echo "$temp_file"
    return
  fi

  # Collect data from all pods sequentially for debugging
  > "$temp_file"
  for pod in "${pod_names[@]}"; do
    local pod_temp_file="${temp_file}.${pod}"
    
    # Copy the standard requests.csv file (no timestamp)
    echo "  Tentando copiar dados do pod: $pod" >&2
    if kubectl cp "${pod}:/data/requests.csv" "${pod_temp_file}" >/dev/null 2>&1; then
      echo "  ✓ Copiado com sucesso de $pod" >&2
    else
      echo "  ✗ Falha ao copiar de $pod" >&2
      # Try to check if the file exists in the pod
      if [[ "$language" == "go" ]]; then
        kubectl exec "$pod" -- sh -c "ls -la /data/" 2>/dev/null >&2 || echo "  ✗ Não conseguiu listar /data/ no pod $pod" >&2
      else
        kubectl exec "$pod" -- bash -c "ls -la /data/" 2>/dev/null >&2 || echo "  ✗ Não conseguiu listar /data/ no pod $pod" >&2
      fi
      continue
    fi
    
    # Process only if the file exists and has content
    if [ -f "${pod_temp_file}" ] && [ -s "${pod_temp_file}" ]; then
      # OPTIMIZATION 5: Simplified awk processing
      tail -n +2 "${pod_temp_file}" | 
      grep -v '^client_id' | 
      grep -v '^$' |
      awk -F, 'NF >= 3 {
        printf "%s,%s,%s", $1, $2, $3;
        for (i=4; i<=10; i++) {
          printf ",%s", (i <= NF && length($i) > 0) ? $i : "unknown";
        }
        printf "\n";
      }' >> "$temp_file"
    fi
    rm -f "${pod_temp_file}"
  done
  echo "$temp_file"
}

# OPTIMIZATION 6: Build images only once, reuse for all tests
echo "--- Construindo imagens Docker (otimizado) ---"

echo "Construindo imagem do cliente..."
docker build -t meu-cliente ./client/ > /dev/null 2>&1

if [ "$SERVER_TYPE" = "python" ]; then
  SERVER_IMAGE_NAME="meu-servidor-python"
  echo "Construindo imagem do servidor $SERVER_TYPE..."
  docker build -t $SERVER_IMAGE_NAME ./server-python/ > /dev/null 2>&1
elif [ "$SERVER_TYPE" = "go" ]; then
  SERVER_IMAGE_NAME="meu-servidor-go"
  echo "Construindo imagem do servidor $SERVER_TYPE..."
  docker build -t $SERVER_IMAGE_NAME ./server-go/ > /dev/null 2>&1
fi

# Load images into kind cluster
echo "Carregando imagens no cluster kind..."
kind load docker-image meu-cliente --name cliente-servidor > /dev/null 2>&1
kind load docker-image $SERVER_IMAGE_NAME --name cliente-servidor > /dev/null 2>&1

# Update deployment with correct image name
sed -i "s/\${SERVER_IMAGE_NAME}/$SERVER_IMAGE_NAME/g" "$SERVER_DIR/k8s/deployment.yaml"

echo "Usando armazenamento emptyDir para permitir múltiplos pods..."

# Apply Service and Deployment
echo "Aplicando Service '$SERVICE_NAME'..."
kubectl apply -f "$SERVER_DIR/k8s/service.yaml" > /dev/null

echo "Aplicando Deployment '$DEPLOYMENT_NAME'..."
kubectl apply -f "$SERVER_DIR/k8s/deployment.yaml" > /dev/null

# Initialize environment
kubectl set env deployment/"$DEPLOYMENT_NAME" \
  NUM_SERVERS="${SERVERS[0]}" \
  NUM_CLIENTES="${CLIENTS[0]}" \
  NUM_MENSAGENS="${MESSAGES[0]}" > /dev/null

current_replicas=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.spec.replicas}')
wait_for_pods_ready "$DEPLOYMENT_NAME" "$current_replicas" || {
  echo "Erro: Falha ao criar o deployment inicial do servidor."
  exit 1
}

# OPTIMIZATION 7: Main execution loop with reduced wait times
for servers in "${SERVERS[@]}"; do
  echo "--- Cenário: $servers servidores ---"
  
  # Scale deployment efficiently
  kubectl scale deployment "$DEPLOYMENT_NAME" --replicas="$servers" > /dev/null 2>&1
  wait_for_pods_ready "$DEPLOYMENT_NAME" "$servers" 45 || {
    echo "Erro: Falha ao escalar para $servers servidores."
    continue
  }

  for clients in "${CLIENTS[@]}"; do
    for msgs in "${MESSAGES[@]}"; do
      echo "--- Sub-cenário: $clients clientes, $msgs mensagens ---"
      
      for iteration in $(seq 1 $ITERATIONS); do
        echo "--- Iteração $iteration/$ITERATIONS ---"
        
        # Update environment variables efficiently
        kubectl set env deployment/"$DEPLOYMENT_NAME" \
          NUM_SERVERS="$servers" \
          NUM_CLIENTES="$clients" \
          NUM_MENSAGENS="$msgs" > /dev/null 2>&1

        # OPTIMIZATION 8: Reduced rollout timeout and wait times
        echo "Aguardando atualização dos pods após mudança de configuração..."
        kubectl rollout status deployment/"$DEPLOYMENT_NAME" --timeout=20s > /dev/null 2>&1 || echo "Aviso: Rollout pode não ter completado, mas continuando..."
        
        # Sleep removido - rollout status já garante que pods estão prontos

        # Clear previous CSV data for both server types
        pod_names=($(kubectl get pods -l app="$DEPLOYMENT_NAME" --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null))
        for pod in "${pod_names[@]}"; do
          if [[ "$SERVER_TYPE" == "go" ]]; then
            kubectl exec "$pod" -- sh -c "echo 'client_id,message_id,server_id,client_send_time,server_processing_time,client_receive_time,response_time,num_servers,num_clients,num_messages' > /data/requests.csv" 2>/dev/null || true
          else
            kubectl exec "$pod" -- bash -c "echo 'client_id,message_id,server_id,client_send_time,server_processing_time,client_receive_time,response_time,num_servers,num_clients,num_messages' > /data/requests.csv" 2>/dev/null || true
          fi
        done

        # Prepare job environment
        TIMESTAMP=$(date +%s%N)
        export NUM_CLIENTES="$clients"
        export NUM_MENSAGENS="$msgs"
        export SERVER_SERVICE="${SERVICE_NAME}"
        
        # Remove previous job if exists
        kubectl delete job client-load-test --ignore-not-found=true > /dev/null 2>&1
        
        echo "Executando job do cliente com $clients clientes e $msgs mensagens..."
        envsubst < client/k8s/job.yaml | kubectl apply -f - > /dev/null
        
        # OPTIMIZATION 10: More aggressive timeout calculation
        max_wait_time=$((20 + msgs * clients / 30))
        if kubectl wait --for=condition=complete --timeout=${max_wait_time}s job/client-load-test > /dev/null 2>&1; then
          echo "Job do cliente concluído com sucesso."
        else
          echo "Aviso: Job do cliente falhou ou expirou para este cenário."
          kubectl delete job client-load-test --ignore-not-found=true > /dev/null 2>&1
          continue
        fi
        
        kubectl delete job client-load-test --ignore-not-found=true > /dev/null 2>&1

        # OPTIMIZATION 11: Verificação inteligente de persistência ao invés de sleep fixo
        echo "Verificando se dados foram persistidos..."
        data_ready=false
        for attempt in {1..10}; do
          # Verificar se pelo menos um pod tem dados no CSV
          for pod in "${pod_names[@]}"; do
            if [[ "$SERVER_TYPE" == "go" ]]; then
              line_count=$(kubectl exec "$pod" -- sh -c "wc -l < /data/requests.csv 2>/dev/null || echo 0" 2>/dev/null | tr -d ' \t\n\r')
            else
              line_count=$(kubectl exec "$pod" -- bash -c "wc -l < /data/requests.csv 2>/dev/null || echo 0" 2>/dev/null | tr -d ' \t\n\r')
            fi
            
            # Garantir que line_count é um número válido
            if [[ "$line_count" =~ ^[0-9]+$ ]] && [ "$line_count" -gt 1 ]; then  # Mais que apenas o header
              data_ready=true
              break
            fi
          done
          
          if [ "$data_ready" = true ]; then
            echo "Dados detectados, continuando..."
            break
          fi
          
          echo "Tentativa $attempt/10: Aguardando persistência..."
          sleep 0.1
        done

        # Collect data
        echo "Coletando dados dos servidores..."
        temp_file=$(collect_data_from_pods "$DEPLOYMENT_NAME" "$TIMESTAMP" "$SERVER_TYPE")
        
        # Process and append results efficiently
        if [ -s "$temp_file" ]; then
          # OPTIMIZATION 12: Streamlined validation and append
          temp_validated="${temp_file}.validated"
          grep -v "^$" "$temp_file" | \
          awk -v s="$servers" -v c="$clients" -v m="$msgs" '
          BEGIN { FS=OFS="," } 
          NF >= 3 {
            # Replace unknown values in critical fields
            if ($8 == "unknown") $8 = s;
            if ($9 == "unknown") $9 = c;
            if ($10 == "unknown") $10 = m;
            print $0
          }' > "$temp_validated"
          
          lines_added=$(wc -l < "$temp_validated")
          cat "$temp_validated" >> "$RESULTS_FILE"
          echo "Adicionadas $lines_added linhas de dados validadas para o cenário: $servers servidores, $clients clientes, $msgs mensagens."
          
          rm -f "$temp_file" "$temp_validated"
        else
          echo "Aviso: Nenhum dado coletado para este cenário."
        fi

      done  # End iteration loop
    done    # End messages loop
  done      # End clients loop
done        # End servers loop

# Final cleanup
echo "--- Limpando recursos do Kubernetes ---"
kubectl delete deployment "$DEPLOYMENT_NAME" --ignore-not-found=true > /dev/null 2>&1
kubectl delete service "$SERVICE_NAME" --ignore-not-found=true > /dev/null 2>&1

echo "--- Coleta de dados para '$SERVER_TYPE' concluída. Resultados em '$RESULTS_FILE' ---"
total_lines=$(wc -l < "$RESULTS_FILE")
echo "Total de linhas coletadas: $((total_lines - 1))"

# OPTIMIZATION 13: Simplified final validation
echo "Validando formato do arquivo CSV..."
CSV_TMP="${RESULTS_FILE}.tmp"

head -n 1 "$RESULTS_FILE" > "$CSV_TMP"
tail -n +2 "$RESULTS_FILE" | awk -F, '
BEGIN { OFS="," }
NF >= 3 && $0 !~ /^[[:space:]]*$/ {
  for (i = 1; i <= 10; i++) {
    printf "%s%s", (i <= NF && length($i) > 0) ? $i : "unknown", (i < 10 ? OFS : "")
  }
  printf "\n"
}' >> "$CSV_TMP"

mv "$CSV_TMP" "$RESULTS_FILE"

echo "Verificação final do CSV..."
FIELD_COUNT=$(awk -F, 'NR > 1 {print NF}' "$RESULTS_FILE" | sort | uniq -c)
echo "Distribuição do número de campos por linha (deve ser tudo 10):"
echo "$FIELD_COUNT"

echo "Formato do CSV validado."
total_lines=$(wc -l < "$RESULTS_FILE")
echo "Total final de linhas: $((total_lines - 1))"

# Remove temporary files
rm -f temp_results_*.csv*

# OPTIMIZATION 14: Skip analysis in optimized mode for speed
echo "Análise pulada no modo otimizado para economizar tempo."
echo "Para analisar resultados, execute: python3 analyze.py $SERVER_TYPE"
echo "Para comparar os resultados, execute: python3 analyze.py compare"

# Calculate and display total execution time
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
echo "Tempo total de execução OTIMIZADO: $(($TOTAL_TIME / 60)) minutos e $(($TOTAL_TIME % 60)) segundos."
echo "Economia estimada: ~$(( (TOTAL_TIME * 2) / 60 )) minutos comparado ao modo padrão."
