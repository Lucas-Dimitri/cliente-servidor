#!/bin/bash

# Check for server type argument
if [ -z "$1" ] || ( [ "$1" != "python" ] && [ "$1" != "go" ] ); then
  echo "Uso: $0 <python|go>"
  exit 1
fi

SERVER_TYPE=$1
SERVER_DIR="server-$SERVER_TYPE"
RESULTS_FILE="requests_$SERVER_TYPE.csv"
DEPLOYMENT_NAME="server-deployment-$SERVER_TYPE"
SERVICE_NAME="server-service-$SERVER_TYPE"

echo "--- Executando testes para o servidor: $SERVER_TYPE ---"

# Test configurations - check if running in quick test mode
if [ "$QUICK_TEST" = "true" ]; then
  echo "--- Modo TESTE RÁPIDO ativado ---"
  SERVERS=($SERVERS_CONFIG)
  CLIENTS=($CLIENTS_CONFIG)
  MESSAGES=($MESSAGES_CONFIG)
  ITERATIONS=$ITERATIONS_CONFIG
else
  echo "--- Modo TESTE COMPLETO (conforme afazeres.txt) ---"
  # Full test configurations - conforming to requirements in afazeres.txt
  SERVERS=(2 4 6 8 10)
  CLIENTS=(10 20 30 40 50 60 70 80 90 100)
  MESSAGES=(1 10 100 500 1000 10000)
  ITERATIONS=10  # Number of repetitions per scenario for statistical analysis
fi

# Calculate and display total number of executions
TOTAL_SCENARIOS=$((${#SERVERS[@]} * ${#CLIENTS[@]} * ${#MESSAGES[@]} * ITERATIONS))
echo "Total de execuções planejadas: $TOTAL_SCENARIOS"
echo "Configurações: ${#SERVERS[@]} servidores × ${#CLIENTS[@]} clientes × ${#MESSAGES[@]} mensagens × $ITERATIONS iterações"
echo "Tempo estimado: ~$((TOTAL_SCENARIOS * 2 / 60)) minutos (assumindo 2s por execução)"
echo "ATENÇÃO: Este é um teste completo que pode levar várias horas!"
echo ""

# Record start time for execution time calculation
START_TIME=$(date +%s)

# Initialize results file with header
> "$RESULTS_FILE"
echo "client_id,message_id,server_id,client_send_time,server_processing_time,client_receive_time,response_time,num_servers,num_clients,num_messages" > "$RESULTS_FILE"

# Helper functions for optimization
function wait_for_pods_ready() {
  local deployment=$1
  local replicas=$2
  local timeout=${3:-120}
  
  echo "Aguardando $replicas pods ficarem prontos..."
  
  # Wait for deployment to be available first
  if ! kubectl wait --for=condition=available --timeout=${timeout}s deployment/"$deployment" > /dev/null 2>&1; then
    echo "Erro: Deployment não ficou disponível no tempo esperado."
    return 1
  fi
  
  # Additional check to ensure all pods are actually running
  local ready_count=0
  local attempts=0
  while [ $attempts -lt $((timeout/5)) ]; do
    ready_count=$(kubectl get pods -l app="$deployment" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    if [ $ready_count -ge $replicas ]; then
      echo "Todos os $replicas pods estão prontos (contagem atual: $ready_count)."
      return 0
    fi
    sleep 5
    ((attempts++))
  done
  
  echo "Aviso: Apenas $ready_count de $replicas pods estão prontos após ${timeout}s."
  # Return success anyway if we have some pods running
  if [ $ready_count -gt 0 ]; then
    echo "Continuando com $ready_count pods disponíveis..."
    return 0
  else
    return 1
  fi
}

function collect_data_from_pods() {
  local deployment=$1
  local timestamp=$2
  local language=$3
  local temp_file="temp_results_${timestamp}.csv"
  
  # Get all pod names
  local pod_names=($(kubectl get pods -l app="$deployment" -o jsonpath='{.items[*].metadata.name}'))
  
  # Collect data from all pods sequentially for debugging
  > "$temp_file"
  for pod in "${pod_names[@]}"; do
    # Use a pod-specific temporary file for processing
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
        kubectl exec "$pod" -- ls -la /data/ 2>/dev/null >&2 || echo "  ✗ Não conseguiu listar /data/ no pod $pod" >&2
      fi
    fi
    
    # Process only if the file exists and has content
    if [ -f "${pod_temp_file}" ] && [ -s "${pod_temp_file}" ]; then
      # Skip header, empty lines, and ensure each line has exactly 10 fields
      tail -n +2 "${pod_temp_file}" | 
      grep -v '^client_id' | 
      grep -v '^$' |
      awk -F, '{
        # Only process lines with at least the first 3 fields (client_id, message_id, server_id)
        if (NF >= 3) {
          # Print exactly 10 fields, using existing values or "unknown"
          printf "%s,%s,%s", $1, $2, $3;
          # Fields 4-10
          for (i=4; i<=10; i++) {
            if (i <= NF && length($i) > 0) {
              printf ",%s", $i;
            } else {
              printf ",unknown";
            }
          }
          printf "\n";
        }
      }' >> "$temp_file"
    fi
     # Clean up the pod temp file
    rm -f "${pod_temp_file}"
  done
  echo "$temp_file"
}

# Build Docker images (always rebuild for testing)
echo "--- Construindo imagens Docker ---"

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

# Load images into kind cluster (only if needed)
echo "Carregando imagens no cluster kind..."
kind load docker-image meu-cliente --name cliente-servidor > /dev/null 2>&1
kind load docker-image $SERVER_IMAGE_NAME --name cliente-servidor > /dev/null 2>&1

# Update deployment with correct image name
sed -i "s/\${SERVER_IMAGE_NAME}/$SERVER_IMAGE_NAME/g" "$SERVER_DIR/k8s/deployment.yaml"

# Note: Using emptyDir instead of PVC to allow multiple pods per scenario
echo "Usando armazenamento emptyDir para permitir múltiplos pods..."

# Apply Service
echo "Aplicando Service '$SERVICE_NAME'..."
kubectl apply -f "$SERVER_DIR/k8s/service.yaml" > /dev/null

# Apply Deployment
echo "Aplicando Deployment '$DEPLOYMENT_NAME'..."
kubectl apply -f "$SERVER_DIR/k8s/deployment.yaml" > /dev/null

# Add environment variables to server deployment
kubectl set env deployment/"$DEPLOYMENT_NAME" \
  NUM_SERVERS="${SERVERS[0]}" \
  NUM_CLIENTES="${CLIENTS[0]}" \
  NUM_MENSAGENS="${MESSAGES[0]}" > /dev/null

# Get the current replica count from the deployment and wait for it
current_replicas=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.spec.replicas}')
wait_for_pods_ready "$DEPLOYMENT_NAME" "$current_replicas" || {
  echo "Erro: Falha ao criar o deployment inicial do servidor."
  exit 1
}

for servers in "${SERVERS[@]}"; do
  echo "--- Cenário: $servers servidores ---"
  
  # Limpar arquivos temporários anteriores
  rm -f temp_results_*.csv
  
  kubectl scale deployment "$DEPLOYMENT_NAME" --replicas=$servers > /dev/null
  
  # Update server environment variables with current test scenario
  kubectl set env deployment/"$DEPLOYMENT_NAME" NUM_SERVERS="$servers" > /dev/null
  
  # Wait for all replicas to be ready
  wait_for_pods_ready "$DEPLOYMENT_NAME" "$servers" || {
    echo "Erro: Falha ao escalar o deployment para $servers réplicas."
    continue
  }

  for clients in "${CLIENTS[@]}"; do
    for msgs in "${MESSAGES[@]}"; do
      echo "--- Sub-cenário: $clients clientes, $msgs mensagens ---"
      
      # Loop for multiple iterations per scenario (for statistical analysis)
      for iteration in $(seq 1 $ITERATIONS); do
        echo "--- Iteração $iteration/$ITERATIONS ---"

        # Use timestamp to create unique file names (avoid cleaning CSV each time)
        TIMESTAMP=$(date +%s%N | cut -b1-13)  # timestamp in milliseconds
        
        # Update server environment variables for this scenario
        kubectl set env deployment/"$DEPLOYMENT_NAME" \
          NUM_CLIENTES="$clients" \
          NUM_MENSAGENS="$msgs" > /dev/null

        # Wait for rolling update to complete after environment change
        echo "Aguardando atualização dos pods após mudança de configuração..."
        kubectl rollout status deployment/"$DEPLOYMENT_NAME" --timeout=60s > /dev/null 2>&1 || echo "Aviso: Rollout pode não ter completado, mas continuando..."
        
        # Give pods a moment to be fully ready
        sleep 3
          
        # Limpar arquivo de requests antes do teste para evitar duplicações
        for pod in $(kubectl get pods -l app="$DEPLOYMENT_NAME" -o jsonpath='{.items[*].metadata.name}'); do
          # Go server automatically initializes CSV, so we only need to do this for Python
          if [[ "$LANGUAGE" == "python" ]]; then
            kubectl exec "$pod" -- bash -c 'echo "client_id,message_id,server_id,client_send_time,server_processing_time,client_receive_time,response_time,num_servers,num_clients,num_messages" > /data/requests.csv' 2>/dev/null || echo "Aviso: Não foi possível inicializar CSV no pod $pod"
          fi
        done
      
      # Execute client job
      export NUM_MENSAGENS=$msgs
      export NUM_CLIENTES=$clients
      export SERVER_SERVICE="${SERVICE_NAME}"
      # Vamos parar de usar TIMESTAMP_SUFFIX já que isso está causando problemas
      
      # Remove previous job if exists
      kubectl delete job client-load-test --ignore-not-found=true > /dev/null 2>&1
      
      echo "Executando job do cliente com $clients clientes e $msgs mensagens..."
      envsubst < client/k8s/job.yaml | kubectl apply -f - > /dev/null
      
      # Wait for job completion with optimized timeout
      max_wait_time=$((60 + msgs * clients / 10))  # Dynamic timeout based on workload
      if kubectl wait --for=condition=complete --timeout=${max_wait_time}s job/client-load-test > /dev/null 2>&1; then
        echo "Job do cliente concluído com sucesso."
      else
        echo "Aviso: Job do cliente falhou ou expirou para este cenário."
        kubectl delete job client-load-test --ignore-not-found=true > /dev/null 2>&1
        continue
      fi
      
      kubectl delete job client-load-test --ignore-not-found=true > /dev/null 2>&1

      # Give pods a moment to flush any pending writes before collection
      echo "Esperando para garantir que todos os dados foram persistidos..."
      sleep 5  # Increased to ensure data is flushed
      
      # Collect data from server pods
      echo "Coletando dados dos servidores..."
      
      # Check what files are available in the data directory (use any available pod)
      available_pod=$(kubectl get pods -l app="$DEPLOYMENT_NAME" --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
      if [ -n "$available_pod" ]; then
        # Use appropriate shell for each container type
        if [[ "$LANGUAGE" == "go" ]]; then
          kubectl exec "$available_pod" -- sh -c "ls -la /data/" 2>/dev/null || echo "Não foi possível listar arquivos no pod"
        else
          kubectl exec "$available_pod" -- bash -c "ls -la /data/" 2>/dev/null || echo "Não foi possível listar arquivos no pod"
        fi
      fi
      
      temp_file=$(collect_data_from_pods "$DEPLOYMENT_NAME" "$TIMESTAMP" "$LANGUAGE")
      
      # Process and append results
      if [ -s "$temp_file" ]; then
        # Create a validated version with exactly 10 columns per row
        temp_validated="${temp_file}.validated"
        # Filter empty lines and ensure proper formatting (no need to remove header since temp files don't have headers)
        grep -v "^$" "$temp_file" | \
        awk -v s="$servers" -v c="$clients" -v m="$msgs" '
        BEGIN { FS=OFS="," } 
        {
          # Skip lines with less than 3 required fields
          if (NF >= 3) {
            # Start with the first 3 required fields
            printf "%s,%s,%s", $1, $2, $3
            
            # Add remaining fields up to 10, using available data or scenario values
            for (i = 4; i <= 10; i++) {
              if (i <= NF && length($i) > 0) {
                # Use original value if available and not empty
                printf ",%s", $i
              } else if (i == 8) {
                # num_servers
                printf ",%s", s
              } else if (i == 9) {
                # num_clients
                printf ",%s", c  
              } else if (i == 10) {
                # num_messages
                printf ",%s", m
              } else {
                # Other missing fields
                printf ",unknown"
              }
            }
            printf "\n"
          }
        }' > "$temp_validated"
        
        # Verify every line has exactly 10 fields
        while IFS= read -r line; do
          field_count=$(echo "$line" | awk -F, '{print NF}')
          if [ "$field_count" -ne 10 ]; then
            echo "ERRO: Linha com número incorreto de campos ($field_count): $line"
            # Skip adding this line
          else
            echo "$line" >> "$RESULTS_FILE"
          fi
        done < "$temp_validated"
        
        LINES_ADDED=$(wc -l < "$temp_validated")
        echo "Adicionadas $LINES_ADDED linhas de dados validadas para o cenário: $servers servidores, $clients clientes, $msgs mensagens."
        
        # Clean up
        rm -f "$temp_validated"
      else
        echo "Aviso: Nenhum dado coletado para o cenário: $servers servidores, $clients clientes, $msgs mensagens."
      fi
      
      # Cleanup temp files after each iteration
      rm -f "$temp_file"

      done  # End iteration loop
    done    # End messages loop
  done      # End clients loop
done        # End servers loop

# Final cleanup
echo "--- Limpando recursos do Kubernetes ---"
kubectl delete deployment "$DEPLOYMENT_NAME" --ignore-not-found=true > /dev/null 2>&1
kubectl delete service "$SERVICE_NAME" --ignore-not-found=true > /dev/null 2>&1
# Note: No PVC cleanup needed since we're using emptyDir

echo "--- Coleta de dados para '$SERVER_TYPE' concluída. Resultados em '$RESULTS_FILE' ---"
total_lines=$(wc -l < "$RESULTS_FILE")
echo "Total de linhas coletadas: $((total_lines - 1))"

# Validação final do arquivo CSV para garantir que todas as linhas têm o formato correto
echo "Validando formato do arquivo CSV..."
CSV_TMP="${RESULTS_FILE}.tmp"

# Preservar o cabeçalho
head -n 1 "$RESULTS_FILE" > "$CSV_TMP"

# Processar todas as linhas para garantir o formato correto (10 campos)
tail -n +2 "$RESULTS_FILE" | awk -F, '
BEGIN { OFS="," }
{
  # Skip completely empty lines
  if (NF == 0 || $0 ~ /^[[:space:]]*$/) {
    next
  }
  
  # Verificar se a linha tem pelo menos 3 campos
  if (NF >= 3) {
    # Obter os primeiros 10 campos ou preencher com "unknown" se estiverem faltando
    for (i = 1; i <= 10; i++) {
      if (i <= NF && length($i) > 0) {
        printf "%s%s", $i, (i < 10 ? OFS : "")
      } else {
        printf "%s%s", "unknown", (i < 10 ? OFS : "")
      }
    }
    printf "\n"
  }
}' >> "$CSV_TMP"

# Validate the temporary CSV - check each line has exactly 10 fields
echo "Verificando número de campos em cada linha..."
INVALID_LINES=$(awk -F, '{if (NF != 10) print NR, ":", NF, "fields:", $0}' "$CSV_TMP")
if [ -n "$INVALID_LINES" ]; then
  echo "Aviso: Linhas com número incorreto de campos encontradas no arquivo CSV:"
  echo "$INVALID_LINES"
  echo "Corrigindo estas linhas..."
  
  # Create a fixed version
  CSV_FIXED="${CSV_TMP}.fixed"
  awk -F, 'BEGIN { OFS="," } 
  { 
    if (NR == 1) {
      # Always keep the header as is
      print $0
    } else if (NF == 10) {
      # Line has correct number of fields, keep it
      print $0
    } else if (NF > 10) {
      # Too many fields, trim to 10
      printf "%s", $1
      for (i=2; i<=10; i++) {
        printf ",%s", $i
      }
      printf "\n"
    } else if (NF > 3 && NF < 10) {
      # Not enough fields, pad with "unknown"
      printf "%s", $1
      for (i=2; i<=NF; i++) {
        printf ",%s", $i
      }
      for (i=NF+1; i<=10; i++) {
        printf ",unknown"
      }
      printf "\n"
    }
    # Skip lines with less than 3 fields
  }' "$CSV_TMP" > "$CSV_FIXED"
  
  # Replace with fixed version
  mv "$CSV_FIXED" "$CSV_TMP"
fi

# Substituir o arquivo original pelo arquivo validado
mv "$CSV_TMP" "$RESULTS_FILE"

# Final verification
echo "Verificação final do CSV..."
FIELD_COUNT=$(awk -F, 'NR > 1 {print NF}' "$RESULTS_FILE" | sort | uniq -c)
echo "Distribuição do número de campos por linha (deve ser tudo 10):"
echo "$FIELD_COUNT"

echo "Formato do CSV validado."
total_lines=$(wc -l < "$RESULTS_FILE")
echo "Total final de linhas: $((total_lines - 1))"

# Remove all temporary files
rm -f temp_results_*.csv*

echo "Executando análise..."
if command -v python3 > /dev/null 2>&1 && [ -f "analyze.py" ]; then
  python3 analyze.py "$SERVER_TYPE"
  echo "Para comparar os resultados, execute: python3 analyze.py compare"
else
  echo "Análise não executada (python3 ou analyze.py não encontrado)"
fi

# Calculate and display total execution time
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
echo "Tempo total de execução: $(($TOTAL_TIME / 60)) minutos e $(($TOTAL_TIME % 60)) segundos."
