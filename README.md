# Sistema Cliente-Servidor Escalável com Protocolo Customizado (Python & Go)

Este projeto implementa um sistema cliente-servidor escalável, desenvolvido para avaliação de desempenho, escalabilidade e análise de protocolos em ambiente Kubernetes. O sistema utiliza Python e Go, e foi projetado para facilitar experimentos de balanceamento de carga, testes de estresse e análise estatística de resultados.

---

## Sumário

- [Descrição](#descrição)
- [Protocolo Customizado](#protocolo-customizado)
- [Requisitos Atendidos](#requisitos-atendidos)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Resultados](#resultados)
- [Autores](#autores)

---

## Descrição

O sistema consiste em:

- **Servidor:** Implementado em Python (Flask) e Go, ambos com suporte a múltiplas threads/conexões simultâneas, registrando cada sessão de cliente em CSV.
- **Cliente:** Implementado em Python, parametrizável por variáveis de ambiente, capaz de enviar milhares de mensagens por conexão usando TCP pipelining.
- **Automação:** Scripts `deploy.sh` e `deploy-quick.sh` executam todos os cenários de teste, coletam resultados e geram gráficos e relatórios automáticos.

---

## Protocolo Customizado

O sistema utiliza um **protocolo binário customizado sobre TCP**, projetado para máxima eficiência e flexibilidade, com as seguintes características:

### Estrutura do Protocolo

```
┌─────────────────────────────────────────────────────────────┐
│                    CABEÇALHO (12 bytes)                    │
├─────────────┬─────────────┬─────────────────────────────────┤
│ Magic Number│ Message Type│     Payload Length              │
│  (4 bytes)  │  (4 bytes)  │      (4 bytes)                 │
│ 0x12345678  │    1,2,4    │   tamanho do JSON              │
├─────────────┴─────────────┴─────────────────────────────────┤
│                    PAYLOAD (JSON)                          │
│         Tamanho variável conforme especificado             │
└─────────────────────────────────────────────────────────────┘
```

**Constantes:**

- `MAGIC_NUMBER = 0x12345678` (identificador do protocolo)
- `MSG_CLIENT_REQUEST = 1` (requisição do cliente)
- `MSG_SERVER_RESPONSE = 2` (resposta do servidor)
- `MSG_CLOSE_CONNECTION = 4` (fechamento de conexão)

### Fluxo de Comunicação

1. **Cliente** abre uma conexão TCP, envia todas as mensagens (pipelining) e só depois lê as respostas.
2. **Servidor** processa cada mensagem, responde e, ao final, registra uma linha consolidada por cliente no CSV.
3. **Fechamento:** Cliente envia mensagem de fechamento (`MSG_CLOSE_CONNECTION`).

### Exemplo de Payload

**Requisição do Cliente:**

```json
{
  "client_id": "client_1_4765",
  "message_id": 1,
  "timestamp": 1752846296.406,
  "data": "Hello from client"
}
```

**Resposta do Servidor:**

```json
{
  "client_id": "client_1_4765",
  "message_id": 1,
  "timestamp": 1752846296.408,
  "data": "Response from server",
  "processing_time": 0.0021
}
```

### Inovações do Protocolo

- **TCP pipelining:** Uma única conexão por cliente, envio em lote, máxima performance.
- **Cabeçalho binário fixo:** 12 bytes, fácil parsing e validação (magic number).
- **Payload JSON:** Flexível, fácil de estender.
- **Logging consolidado:** Uma linha por cliente no CSV, não por mensagem.
- **Compatibilidade:** Implementado em Python (`client/app.py`, `server-python/app.py`) e Go (`server-go/main.go`).

---

## Requisitos Atendidos

- [x] Protocolo customizado binário sobre TCP (com magic number, tipo e tamanho)
- [x] Cliente parametrizável (número de mensagens, clientes, etc)
- [x] Suporte a múltiplas threads/conexões no servidor
- [x] Registro de dados em CSV consolidado por cliente
- [x] Geração automática de gráficos e relatórios (média, mediana, desvio padrão, z-score para outliers)
- [x] Testes automatizados via scripts e Kubernetes
- [x] Implementação em duas linguagens (Python e Go)
- [x] Scripts para setup, execução e análise de resultados

---

## Sumário

- [Descrição](#descrição)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Dependências](#dependências)
- [Ambiente de Teste](#ambiente-de-teste)
- [Como Executar](#como-executar)
- [Resultados](#resultados)
- [Autores](#autores)

---

## Descrição

O sistema consiste em:

- **Servidor:** API HTTP que registra cada requisição em um arquivo CSV persistente.
- **Cliente:** Envia múltiplas requisições concorrentes ao servidor, parametrizável por quantidade de mensagens.
- **Automação:** Script `deploy.sh` executa todos os cenários de teste, coleta resultados e gera gráficos.

---

## Estrutura do Projeto

```
cliente-servidor/
├── client/                 # Cliente TCP customizado (Python)
│   └── app.py              # Implementação do protocolo
├── server-python/          # Servidor TCP customizado (Python)
│   └── app.py              # Implementação do protocolo
├── server-go/              # Servidor TCP customizado (Go)
│   └── main.go             # Implementação do protocolo
├── analyze.py              # Script de análise e gráficos 3D
├── summary_analysis.py     # Relatório estatístico detalhado
├── deploy.sh               # Script de automação dos experimentos
├── deploy-quick.sh         # Execução rápida para desenvolvimento
├── kind-config.yaml        # Configuração do cluster Kind
├── analysis_results_interactive/ # Gráficos e relatórios gerados
├── requirements.txt        # Dependências Python para análise
├── README.md
├── afazeres.txt            # Requisitos do trabalho
```

---

---

## Dependências

- Docker
- Kind (Kubernetes in Docker)
- kubectl
- Python 3.8+ (para análise local dos resultados)
- Bibliotecas Python: Flask, pandas, matplotlib, plotly, gunicorn

Instale as dependências Python para análise:

```sh
pip install -r requirements.txt
```

---

---

## Ambiente de Teste e Cenários

- **Cluster:** Kubernetes local via Kind
- **Servidor:** Python (Flask) e Go, múltiplas réplicas
- **Cliente:** Python, parametrizável por variáveis de ambiente
- **Cenários de Teste:**
  - Servidores: 2, 4, 6, 8, 10 réplicas
  - Clientes: 10 a 100 (incremento de 10)
  - Mensagens por cliente: 1, 10, 100, 500, 1000, 10000
  - Execuções por cenário: 10 (para estatísticas robustas)
  - Total mínimo: 5 (servidores) × 10 (clientes) × 6 (mensagens) × 10 (execuções) = 3000 execuções por linguagem

---

---

## Como Executar

1. (Opcional) Remova cluster antigo:
   ```sh
   kind delete cluster --name cliente-servidor
   ```
2. Crie o cluster Kind:
   ```sh
   kind create cluster --config kind-config.yaml --name cliente-servidor
   ```
3. Construa as imagens Docker:
   ```sh
   docker build -t meu-servidor-python -f server-python/Dockerfile ./server-python
   docker build -t meu-servidor-go -f server-go/Dockerfile ./server-go
   docker build -t meu-cliente -f client/Dockerfile ./client
   ```
4. Carregue as imagens no Kind:
   ```sh
   kind load docker-image meu-servidor-python --name cliente-servidor
   kind load docker-image meu-servidor-go --name cliente-servidor
   kind load docker-image meu-cliente --name cliente-servidor
   ```
5. Aplique os manifests Kubernetes:
   ```sh
   kubectl apply -f server-python/k8s/
   kubectl apply -f server-go/k8s/
   kubectl apply -f client/k8s/
   ```
6. Execute os testes automatizados:
   ```sh
   bash deploy.sh go    # Para servidor Go
   bash deploy.sh python # Para servidor Python
   # Ou use ./deploy-quick.sh para rodar cenários reduzidos
   ```
7. Resultados:
   - Os arquivos `requests_python.csv` e `requests_go.csv` serão gerados.
   - Gráficos e relatórios em `analysis_results_interactive/`.

---

---

## Resultados e Análise

Após a execução dos testes, os resultados são automaticamente processados:

- **CSV:** Resultados brutos por cliente/sessão (`requests_python.csv`, `requests_go.csv`)
- **Gráficos 3D:** Tempo total por cenário, diferença entre linguagens, escalabilidade
- **Relatório Markdown:** Estatísticas detalhadas (média, mediana, desvio padrão, outliers removidos via z-score)

Exemplo de análise gerada:

![Exemplo de gráfico 3D](analysis_results_interactive/clientes_vs_servidores_100msgs.html)

Abra qualquer arquivo `.html` da pasta `analysis_results_interactive/` para visualização interativa.

---

---

## Autores

- Lucas Ferreira Soares
- Lucas-Dimitri | lucas.ferreirasoares@hotmail.com
