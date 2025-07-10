# In a new file (e.g., analyze.py)
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import shutil
import sys


def analyze_file(input_file, results_dir_suffix=""):
    """
    Analyzes a single request data file, calculates statistics, and generates graphs.
    """
    # --- Configuração ---
    Z_SCORE_THRESHOLD = 3
    RESULTS_DIR = "analysis_results"
    if results_dir_suffix:
        RESULTS_DIR = f"{RESULTS_DIR}_{results_dir_suffix}"

    # --- Limpa e cria o diretório de resultados ---
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
    os.makedirs(RESULTS_DIR)

    # --- Carregamento e Limpeza dos Dados ---
    print(f"Carregando dados de: {input_file}")
    try:
        df = pd.read_csv(input_file)
        if df.empty:
            print(f"Aviso: Arquivo '{input_file}' está vazio.")
            return None
    except FileNotFoundError:
        print(f"Erro: Arquivo '{input_file}' não encontrado.")
        return None

    # Renomeia as colunas para corresponder às expectativas do script
    df.rename(
        columns={
            "num_servers": "servers",
            "num_clients": "clients",
            "num_messages": "messages",
        },
        inplace=True,
    )

    required_cols = [
        "servers",
        "clients",
        "messages",
        "response_time",
        "client_receive_time",
    ]
    if not all(col in df.columns for col in required_cols):
        print(
            f"Erro: O arquivo {input_file} não contém todas as colunas necessárias: {required_cols}"
        )
        return None

    df["response_time"] = pd.to_numeric(df["response_time"], errors="coerce")
    df.dropna(subset=["response_time"], inplace=True)

    # --- Conversão de Timestamp ---
    # Usa 'client_receive_time' como o timestamp principal para a análise
    df["timestamp"] = pd.to_datetime(
        df["client_receive_time"], format="mixed", errors="coerce", utc=True
    )
    df.dropna(subset=["timestamp"], inplace=True)

    # --- Remoção de Outliers com Z-score ---
    print(f"Removendo outliers com Z-score > {Z_SCORE_THRESHOLD}...")
    # Handle cases with single data points in a group where std is 0
    grouped = df.groupby(["servers", "clients", "messages"])
    df["z_score"] = grouped["response_time"].transform(
        lambda x: np.abs((x - x.mean()) / x.std()) if x.std() > 0 else 0
    )
    df_cleaned = df[df["z_score"] <= Z_SCORE_THRESHOLD]
    print(f"Removidas {len(df) - len(df_cleaned)} linhas como outliers.")

    # --- Cálculo das Estatísticas Agregadas ---
    print("Calculando estatísticas agregadas...")
    stats = (
        df_cleaned.groupby(["servers", "clients", "messages"])["response_time"]
        .agg(["mean", "median", "min", "max", "std"])
        .reset_index()
    )
    stats.to_csv(f"{RESULTS_DIR}/estatisticas_agregadas.csv", index=False)
    print(f"Estatísticas salvas em {RESULTS_DIR}/estatisticas_agregadas.csv")

    # --- Cálculo de Throughput ---
    print("Calculando throughput...")
    # Agrupa por cenário de teste
    grouped = df_cleaned.groupby(["servers", "clients", "messages"])

    # Calcula o número de requisições por grupo
    requests = grouped.size()

    # Calcula a duração de cada grupo (diferença entre o último e o primeiro timestamp)
    duration_td = grouped["timestamp"].max() - grouped["timestamp"].min()

    # Converte a duração para segundos. Se a duração for zero, usa 1 segundo para evitar divisão por zero.
    duration_s = duration_td.dt.total_seconds().where(lambda x: x > 0, 1)

    # Calcula o throughput (requisições por segundo)
    throughput = requests / duration_s

    # Preenche valores NaN ou infinitos com 0 (caso de grupos com 1 request)
    throughput.fillna(0, inplace=True)
    throughput.replace([np.inf, -np.inf], 0, inplace=True)

    print("Estatísticas de Throughput (requisições/segundo):")
    print(throughput.describe())

    # Salva o throughput em um arquivo CSV
    throughput.to_csv(os.path.join(RESULTS_DIR, "throughput.csv"))

    # Adiciona o throughput ao DataFrame de estatísticas
    stats = pd.merge(
        stats,
        throughput.reset_index(name="throughput"),
        on=["servers", "clients", "messages"],
    )

    if stats.empty:
        print(f"Aviso: Nenhuma estatística para plotar para {input_file}.")
        return stats

    # --- Geração de Gráfico de Throughput ---
    print("Gerando gráfico de throughput...")
    plt.figure(figsize=(12, 8))
    for srv in sorted(stats["servers"].unique()):
        subset = stats[stats["servers"] == srv]
        # Plot throughput vs. clients. Grouping by messages will create multiple lines if needed.
        for msg_count in sorted(subset["messages"].unique()):
            scenario_subset = subset[subset["messages"] == msg_count]
            plt.plot(
                scenario_subset["clients"],
                scenario_subset["throughput"],
                marker="o",
                linestyle="-",
                label=f"{srv} Servidores, {msg_count} Mensagens",
            )
    plt.title("Throughput vs. Número de Clientes")
    plt.xlabel("Número de Clientes")
    plt.ylabel("Throughput (requisições/s)")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/throughput_vs_clientes.png")
    print("Gráfico 'Throughput' salvo.")

    # --- Geração de Gráficos ---

    # Gráfico 1: Tempo de Resposta Médio vs. Clientes (com desvio padrão)
    plt.figure(figsize=(12, 8))
    for srv in sorted(stats["servers"].unique()):
        subset = stats[stats["servers"] == srv]
        plt.errorbar(
            subset["clients"],
            subset["mean"],
            yerr=subset["std"],
            marker="o",
            capsize=5,
            label=f"{srv} Servidores",
        )
    plt.title("Tempo de Resposta Médio vs. Número de Clientes")
    plt.xlabel("Número de Clientes")
    plt.ylabel("Tempo de Resposta Médio (s)")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/tempo_resposta_vs_clientes.png")
    print("Gráfico 'Tempo de Resposta' salvo.")

    print(f"\nAnálise concluída para {input_file}!")
    return stats


def compare_results(file_py, file_go):
    """
    Compares results from Python and Go implementations and generates a comparative graph.
    """
    print("--- Carregando dados para comparação ---")
    try:
        df_py = pd.read_csv(file_py)
        df_go = pd.read_csv(file_go)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo de resultados não encontrado: {e.filename}")
        return

    df_py["implementation"] = "Python"
    df_go["implementation"] = "Go"

    df_combined = pd.concat([df_py, df_go], ignore_index=True)

    # Renomeia colunas se necessário
    df_combined.rename(
        columns={
            "num_servers": "servers",
            "num_clients": "clients",
            "num_messages": "messages",
        },
        inplace=True,
    )

    # --- Limpeza e Remoção de Outliers ---
    df_combined["response_time"] = pd.to_numeric(
        df_combined["response_time"], errors="coerce"
    )
    df_combined.dropna(subset=["response_time"], inplace=True)

    # --- Conversão de Timestamp para a comparação ---
    if "client_receive_time" in df_combined.columns:
        df_combined["timestamp"] = pd.to_datetime(
            df_combined["client_receive_time"],
            format="mixed",
            errors="coerce",
            utc=True,
        )
        df_combined.dropna(subset=["timestamp"], inplace=True)
    else:
        print("Aviso: Coluna 'client_receive_time' não encontrada para a comparação.")

    grouped = df_combined.groupby(["servers", "clients", "messages", "implementation"])
    df_combined["z_score"] = grouped["response_time"].transform(
        lambda x: np.abs((x - x.mean()) / x.std()) if x.std() > 0 else 0
    )
    df_cleaned = df_combined[df_combined["z_score"] <= 3]

    # --- Cálculo das Estatísticas Agregadas ---
    print("Calculando estatísticas agregadas para comparação...")
    stats_combined = (
        df_cleaned.groupby(["servers", "clients", "implementation"])["response_time"]
        .agg(["mean", "std"])
        .reset_index()
    )

    # --- Geração do Gráfico Comparativo ---
    RESULTS_DIR = "analysis_results"
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    print("Gerando gráfico comparativo...")
    plt.figure(figsize=(15, 10))
    # Create a scenario label for the x-axis
    stats_combined["scenario"] = stats_combined.apply(
        lambda row: f"{row['clients']} Clientes, {row['servers']} Servidores", axis=1
    )

    sns.barplot(
        data=stats_combined,
        x="scenario",
        y="mean",
        hue="implementation",
        palette={"Python": "skyblue", "Go": "lightgreen"},
    )

    plt.title("Comparativo de Desempenho: Python vs. Go", fontsize=16)
    plt.xlabel("Cenário de Teste", fontsize=12)
    plt.ylabel("Tempo de Resposta Médio (s)", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Implementação")
    plt.grid(axis="y", linestyle="--", linewidth=0.7)
    plt.tight_layout()

    output_path = f"{RESULTS_DIR}/comparativo_python_vs_go.png"
    plt.savefig(output_path)
    print(f"Gráfico comparativo salvo em: {output_path}")
    print("\nAnálise comparativa concluída!")


def generate_advanced_report(df_py, df_go):
    """
    Calculates advanced performance metrics and generates a radar chart and summary table.
    """
    print("\n--- Gerando Relatório de Métricas Avançadas ---")
    RESULTS_DIR = "analysis_results"
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    metrics_data = []

    for df, name in [(df_py, "Python"), (df_go, "Go")]:
        # --- Check for empty dataframe ---
        if df.empty:
            print(f"Aviso: DataFrame para '{name}' está vazio. Métricas serão zeradas.")
            metrics_data.append(
                {
                    "Implementação": name,
                    "Escalabilidade": 0,
                    "Speedup": 0,
                    "Eficiência Relativa": 0,
                    "Consistência (DPR)": np.inf,
                    "Overhead (ms/cli)": np.inf,
                    "Resp. por Mensagem (ms)": np.inf,
                }
            )
            continue

        # --- Pre-processing ---
        df.rename(
            columns={
                "num_servers": "servers",
                "num_clients": "clients",
                "num_messages": "messages",
            },
            inplace=True,
        )

        required_cols = [
            "servers",
            "clients",
            "messages",
            "response_time",
            "client_receive_time",
        ]
        if not all(col in df.columns for col in required_cols):
            print(
                f"Aviso: Colunas necessárias ausentes para '{name}'. Pulando métricas avançadas."
            )
            metrics_data.append(
                {
                    "Implementação": name,
                    "Escalabilidade": 0,
                    "Speedup": 0,
                    "Eficiência Relativa": 0,
                    "Consistência (DPR)": np.inf,
                    "Overhead (ms/cli)": np.inf,
                    "Resp. por Mensagem (ms)": np.inf,
                }
            )
            continue

        df["timestamp"] = pd.to_datetime(
            df["client_receive_time"], format="mixed", errors="coerce", utc=True
        )
        df["response_time"] = pd.to_numeric(df["response_time"], errors="coerce")
        df.dropna(subset=["timestamp", "response_time"], inplace=True)

        if df.empty:
            print(
                f"Aviso: DataFrame para '{name}' vazio após limpeza. Métricas serão zeradas."
            )
            metrics_data.append(
                {
                    "Implementação": name,
                    "Escalabilidade": 0,
                    "Speedup": 0,
                    "Eficiência Relativa": 0,
                    "Consistência (DPR)": np.inf,
                    "Overhead (ms/cli)": np.inf,
                    "Resp. por Mensagem (ms)": np.inf,
                }
            )
            continue

        # --- Throughput Calculation ---
        group_cols = ["servers", "clients", "messages"]
        duration = df.groupby(group_cols)["timestamp"].apply(
            lambda x: (x.max() - x.min()).total_seconds()
        )
        duration = duration.where(duration > 0, 1)  # Avoid division by zero

        requests = df.groupby(group_cols).size()
        throughput_runs = (requests / duration).reset_index(name="throughput")
        throughput_stats = (
            throughput_runs.groupby(["servers", "clients"])["throughput"]
            .agg(["mean", "std"])
            .reset_index()
        )

        if throughput_stats.empty:
            print(
                f"Aviso: Não foi possível calcular o throughput para '{name}'. Pulando métricas."
            )
            metrics_data.append(
                {
                    "Implementação": name,
                    "Escalabilidade": 0,
                    "Speedup": 0,
                    "Eficiência Relativa": 0,
                    "Consistência (DPR)": np.inf,
                    "Overhead (ms/cli)": np.inf,
                    "Resp. por Mensagem (ms)": np.inf,
                }
            )
            continue

        # --- Base Metrics for a high-load scenario ---
        max_clients = throughput_stats["clients"].max()
        high_load_stats = throughput_stats[throughput_stats["clients"] == max_clients]

        # --- Advanced Metrics Calculation ---
        if high_load_stats.empty or high_load_stats["servers"].nunique() < 2:
            print(
                f"Aviso: Dados insuficientes para calcular escalabilidade para '{name}'."
            )
            escalabilidade = 0
            speedup = 0
        else:
            t_s_min = high_load_stats[
                high_load_stats["servers"] == high_load_stats["servers"].min()
            ]["mean"].iloc[0]
            t_s_max = high_load_stats[
                high_load_stats["servers"] == high_load_stats["servers"].max()
            ]["mean"].iloc[0]
            s_min = high_load_stats["servers"].min()
            s_max = high_load_stats["servers"].max()
            escalabilidade = (
                (t_s_max / t_s_min) / (s_max / s_min)
                if t_s_min > 0 and s_min > 0 and s_max > s_min
                else 0
            )
            speedup = t_s_max / t_s_min if t_s_min > 0 else 0

        # 3. Eficiência Relativa
        eficiencia = (
            (high_load_stats["mean"] / high_load_stats["servers"]).mean()
            if not high_load_stats.empty
            else 0
        )

        # 4. Consistência (DPR)
        consistencia = (
            (df["response_time"].std() / df["response_time"].mean())
            if df["response_time"].mean() > 0
            else np.inf
        )

        # 5. Overhead
        overhead = (
            (df["response_time"].mean() * 1000) / df["clients"].mean()
            if df["clients"].mean() > 0
            else np.inf
        )

        # 6. Resposta por Mensagem
        resp_por_msg = df["response_time"].mean() * 1000

        metrics_data.append(
            {
                "Implementação": name,
                "Escalabilidade": escalabilidade,
                "Speedup": speedup,
                "Eficiência Relativa": eficiencia,
                "Consistência (DPR)": consistencia,
                "Overhead (ms/cli)": overhead,
                "Resp. por Mensagem (ms)": resp_por_msg,
            }
        )

    metrics_df = pd.DataFrame(metrics_data)

    # --- Data for Radar Chart ---
    labels = [
        "Escalabilidade",
        "Speedup",
        "Eficiência Relativa",
        "Consistência (DPR)",
        "Overhead (ms/cli)",
        "Resp. por Mensagem (ms)",
    ]

    metrics_plot_df = metrics_df.copy()
    epsilon = 1e-9  # Evita divisão por zero

    # Inverte as métricas onde "menor é melhor" para que "maior seja melhor"
    for col in ["Consistência (DPR)", "Overhead (ms/cli)", "Resp. por Mensagem (ms)"]:
        metrics_plot_df[col] = 1 / (metrics_plot_df[col] + epsilon)

    # Normaliza os dados para o radar (0 a 1)
    for col in labels:
        # Handle cases where a column might be all zero or NaN
        if col in metrics_plot_df:
            max_val = metrics_plot_df[col].max()
            if pd.notna(max_val) and max_val > 0:
                # Normaliza para que o melhor valor seja 1 e o outro seja proporcional
                metrics_plot_df[col] = metrics_plot_df[col] / max_val
            else:
                metrics_plot_df[col] = 0  # Set to 0 if max is 0 or NaN

            # Garante que nenhum valor seja exatamente zero para ser visível no gráfico polar
            metrics_plot_df[col] = metrics_plot_df[col].clip(lower=0.05)
        else:
            metrics_plot_df[col] = 0.05

    stats_go = metrics_plot_df[metrics_plot_df["Implementação"] == "Go"].iloc[0]
    stats_py = metrics_plot_df[metrics_plot_df["Implementação"] == "Python"].iloc[0]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats_go = np.concatenate((stats_go[labels], [stats_go[labels[0]]]))
    stats_py = np.concatenate((stats_py[labels], [stats_py[labels[0]]]))
    angles += angles[:1]

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(14, 8), subplot_kw=dict(polar=True))

    # Plot Go
    ax.plot(
        angles, stats_go, color="dodgerblue", linewidth=2, linestyle="solid", label="Go"
    )
    ax.fill(angles, stats_go, color="dodgerblue", alpha=0.25)

    # Plot Python
    ax.plot(
        angles,
        stats_py,
        color="darkorange",
        linewidth=2,
        linestyle="solid",
        label="Python",
    )
    ax.fill(angles, stats_py, color="darkorange", alpha=0.25)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=12)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    plt.title("Radar de Métricas Avançadas de Desempenho", size=16, y=1.1)

    plt.tight_layout()
    output_path_radar = f"{RESULTS_DIR}/perfil_avancado_radar.png"
    plt.savefig(output_path_radar, bbox_inches="tight")
    plt.close(fig)  # Fecha a figura do radar
    print(f"Gráfico de radar salvo em: {output_path_radar}")

    # --- Geração da Tabela como Imagem Separada ---
    summary_df = metrics_df.set_index("Implementação").T
    summary_df["Melhor"] = summary_df.apply(
        lambda row: (
            "Go"
            if (
                row["Go"] > row["Python"]
                and row.name
                not in [
                    "Consistência (DPR)",
                    "Overhead (ms/cli)",
                    "Resp. por Mensagem (ms)",
                ]
            )
            or (
                row["Go"] < row["Python"]
                and row.name
                in [
                    "Consistência (DPR)",
                    "Overhead (ms/cli)",
                    "Resp. por Mensagem (ms)",
                ]
            )
            else "Python"
        ),
        axis=1,
    )
    summary_df = summary_df.round(4)

    fig_table, ax_table = plt.subplots(figsize=(8, 4))  # Tamanho ajustado para a tabela
    ax_table.axis("tight")
    ax_table.axis("off")
    table = ax_table.table(
        cellText=summary_df.values,
        rowLabels=summary_df.index,
        colLabels=summary_df.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)

    plt.title("Tabela de Métricas de Desempenho", size=16, y=0.85)
    output_path_table = f"{RESULTS_DIR}/metricas_avancadas_tabela.png"
    plt.savefig(output_path_table, bbox_inches="tight", dpi=200)
    plt.close(fig_table)  # Fecha a figura da tabela
    print(f"Tabela de métricas salva em: {output_path_table}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analyze.py <arquivo.csv> | compare")
        sys.exit(1)

    command = sys.argv[1]

    if command == "compare":
        analyze_file("requests_python.csv", "python")
        analyze_file("requests_go.csv", "go")
        compare_results("requests_python.csv", "requests_go.csv")
        try:
            # Read the cleaned and aggregated stats, not the raw files
            df_py = pd.read_csv("requests_python.csv")
            df_go = pd.read_csv("requests_go.csv")
            generate_advanced_report(df_py, df_go)
        except FileNotFoundError as e:
            print(
                f"Erro ao gerar relatório avançado: Arquivo não encontrado - {e.filename}"
            )
        except Exception as e:
            print(f"Um erro inesperado ocorreu ao gerar o relatório avançado: {e}")
    elif command == "python" or command == "go":
        analyze_file(f"requests_{command}.csv", command)
    else:
        print("Comando inválido. Use 'python', 'go' ou 'compare'.")
        sys.exit(1)
