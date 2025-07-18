# 📊 Análise de Performance: Python vs Go

**Relatório gerado em:** 2025-07-18 18:40:07

## 🎯 Metodologia

Este relatório analisa o **tempo total para processar todos os clientes** de cada cenário,
não apenas o tempo médio individual. A fórmula utilizada é:

**Tempo Total do Cenário = Tempo Médio por Cliente × Número de Clientes**

Esta abordagem fornece uma visão mais realista do desempenho total do sistema.

---
## � Resumo dos Dados

| Métrica | Python | Go | Total |
|---------|--------|----|----|
| Requisições originais | 22,000 | 22,000 | 44,000 |
| Requisições após limpeza | 21,704 | 21,748 | 43,452 |
| Outliers removidos | - | - | 548 |

## 1️⃣ Estatísticas Gerais

### � Estatísticas Detalhadas

| Implementação | Requisições | Tempo Médio (s) | Mediana (s) | Desvio Padrão (s) | Mínimo (s) | Máximo (s) |
|---------------|-------------|-----------------|-------------|------------------|------------|------------|
| **Python** | 21,704 | 0.8701 | 0.2161 | 1.1519 | 0.0012 | 6.9991 |
| **Go** | 21,748 | 0.8262 | 0.2436 | 1.0067 | 0.0013 | 4.1157 |

### 🎯 Comparação Direta

| Métrica | Valor |
|---------|-------|
| Diferença absoluta | **0.0439s** |
| Diferença percentual | **5.04%** |
| **Resultado** | ✅ **Go é 5.04% mais rápido que Python** |

## 2️⃣ Análise por Cenários

**Total de cenários analisados:** 200

### 🏆 Vencedores por Cenário

| Implementação | Cenários Vencidos | Percentual |
|---------------|-------------------|------------|
| **Go** | 39 | **19.5%** |
| **Python** | 161 | **80.5%** |

### 🚀 Top 5 Maiores Diferenças de Tempo Total

| Ranking | Vencedor | Melhoria | Cenário | Python Total (s) | Go Total (s) |
|---------|----------|----------|---------|------------------|--------------|
| 1 | **Go** | **44.0%** | 2 serv, 100 cli, 500 msg | 247.79 | 138.65 |
| 2 | **Go** | **43.6%** | 2 serv, 90 cli, 1000 msg | 422.21 | 238.28 |
| 3 | **Go** | **39.9%** | 2 serv, 100 cli, 1000 msg | 481.94 | 289.54 |
| 4 | **Python** | **38.8%** | 2 serv, 90 cli, 1 msg | 0.20 | 0.33 |
| 5 | **Go** | **36.5%** | 2 serv, 90 cli, 500 msg | 204.55 | 129.81 |

## 3️⃣ Análise por Número de Mensagens

### 📨 Performance Média por Número de Mensagens

| Mensagens | Python (s) | Go (s) | Vencedor | Melhoria |
|-----------|------------|--------|----------|----------|
| 1 | 0.0024 | 0.0030 | ✅ **Python** | 19.3% mais rápido |
| 10 | 0.0217 | 0.0246 | ✅ **Python** | 12.1% mais rápido |
| 100 | 0.2268 | 0.2513 | ✅ **Python** | 9.7% mais rápido |
| 500 | 1.3284 | 1.2648 | ✅ **Go** | 4.8% mais rápido |
| 1,000 | 2.7259 | 2.5460 | ✅ **Go** | 6.6% mais rápido |

## 4️⃣ Análise de Escalabilidade

### 👥 Escalabilidade por Número de Clientes

| Clientes | Python (s) | Go (s) | Vencedor | Melhoria (%) |
|----------|------------|--------|----------|--------------|
| 10 | 0.6487 | 0.6457 | **Go** | 0.5 |
| 20 | 0.6519 | 0.6556 | **Python** | 0.6 |
| 30 | 0.6624 | 0.6818 | **Python** | 2.8 |
| 40 | 0.6791 | 0.7030 | **Python** | 3.4 |
| 50 | 0.7312 | 0.7579 | **Python** | 3.5 |
| 60 | 0.7855 | 0.7938 | **Python** | 1.0 |
| 70 | 0.8518 | 0.8524 | **Python** | 0.1 |
| 80 | 0.9346 | 0.8665 | **Go** | 7.3 |
| 90 | 0.9933 | 0.8930 | **Go** | 10.1 |
| 100 | 1.0448 | 0.9137 | **Go** | 12.5 |

### 🖥️ Escalabilidade por Número de Servidores

| Servidores | Python (s) | Go (s) | Vencedor | Melhoria (%) |
|------------|------------|--------|----------|--------------|
| 2 | 1.1237 | 0.8303 | **Go** | 26.1 |
| 4 | 0.8472 | 0.8059 | **Go** | 4.9 |
| 6 | 0.7680 | 0.8451 | **Python** | 9.1 |
| 8 | 0.7408 | 0.8235 | **Python** | 10.0 |

## 5️⃣ Conclusões e Recomendações

### 🎯 Resumo Executivo

- ✅ **Python demonstrou superioridade em 80.5% dos cenários**
- 🚀 **Python é em média 5.04% mais rápido que Go**
- 📈 **Python mostra melhor escalabilidade em cargas altas**

### 💡 Recomendações

- ⭐ **Priorizar Python para sistemas de alta performance**
- 🔥 **Python é ideal para microserviços e APIs de baixa latência**
- 🔄 **Considerar migração gradual de componentes críticos para Python**

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
