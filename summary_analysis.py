#!/usr/bin/env python3
# Análise Textual dos Resultados - Cliente-Servidor Python vs Go
import pandas as pd
import numpy as np


def analyze_performance():
    """
    Gera análise textual detalhada dos resultados de performance
    """
    print("=" * 70)
    print("     ANÁLISE DE PERFORMANCE: PYTHON vs GO")
    print("=" * 70)

    # Carregar dados
    try:
        df_py = pd.read_csv("requests_python.csv")
        df_go = pd.read_csv("requests_go.csv")
    except FileNotFoundError as e:
        print(f"❌ Erro: Arquivo não encontrado: {e.filename}")
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

    print(f"📊 Dados carregados:")
    print(f"   • Python: {len(df_py):,} requisições")
    print(f"   • Go: {len(df_go):,} requisições")
    print(f"   • Total após limpeza: {len(df_cleaned):,} requisições")
    print(f"   • Outliers removidos: {len(df_combined) - len(df_cleaned):,}")

    # Estatísticas gerais
    print("\n" + "=" * 70)
    print("1. ESTATÍSTICAS GERAIS")
    print("=" * 70)

    stats_general = (
        df_cleaned.groupby("implementation")["response_time"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .round(6)
    )

    print("\n📈 Resumo Geral:")
    for impl in ["Python", "Go"]:
        data = stats_general.loc[impl]
        print(f"\n{impl}:")
        print(f"   • Requisições: {data['count']:,}")
        print(f"   • Tempo médio: {data['mean']:.4f}s")
        print(f"   • Mediana: {data['median']:.4f}s")
        print(f"   • Desvio padrão: {data['std']:.4f}s")
        print(f"   • Mínimo: {data['min']:.4f}s")
        print(f"   • Máximo: {data['max']:.4f}s")

    # Comparação direta
    py_mean = stats_general.loc["Python", "mean"]
    go_mean = stats_general.loc["Go", "mean"]
    difference = py_mean - go_mean
    percent_diff = (difference / py_mean) * 100

    print(f"\n🎯 Comparação Direta:")
    print(f"   • Diferença absoluta: {difference:.4f}s")
    print(f"   • Diferença percentual: {percent_diff:.2f}%")
    if go_mean < py_mean:
        print(f"   • ✅ Go é {abs(percent_diff):.2f}% mais rápido que Python")
    else:
        print(f"   • ✅ Python é {abs(percent_diff):.2f}% mais rápido que Go")

    # Análise por cenários
    print("\n" + "=" * 70)
    print("2. ANÁLISE POR CENÁRIOS")
    print("=" * 70)

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
            py_time = group[group["implementation"] == "Python"]["mean"].iloc[0]
            go_time = group[group["implementation"] == "Go"]["mean"].iloc[0]

            winner = "Go" if go_time < py_time else "Python"
            improvement = abs(py_time - go_time) / max(py_time, go_time) * 100

            best_scenarios.append(
                {
                    "servers": servers,
                    "clients": clients,
                    "messages": messages,
                    "python_time": py_time,
                    "go_time": go_time,
                    "winner": winner,
                    "improvement": improvement,
                }
            )

    best_df = pd.DataFrame(best_scenarios)

    print(f"\n📋 Análise de {len(best_df)} cenários completos:")

    # Estatísticas dos vencedores
    go_wins = len(best_df[best_df["winner"] == "Go"])
    py_wins = len(best_df[best_df["winner"] == "Python"])

    print(f"\n🏆 Vencedores por cenário:")
    print(f"   • Go venceu: {go_wins} cenários ({go_wins/len(best_df)*100:.1f}%)")
    print(f"   • Python venceu: {py_wins} cenários ({py_wins/len(best_df)*100:.1f}%)")

    # Top 5 maiores melhorias
    print(f"\n🚀 Top 5 maiores diferenças de performance:")
    top_improvements = best_df.nlargest(5, "improvement")

    for i, row in top_improvements.iterrows():
        print(f"   {row['winner']} foi {row['improvement']:.1f}% melhor")
        print(
            f"     Cenário: {int(row['servers'])} serv, {int(row['clients'])} cli, {int(row['messages'])} msg"
        )
        print(f"     Python: {row['python_time']:.4f}s vs Go: {row['go_time']:.4f}s")
        print()

    # Análise por número de mensagens
    print("\n" + "=" * 70)
    print("3. ANÁLISE POR NÚMERO DE MENSAGENS")
    print("=" * 70)

    msg_analysis = (
        df_cleaned.groupby(["num_messages", "implementation"])["response_time"]
        .mean()
        .unstack()
    )

    print("\n📨 Performance média por número de mensagens:")
    for messages in sorted(df_cleaned["num_messages"].unique()):
        py_time = msg_analysis.loc[messages, "Python"]
        go_time = msg_analysis.loc[messages, "Go"]

        print(f"\n{int(messages)} mensagem(s):")
        print(f"   • Python: {py_time:.4f}s")
        print(f"   • Go: {go_time:.4f}s")

        if go_time < py_time:
            improvement = (py_time - go_time) / py_time * 100
            print(f"   • ✅ Go é {improvement:.1f}% mais rápido")
        else:
            improvement = (go_time - py_time) / go_time * 100
            print(f"   • ✅ Python é {improvement:.1f}% mais rápido")

    # Análise de escalabilidade
    print("\n" + "=" * 70)
    print("4. ANÁLISE DE ESCALABILIDADE")
    print("=" * 70)

    # Performance vs número de clientes
    client_scale = (
        df_cleaned.groupby(["num_clients", "implementation"])["response_time"]
        .mean()
        .unstack()
    )

    print("\n👥 Escalabilidade por número de clientes:")
    print(
        f"{'Clientes':<10} {'Python (s)':<12} {'Go (s)':<10} {'Vencedor':<10} {'Melhoria (%)'}"
    )
    print("-" * 60)

    for clients in sorted(df_cleaned["num_clients"].unique()):
        py_time = client_scale.loc[clients, "Python"]
        go_time = client_scale.loc[clients, "Go"]

        if go_time < py_time:
            winner = "Go"
            improvement = (py_time - go_time) / py_time * 100
        else:
            winner = "Python"
            improvement = (go_time - py_time) / go_time * 100

        print(
            f"{int(clients):<10} {py_time:<12.4f} {go_time:<10.4f} {winner:<10} {improvement:.1f}"
        )

    # Performance vs número de servidores
    server_scale = (
        df_cleaned.groupby(["num_servers", "implementation"])["response_time"]
        .mean()
        .unstack()
    )

    print("\n🖥️  Escalabilidade por número de servidores:")
    print(
        f"{'Servidores':<12} {'Python (s)':<12} {'Go (s)':<10} {'Vencedor':<10} {'Melhoria (%)'}"
    )
    print("-" * 62)

    for servers in sorted(df_cleaned["num_servers"].unique()):
        py_time = server_scale.loc[servers, "Python"]
        go_time = server_scale.loc[servers, "Go"]

        if go_time < py_time:
            winner = "Go"
            improvement = (py_time - go_time) / py_time * 100
        else:
            winner = "Python"
            improvement = (go_time - py_time) / go_time * 100

        print(
            f"{int(servers):<12} {py_time:<12.4f} {go_time:<10.4f} {winner:<10} {improvement:.1f}"
        )

    # Conclusões
    print("\n" + "=" * 70)
    print("5. CONCLUSÕES E RECOMENDAÇÕES")
    print("=" * 70)

    overall_go_wins = go_wins / len(best_df) * 100

    print(f"\n🎯 Resumo Executivo:")

    if overall_go_wins > 50:
        print(
            f"   • ✅ Go demonstrou superioridade em {overall_go_wins:.1f}% dos cenários"
        )
        print(f"   • 🚀 Go é em média {abs(percent_diff):.2f}% mais rápido que Python")
        print(f"   • 📈 Go mostra melhor escalabilidade em cargas altas")

        print(f"\n💡 Recomendações:")
        print(f"   • Priorizar Go para sistemas de alta performance")
        print(f"   • Go é ideal para microserviços e APIs de baixa latência")
        print(f"   • Considerar migração gradual de componentes críticos")
    else:
        print(
            f"   • ✅ Python demonstrou competitividade em {100-overall_go_wins:.1f}% dos cenários"
        )
        print(
            f"   • 🤝 Diferença média de apenas {abs(percent_diff):.2f}% entre as implementações"
        )
        print(f"   • 📈 Ambas linguagens mostram boa escalabilidade")

        print(f"\n💡 Recomendações:")
        print(f"   • Python mantém-se viável para a maioria dos casos")
        print(f"   • Foco na otimização antes de considerar mudança de linguagem")
        print(f"   • Go pode ser considerado para componentes específicos")

    print(f"\n📊 Arquivos de visualização gerados:")
    print(f"   • analysis_results_interactive/ (12 gráficos 3D interativos)")
    print(f"   • Abra qualquer .html no navegador para visualização detalhada")

    print("\n" + "=" * 70)
    print("     ANÁLISE CONCLUÍDA")
    print("=" * 70)


if __name__ == "__main__":
    analyze_performance()
