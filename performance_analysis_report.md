# 📊 Análise de Performance: Python vs Go

**Relatório gerado em:** 2025-07-18 11:21:44

## 🎯 Metodologia

Este relatório analisa o **tempo total para processar todos os clientes** de cada cenário,
não apenas o tempo médio individual. A fórmula utilizada é:

**Tempo Total do Cenário = Tempo Médio por Cliente × Número de Clientes**

Esta abordagem fornece uma visão mais realista do desempenho total do sistema.

---
## � Resumo dos Dados

| Métrica | Python | Go | Total |
|---------|--------|----|----|
| Requisições originais | 5,499 | 5,500 | 10,999 |
| Requisições após limpeza | 5,435 | 5,438 | 10,873 |
| Outliers removidos | - | - | 126 |

## 1️⃣ Estatísticas Gerais

### � Estatísticas Detalhadas

| Implementação | Requisições | Tempo Médio (s) | Mediana (s) | Desvio Padrão (s) | Mínimo (s) | Máximo (s) |
|---------------|-------------|-----------------|-------------|------------------|------------|------------|
| **Python** | 5,435 | 1.0483 | 0.2354 | 1.4478 | 0.0013 | 8.3546 |
| **Go** | 5,438 | 0.9340 | 0.2553 | 1.1719 | 0.0014 | 4.8179 |

### 🎯 Comparação Direta

| Métrica | Valor |
|---------|-------|
| Diferença absoluta | **0.1143s** |
| Diferença percentual | **10.91%** |
| **Resultado** | ✅ **Go é 10.91% mais rápido que Python** |

## 2️⃣ Análise por Cenários

**Total de cenários analisados:** 100

### 🏆 Vencedores por Cenário

| Implementação | Cenários Vencidos | Percentual |
|---------------|-------------------|------------|
| **Go** | 36 | **36.0%** |
| **Python** | 64 | **64.0%** |

### 🚀 Top 5 Maiores Diferenças de Tempo Total

| Ranking | Vencedor | Melhoria | Cenário | Python Total (s) | Go Total (s) |
|---------|----------|----------|---------|------------------|--------------|
| 1 | **Go** | **46.0%** | 10 serv, 10 cli, 1 msg | 0.04 | 0.02 |
| 2 | **Python** | **44.1%** | 2 serv, 20 cli, 1 msg | 0.04 | 0.07 |
| 3 | **Go** | **41.4%** | 2 serv, 100 cli, 1000 msg | 591.70 | 346.81 |
| 4 | **Go** | **40.1%** | 2 serv, 100 cli, 500 msg | 277.67 | 166.23 |
| 5 | **Python** | **35.8%** | 2 serv, 60 cli, 10 msg | 1.33 | 2.08 |

## 3️⃣ Análise por Número de Mensagens

### 📨 Performance Média por Número de Mensagens

| Mensagens | Python (s) | Go (s) | Vencedor | Melhoria |
|-----------|------------|--------|----------|----------|
| 1 | 0.0029 | 0.0032 | ✅ **Python** | 11.2% mais rápido |
| 10 | 0.0229 | 0.0275 | ✅ **Python** | 16.9% mais rápido |
| 100 | 0.2712 | 0.2768 | ✅ **Python** | 2.0% mais rápido |
| 500 | 1.6365 | 1.4566 | ✅ **Go** | 11.0% mais rápido |
| 1,000 | 3.2555 | 2.8603 | ✅ **Go** | 12.1% mais rápido |

## 4️⃣ Análise de Escalabilidade

### 👥 Escalabilidade por Número de Clientes

| Clientes | Python (s) | Go (s) | Vencedor | Melhoria (%) |
|----------|------------|--------|----------|--------------|
| 10 | 0.6462 | 0.6581 | **Python** | 1.8 |
| 20 | 0.6601 | 0.6615 | **Python** | 0.2 |
| 30 | 0.6740 | 0.6709 | **Go** | 0.5 |
| 40 | 0.7387 | 0.7246 | **Go** | 1.9 |
| 50 | 0.8038 | 0.7855 | **Go** | 2.3 |
| 60 | 0.9229 | 0.8739 | **Go** | 5.3 |
| 70 | 1.0442 | 0.9275 | **Go** | 11.2 |
| 80 | 1.1434 | 1.0439 | **Go** | 8.7 |
| 90 | 1.1937 | 1.0551 | **Go** | 11.6 |
| 100 | 1.3960 | 1.0975 | **Go** | 21.4 |

### 🖥️ Escalabilidade por Número de Servidores

| Servidores | Python (s) | Go (s) | Vencedor | Melhoria (%) |
|------------|------------|--------|----------|--------------|
| 2 | 1.2778 | 0.9542 | **Go** | 25.3 |
| 10 | 0.8183 | 0.9138 | **Python** | 10.5 |

## 5️⃣ Conclusões e Recomendações

### 🎯 Resumo Executivo

- ✅ **Python demonstrou competitividade em 64.0% dos cenários**
- 🤝 **Diferença média de apenas 10.91% entre as implementações**
- 📈 **Ambas linguagens mostram boa escalabilidade**

### 💡 Recomendações

- ✅ **Python mantém-se viável para a maioria dos casos**
- 🔧 **Foco na otimização antes de considerar mudança de linguagem**
- 🎯 **Go pode ser considerado para componentes específicos**

## � Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `performance_analysis_report.md` | Este relatório completo em Markdown |
| `analysis_results_interactive/` | Gráficos 3D de tempo total por cenário |
| `requests_python.csv` | Dados brutos Python |
| `requests_go.csv` | Dados brutos Go |

💡 **Dica:** Abra qualquer arquivo `.html` da pasta `analysis_results_interactive/` no navegador para visualização detalhada!

---
**Análise Concluída** ✅
