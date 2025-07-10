# Cliente-Servidor Escalável com Kubernetes

Este projeto implementa um sistema cliente-servidor escalável, desenvolvido para avaliação de desempenho e escalabilidade em ambiente Kubernetes, utilizando Python (servidor) e Python (cliente). O objetivo é analisar o comportamento do sistema sob diferentes cargas e configurações, registrando métricas para posterior análise e visualização.

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
├── client/                 # Código-fonte do cliente e Dockerfile
├── server/                 # Código-fonte do servidor e Dockerfile
├── analyze.py              # Script para análise e geração de gráficos
├── deploy.sh               # Script de automação dos experimentos
├── server/k8s/             # Manifests Kubernetes do servidor (deployment, service, pvc)
├── client/k8s/             # Manifests Kubernetes do cliente (job)
├── requirements.txt        # Dependências Python do servidor
├── README.md
```

---

## Dependências

- [Docker](https://www.docker.com/)
- [Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- Python 3.8+ (para análise local dos resultados)
- Bibliotecas Python: Flask, Gunicorn, pandas, matplotlib

Instale as dependências Python para análise:

```sh
pip install -r server/requirements.txt
```

---

## Ambiente de Teste

- **Cluster:** Kubernetes local via Kind
- **Servidor:** Python Flask + Gunicorn, persistência via PVC
- **Cliente:** Python, parametrizável por variáveis de ambiente
- **Cenários:**
  - Servidores: 2, 4, 6, 8, 10 réplicas
  - Clientes: 10 a 100 (incremento de 10)
  - Mensagens por cliente: 1, 10, 100

---

## Como Executar

1. **(Opcional) Remova cluster antigo:**

   ```sh
   kind delete cluster --name cliente-servidor
   ```

2. **Crie o cluster Kind:**

   ```sh
   kind create cluster --config kind-config.yaml --name cliente-servidor
   ```

3. **Construa as imagens Docker:**

   ```sh
   docker build -t meu-servidor-python -f server-python/Dockerfile ./server-python
   docker build -t meu-servidor-go -f server-go/Dockerfile ./server-go
   docker build -t meu-cliente -f client/Dockerfile ./client
   ```

4. **Carregue as imagens no Kind:**

   ```sh
   kind load docker-image meu-servidor-python --name cliente-servidor
   kind load docker-image meu-cliente --name cliente-servidor
   ```

5. **Aplique os manifests Kubernetes:**

   ```sh
   kubectl apply -f server/k8s/
   kubectl apply -f client/k8s/
   ```

6. **Execute os testes automatizados:**

   ```sh
   bash deploy.sh
   ```

7. **Resultados:**
   - O arquivo `requests.csv` será gerado na raiz do projeto.
   - Gráficos de análise serão salvos após a execução do `analyze.py`.

---

## Resultados

Os resultados dos experimentos (CSV e gráficos) podem ser encontrados na raiz do projeto após a execução do script. Os gráficos mostram o desempenho do servidor sob diferentes cargas e configurações.

---

## Autores

- Lucas Ferreira Soares
- Lucas-Dimitri | lucas.ferreirasoares@hotmail.com
