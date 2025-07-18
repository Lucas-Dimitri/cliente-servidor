#!/usr/bin/env python3
# Análise Textual dos Resultados - Cliente-Servidor Python vs Go
import pandas as pd
import numpy as np
from datetime import datetime


def analyze_performance():
    """
    Gera análise textual detalhada dos resultados de performance e salva em arquivo Markdown
    """
    # Configurar arquivo de saída
    output_file = "performance_analysis_report.md"

    # Criar buffer para capturar toda a saída
    output_lines = []

    def write_output(text):
        """Função auxiliar para escrever tanto no terminal quanto no buffer"""
        print(text)
        output_lines.append(text)

    # Cabeçalho do relatório
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_output("# 📊 Análise de Performance: Python vs Go")
    write_output("")
    write_output(f"**Relatório gerado em:** {timestamp}")
    write_output("")
    write_output("## 🎯 Metodologia")
    write_output("")
    write_output(
        "Este relatório analisa o **tempo total para processar todos os clientes** de cada cenário,"
    )
    write_output("não apenas o tempo médio individual. A fórmula utilizada é:")
    write_output("")
    write_output(
        "**Tempo Total do Cenário = Tempo Médio por Cliente × Número de Clientes**"
    )
    write_output("")
    write_output(
        "Esta abordagem fornece uma visão mais realista do desempenho total do sistema."
    )
    write_output("")
    write_output("---")

    # Carregar dados
    try:
        df_py = pd.read_csv("requests_python.csv")
        df_go = pd.read_csv("requests_go.csv")
    except FileNotFoundError as e:
        error_msg = f"❌ Erro: Arquivo não encontrado: {e.filename}"
        write_output(error_msg)
        # Salvar erro no arquivo
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        return

    # Preparar dados
    df_py["implementation"] = "Python"
    df_go["implementation"] = "Go"
    df_combined = pd.concat([df_py, df_go], ignore_index=True)

    # Limpeza de dados
    df_combined["response_time"] = pd.to_numeric(
        df_combined["response_time"], errors="coerce"
    )
    df_combined.dropna(subset=["response_time"], inplace=True)

    # Remover outliers (Z-score > 3)
    grouped = df_combined.groupby(
        ["num_servers", "num_clients", "num_messages", "implementation"]
    )
    df_combined["z_score"] = grouped["response_time"].transform(
        lambda x: np.abs((x - x.mean()) / x.std()) if x.std() > 0 else 0
    )
    df_cleaned = df_combined[df_combined["z_score"] <= 3]

    write_output("## � Resumo dos Dados")
    write_output("")
    write_output("| Métrica | Python | Go | Total |")
    write_output("|---------|--------|----|----|")
    write_output(
        f"| Requisições originais | {len(df_py):,} | {len(df_go):,} | {len(df_py) + len(df_go):,} |"
    )
    write_output(
        f"| Requisições após limpeza | {len(df_cleaned[df_cleaned['implementation'] == 'Python']):,} | {len(df_cleaned[df_cleaned['implementation'] == 'Go']):,} | {len(df_cleaned):,} |"
    )
    write_output(
        f"| Outliers removidos | - | - | {len(df_combined) - len(df_cleaned):,} |"
    )
    write_output("")

    # Estatísticas gerais
    write_output("## 1️⃣ Estatísticas Gerais")
    write_output("")

    stats_general = (
        df_cleaned.groupby("implementation")["response_time"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .round(6)
    )

    write_output("### � Estatísticas Detalhadas")
    write_output("")
    write_output(
        "| Implementação | Requisições | Tempo Médio (s) | Mediana (s) | Desvio Padrão (s) | Mínimo (s) | Máximo (s) |"
    )
    write_output(
        "|---------------|-------------|-----------------|-------------|------------------|------------|------------|"
    )

    for impl in ["Python", "Go"]:
        data = stats_general.loc[impl]
        write_output(
            f"| **{impl}** | {data['count']:,.0f} | {data['mean']:.4f} | {data['median']:.4f} | {data['std']:.4f} | {data['min']:.4f} | {data['max']:.4f} |"
        )

    write_output("")

    # Comparação direta
    py_mean = stats_general.loc["Python", "mean"]
    go_mean = stats_general.loc["Go", "mean"]
    difference = py_mean - go_mean
    # Diferença percentual sempre em relação ao mais lento
    if abs(go_mean) > abs(py_mean):
        percent_diff = (abs(difference) / abs(go_mean)) * 100
    else:
        percent_diff = (abs(difference) / abs(py_mean)) * 100

    write_output("### 🎯 Comparação Direta")
    write_output("")
    write_output("| Métrica | Valor |")
    write_output("|---------|-------|")
    write_output(f"| Diferença absoluta | **{difference:.4f}s** |")
    write_output(f"| Diferença percentual | **{percent_diff:.2f}%** |")

    if py_mean < go_mean:
        write_output(
            f"| **Resultado** | ✅ **Python é {percent_diff:.2f}% mais rápido que Go** |"
        )
    elif go_mean < py_mean:
        write_output(
            f"| **Resultado** | ✅ **Go é {percent_diff:.2f}% mais rápido que Python** |"
        )
    else:
        write_output(f"| **Resultado** | ⚖️ **Empate técnico** |")

    write_output("")

    # Análise por cenários
    write_output("## 2️⃣ Análise por Cenários")
    write_output("")

    scenarios = (
        df_cleaned.groupby(
            ["num_servers", "num_clients", "num_messages", "implementation"]
        )["response_time"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )

    # Melhor performance por cenário
    best_scenarios = []

    for (servers, clients, messages), group in scenarios.groupby(
        ["num_servers", "num_clients", "num_messages"]
    ):
        if len(group) == 2:  # Ambas implementações presentes
            py_time_avg = group[group["implementation"] == "Python"]["mean"].iloc[0]
            go_time_avg = group[group["implementation"] == "Go"]["mean"].iloc[0]

            # Calcular tempo total do cenário (tempo médio × número de clientes)
            py_time_total = py_time_avg * clients
            go_time_total = go_time_avg * clients

            winner = "Go" if go_time_total < py_time_total else "Python"
            improvement = (
                abs(py_time_total - go_time_total)
                / max(py_time_total, go_time_total)
                * 100
            )

            best_scenarios.append(
                {
                    "servers": servers,
                    "clients": clients,
                    "messages": messages,
                    "python_time": py_time_total,
                    "go_time": go_time_total,
                    "winner": winner,
                    "improvement": improvement,
                }
            )

    best_df = pd.DataFrame(best_scenarios)

    write_output(f"**Total de cenários analisados:** {len(best_df)}")
    write_output("")

    # Estatísticas dos vencedores
    go_wins = len(best_df[best_df["winner"] == "Go"])
    py_wins = len(best_df[best_df["winner"] == "Python"])

    write_output("### 🏆 Vencedores por Cenário")
    write_output("")
    write_output("| Implementação | Cenários Vencidos | Percentual |")
    write_output("|---------------|-------------------|------------|")
    write_output(f"| **Go** | {go_wins} | **{go_wins/len(best_df)*100:.1f}%** |")
    write_output(f"| **Python** | {py_wins} | **{py_wins/len(best_df)*100:.1f}%** |")
    write_output("")

    # Top 5 maiores melhorias
    top_improvements = best_df.nlargest(5, "improvement")

    write_output("### 🚀 Top 5 Maiores Diferenças de Tempo Total")
    write_output("")
    write_output(
        "| Ranking | Vencedor | Melhoria | Cenário | Python Total (s) | Go Total (s) |"
    )
    write_output(
        "|---------|----------|----------|---------|------------------|--------------|"
    )

    for idx, (i, row) in enumerate(top_improvements.iterrows(), 1):
        scenario = f"{int(row['servers'])} serv, {int(row['clients'])} cli, {int(row['messages'])} msg"
        write_output(
            f"| {idx} | **{row['winner']}** | **{row['improvement']:.1f}%** | {scenario} | {row['python_time']:.2f} | {row['go_time']:.2f} |"
        )

    write_output("")

    # Análise por número de mensagens
    write_output("## 3️⃣ Análise por Número de Mensagens")
    write_output("")

    msg_analysis = (
        df_cleaned.groupby(["num_messages", "implementation"])["response_time"]
        .mean()
        .unstack()
    )

    write_output("### 📨 Performance Média por Número de Mensagens")
    write_output("")
    write_output("| Mensagens | Python (s) | Go (s) | Vencedor | Melhoria |")
    write_output("|-----------|------------|--------|----------|----------|")

    for messages in sorted(df_cleaned["num_messages"].unique()):
        py_time = msg_analysis.loc[messages, "Python"]
        go_time = msg_analysis.loc[messages, "Go"]

        if py_time < go_time:
            improvement = (go_time - py_time) / go_time * 100
            winner = f"✅ **Python**"
            improvement_text = f"{improvement:.1f}% mais rápido"
        elif go_time < py_time:
            improvement = (py_time - go_time) / py_time * 100
            winner = f"✅ **Go**"
            improvement_text = f"{improvement:.1f}% mais rápido"
        else:
            winner = f"⚖️ Empate"
            improvement_text = "0.0%"

        write_output(
            f"| {int(messages):,} | {py_time:.4f} | {go_time:.4f} | {winner} | {improvement_text} |"
        )

    write_output("")

    # Análise de escalabilidade
    write_output("## 4️⃣ Análise de Escalabilidade")
    write_output("")

    # Performance vs número de clientes
    client_scale = (
        df_cleaned.groupby(["num_clients", "implementation"])["response_time"]
        .mean()
        .unstack()
    )

    write_output("### 👥 Escalabilidade por Número de Clientes")
    write_output("")
    write_output("| Clientes | Python (s) | Go (s) | Vencedor | Melhoria (%) |")
    write_output("|----------|------------|--------|----------|--------------|")

    for clients in sorted(df_cleaned["num_clients"].unique()):
        py_time = client_scale.loc[clients, "Python"]
        go_time = client_scale.loc[clients, "Go"]

        if py_time < go_time:
            winner = "**Python**"
            improvement = (go_time - py_time) / go_time * 100
        elif go_time < py_time:
            winner = "**Go**"
            improvement = (py_time - go_time) / py_time * 100
        else:
            winner = "⚖️ Empate"
            improvement = 0.0

        write_output(
            f"| {int(clients)} | {py_time:.4f} | {go_time:.4f} | {winner} | {improvement:.1f} |"
        )

    write_output("")

    # Performance vs número de servidores
    server_scale = (
        df_cleaned.groupby(["num_servers", "implementation"])["response_time"]
        .mean()
        .unstack()
    )

    write_output("### 🖥️ Escalabilidade por Número de Servidores")
    write_output("")
    write_output("| Servidores | Python (s) | Go (s) | Vencedor | Melhoria (%) |")
    write_output("|------------|------------|--------|----------|--------------|")

    for servers in sorted(df_cleaned["num_servers"].unique()):
        py_time = server_scale.loc[servers, "Python"]
        go_time = server_scale.loc[servers, "Go"]

        if py_time < go_time:
            winner = "**Python**"
            improvement = (go_time - py_time) / go_time * 100
        elif go_time < py_time:
            winner = "**Go**"
            improvement = (py_time - go_time) / py_time * 100
        else:
            winner = "⚖️ Empate"
            improvement = 0.0

        write_output(
            f"| {int(servers)} | {py_time:.4f} | {go_time:.4f} | {winner} | {improvement:.1f} |"
        )

    write_output("")

    # Conclusões
    write_output("## 5️⃣ Conclusões e Recomendações")
    write_output("")

    overall_go_wins = go_wins / len(best_df) * 100
    overall_py_wins = py_wins / len(best_df) * 100

    write_output("### 🎯 Resumo Executivo")
    write_output("")

    if overall_py_wins > 50:
        write_output(
            f"- ✅ **Python demonstrou superioridade em {overall_py_wins:.1f}% dos cenários**"
        )
        write_output(
            f"- 🚀 **Python é em média {abs(percent_diff):.2f}% mais rápido que Go**"
        )
        write_output(f"- 📈 **Python mostra melhor escalabilidade em cargas altas**")
        write_output("")

        write_output("### 💡 Recomendações")
        write_output("")
        write_output("- ⭐ **Priorizar Python para sistemas de alta performance**")
        write_output(
            "- 🔥 **Python é ideal para microserviços e APIs de baixa latência**"
        )
        write_output(
            "- 🔄 **Considerar migração gradual de componentes críticos para Python**"
        )
    elif overall_go_wins > 50:
        write_output(
            f"- ✅ **Go demonstrou superioridade em {overall_go_wins:.1f}% dos cenários**"
        )
        write_output(
            f"- 🚀 **Go é em média {abs(percent_diff):.2f}% mais rápido que Python**"
        )
        write_output(f"- 📈 **Go mostra melhor escalabilidade em cargas altas**")
        write_output("")

        write_output("### 💡 Recomendações")
        write_output("")
        write_output("- ⭐ **Priorizar Go para sistemas de alta performance**")
        write_output("- 🔥 **Go é ideal para microserviços e APIs de baixa latência**")
        write_output(
            "- 🔄 **Considerar migração gradual de componentes críticos para Go**"
        )
    else:
        write_output(
            f"- ⚖️ **Empate técnico: ambas as linguagens apresentam desempenho semelhante**"
        )
        write_output(f"- 📈 **Ambas linguagens mostram boa escalabilidade**")
        write_output("")

        write_output("### 💡 Recomendações")
        write_output("")
        write_output(
            "- ✅ **Ambas as linguagens são viáveis para a maioria dos casos**"
        )
        write_output(
            "- 🔧 **Foco na otimização antes de considerar mudança de linguagem**"
        )
        write_output(
            "- 🎯 **Escolha pode ser baseada em outros critérios (equipe, ecossistema, etc.)**"
        )

    write_output("")

    write_output("## � Arquivos Gerados")
    write_output("")
    write_output("| Arquivo | Descrição |")
    write_output("|---------|-----------|")
    write_output(f"| `{output_file}` | Este relatório completo em Markdown |")
    write_output(
        "| `analysis_results_interactive/` | Gráficos 3D de tempo total por cenário |"
    )
    write_output("| `requests_python.csv` | Dados brutos Python |")
    write_output("| `requests_go.csv` | Dados brutos Go |")
    write_output("")
    write_output(
        "💡 **Dica:** Abra qualquer arquivo `.html` da pasta `analysis_results_interactive/` no navegador para visualização detalhada!"
    )
    write_output("")

    write_output("---")
    write_output("**Análise Concluída** ✅")
    write_output("")

    # Salvar relatório em arquivo
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        print(f"\n💾 Relatório salvo em: {output_file}")
        print(f"📄 Total de linhas: {len(output_lines)}")
        print(f"📂 Arquivo criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return

    return output_file


if __name__ == "__main__":
    report_file = analyze_performance()
    if report_file:
        print(f"\n🎉 Análise concluída! Relatório disponível em: {report_file}")
