# 📊 Análise de Performance: Python vs Go

**Relatório gerado em:** 2025-07-15 15:20:18

---
## � Resumo dos Dados

| Métrica | Python | Go | Total |
|---------|--------|----|----|
| Requisições originais | 82,500 | 82,500 | 165,000 |
| Requisições após limpeza | 80,713 | 80,705 | 161,418 |
| Outliers removidos | - | - | 3,582 |

## 1️⃣ Estatísticas Gerais

### � Estatísticas Detalhadas

| Implementação | Requisições | Tempo Médio (s) | Mediana (s) | Desvio Padrão (s) | Mínimo (s) | Máximo (s) |
|---------------|-------------|-----------------|-------------|------------------|------------|------------|
| **Python** | 80,713 | 0.0120 | 0.0092 | 0.0080 | 0.0035 | 0.0776 |
| **Go** | 80,705 | 0.0094 | 0.0073 | 0.0060 | 0.0030 | 0.0588 |

### 🎯 Comparação Direta

| Métrica | Valor |
|---------|-------|
| Diferença absoluta | **0.0026s** |
| Diferença percentual | **21.92%** |
| **Resultado** | ✅ **Go é 21.92% mais rápido que Python** |

## 2️⃣ Análise por Cenários

**Total de cenários analisados:** 300

### 🏆 Vencedores por Cenário

| Implementação | Cenários Vencidos | Percentual |
|---------------|-------------------|------------|
| **Go** | 300 | **100.0%** |
| **Python** | 0 | **0.0%** |

### 🚀 Top 5 Maiores Diferenças de Performance

| Ranking | Vencedor | Melhoria | Cenário | Python (s) | Go (s) |
|---------|----------|----------|---------|------------|--------|
| 1 | **Go** | **40.2%** | 8 serv, 40 cli, 1000 msg | 0.0134 | 0.0080 |
| 2 | **Go** | **38.1%** | 4 serv, 70 cli, 1 msg | 0.0141 | 0.0087 |
| 3 | **Go** | **36.5%** | 4 serv, 70 cli, 100 msg | 0.0139 | 0.0088 |
| 4 | **Go** | **35.2%** | 6 serv, 100 cli, 10000 msg | 0.0154 | 0.0100 |
| 5 | **Go** | **34.9%** | 10 serv, 80 cli, 1 msg | 0.0148 | 0.0096 |

## 3️⃣ Análise por Número de Mensagens

### 📨 Performance Média por Número de Mensagens

| Mensagens | Python (s) | Go (s) | Vencedor | Melhoria |
|-----------|------------|--------|----------|----------|
| 1 | 0.0120 | 0.0094 | ✅ **Go** | 21.8% mais rápido |
| 10 | 0.0119 | 0.0094 | ✅ **Go** | 21.2% mais rápido |
| 100 | 0.0119 | 0.0095 | ✅ **Go** | 20.5% mais rápido |
| 500 | 0.0122 | 0.0093 | ✅ **Go** | 23.9% mais rápido |
| 1,000 | 0.0119 | 0.0093 | ✅ **Go** | 21.7% mais rápido |
| 10,000 | 0.0121 | 0.0094 | ✅ **Go** | 22.3% mais rápido |

## 4️⃣ Análise de Escalabilidade

### 👥 Escalabilidade por Número de Clientes

| Clientes | Python (s) | Go (s) | Vencedor | Melhoria (%) |
|----------|------------|--------|----------|--------------|
| 10 | 0.0059 | 0.0050 | **Go** | 16.0 |
| 20 | 0.0082 | 0.0067 | **Go** | 17.7 |
| 30 | 0.0090 | 0.0072 | **Go** | 20.1 |
| 40 | 0.0107 | 0.0088 | **Go** | 17.2 |
| 50 | 0.0111 | 0.0090 | **Go** | 18.6 |
| 60 | 0.0115 | 0.0090 | **Go** | 21.5 |
| 70 | 0.0122 | 0.0093 | **Go** | 23.6 |
| 80 | 0.0124 | 0.0097 | **Go** | 22.2 |
| 90 | 0.0133 | 0.0102 | **Go** | 23.2 |
| 100 | 0.0140 | 0.0107 | **Go** | 23.6 |

### 🖥️ Escalabilidade por Número de Servidores

| Servidores | Python (s) | Go (s) | Vencedor | Melhoria (%) |
|------------|------------|--------|----------|--------------|
| 2 | 0.0117 | 0.0093 | **Go** | 20.1 |
| 4 | 0.0122 | 0.0092 | **Go** | 24.6 |
| 6 | 0.0119 | 0.0093 | **Go** | 22.2 |
| 8 | 0.0120 | 0.0094 | **Go** | 22.0 |
| 10 | 0.0122 | 0.0097 | **Go** | 20.6 |

## 5️⃣ Conclusões e Recomendações

### 🎯 Resumo Executivo

- ✅ **Go demonstrou superioridade em 100.0% dos cenários**
- 🚀 **Go é em média 21.92% mais rápido que Python**
- 📈 **Go mostra melhor escalabilidade em cargas altas**

### 💡 Recomendações

- ⭐ **Priorizar Go para sistemas de alta performance**
- 🔥 **Go é ideal para microserviços e APIs de baixa latência**
- 🔄 **Considerar migração gradual de componentes críticos**

## � Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `performance_analysis_report.md` | Este relatório completo em Markdown |
| `analysis_results_interactive/` | 16 gráficos 3D interativos |
| `requests_python.csv` | Dados brutos Python |
| `requests_go.csv` | Dados brutos Go |

💡 **Dica:** Abra qualquer arquivo `.html` da pasta `analysis_results_interactive/` no navegador para visualização detalhada!

---
**Análise Concluída** ✅
