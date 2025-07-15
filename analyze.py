# Análise 3D Interativa de Performance - Cliente-Servidor
import pandas as pd
import numpy as np
import os
import shutil
import sys
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.offline import plot
from scipy.interpolate import griddata


def generate_performance_analysis_3d(file_py, file_go):
    """
    Gera análise 3D de performance com gráficos focados nos tipos de dados.
    Elimina duplicações e usa nomes descritivos baseados no conteúdo.
    """
    print("--- Gerando Análise 3D de Performance ---")

    # Carregar dados
    try:
        df_py = pd.read_csv(file_py)
        df_go = pd.read_csv(file_go)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado: {e.filename}")
        return

    # Preparar dados
    df_py["implementation"] = "Python"
    df_go["implementation"] = "Go"
    df_combined = pd.concat([df_py, df_go], ignore_index=True)

    # Renomear colunas para padronização
    df_combined.rename(
        columns={
            "num_servers": "servers",
            "num_clients": "clients",
            "num_messages": "messages",
        },
        inplace=True,
    )

    # Limpeza de dados
    df_combined["response_time"] = pd.to_numeric(
        df_combined["response_time"], errors="coerce"
    )
    df_combined.dropna(subset=["response_time"], inplace=True)

    # Remover outliers (Z-score > 3)
    grouped = df_combined.groupby(["servers", "clients", "messages", "implementation"])
    df_combined["z_score"] = grouped["response_time"].transform(
        lambda x: np.abs((x - x.mean()) / x.std()) if x.std() > 0 else 0
    )
    df_cleaned = df_combined[df_combined["z_score"] <= 3]

    # Calcular estatísticas agregadas
    stats = (
        df_cleaned.groupby(["servers", "clients", "messages", "implementation"])[
            "response_time"
        ]
        .agg(["mean", "std"])
        .reset_index()
    )

    # Criar diretório de resultados
    RESULTS_DIR = "analysis_results_interactive"
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
    os.makedirs(RESULTS_DIR)

    # 1. Gráficos por número de mensagens (clientes vs servidores)
    unique_messages = sorted(stats["messages"].unique())

    for msg_count in unique_messages:
        msg_data = stats[stats["messages"] == msg_count]

        # Criar figura única com superfícies sobrepostas
        fig = go.Figure()

        # Python data
        py_data = msg_data[msg_data["implementation"] == "Python"]
        if not py_data.empty:
            _add_overlapped_surface_plotly(fig, py_data, "Python", "Blues", 0.7)

        # Go data
        go_data = msg_data[msg_data["implementation"] == "Go"]
        if not go_data.empty:
            _add_overlapped_surface_plotly(fig, go_data, "Go", "Reds", 0.7)

        # Layout
        fig.update_layout(
            title=f"Performance por Carga de Mensagens - {msg_count} Mensagem(s)<br><sub>Clientes vs Servidores | Azul=Python, Vermelho=Go</sub>",
            scene=dict(
                xaxis_title="Número de Clientes",
                yaxis_title="Número de Servidores",
                zaxis_title="Tempo Médio (s)",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            ),
            width=900,
            height=700,
        )

        # Salvar arquivo HTML com nome descritivo
        filename = f"{RESULTS_DIR}/clientes_vs_servidores_{msg_count}msgs.html"
        plot(fig, filename=filename, auto_open=False)
        print(f"✓ Gráfico clientes vs servidores ({msg_count} msgs): {filename}")

    # 2. Gráfico de escalabilidade: clientes vs mensagens
    scalability_stats = (
        stats.groupby(["clients", "messages", "implementation"])["mean"]
        .mean()
        .reset_index()
    )

    fig = go.Figure()

    # Python data
    py_scalability = scalability_stats[scalability_stats["implementation"] == "Python"]
    if not py_scalability.empty:
        _add_overlapped_surface_messages_plotly(fig, py_scalability, "Python", "Blues", 0.7)

    # Go data
    go_scalability = scalability_stats[scalability_stats["implementation"] == "Go"]
    if not go_scalability.empty:
        _add_overlapped_surface_messages_plotly(fig, go_scalability, "Go", "Reds", 0.7)

    fig.update_layout(
        title="Análise de Escalabilidade - Clientes vs Mensagens<br><sub>Como o desempenho varia com carga de trabalho | Azul=Python, Vermelho=Go</sub>",
        scene=dict(
            xaxis_title="Número de Clientes",
            yaxis_title="Número de Mensagens",
            zaxis_title="Tempo Médio (s)",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        ),
        width=900,
        height=700,
    )

    filename = f"{RESULTS_DIR}/escalabilidade_clientes_vs_mensagens.html"
    plot(fig, filename=filename, auto_open=False)
    print(f"✓ Análise de escalabilidade: {filename}")

    # 3. Gráfico de diferença de performance (apenas este)
    _create_performance_difference_chart(stats, RESULTS_DIR)

    print(f"\n🎯 Análise 3D de performance salva em: {RESULTS_DIR}/")
    print("\n� Gráficos gerados:")
    print("   • clientes_vs_servidores_Xmsgs.html - Performance por carga de mensagens")
    print("   • escalabilidade_clientes_vs_mensagens.html - Análise de escalabilidade")
    print("   • diferenca_performance_go_vs_python.html - Apenas diferença de performance")
    print("\n📋 Para visualizar:")
    print("1. Abra o gerenciador de arquivos")
    print(f"2. Navegue até: {os.path.abspath(RESULTS_DIR)}")
    print("3. Clique duplo em qualquer arquivo .html")

    print("\n🖱️  Controles do gráfico:")
    print("   • Arrastar: Rotacionar")
    print("   • Scroll: Zoom")
    print("   • Shift+Arrastar: Pan")
    print("   • Hover: Ver valores")


def _add_overlapped_surface_plotly(fig, data, name, colorscale, opacity):
    """Adiciona superfície 3D sobreposta para clientes vs servidores"""
    if data.empty:
        return

    x = data["clients"].values
    y = data["servers"].values
    z = data["mean"].values

    # Criar grid para interpolação
    if len(x) > 3:
        clients_range = np.linspace(x.min(), x.max(), 15)
        servers_range = np.linspace(y.min(), y.max(), 10)
        X, Y = np.meshgrid(clients_range, servers_range)

        Z = griddata((x, y), z, (X, Y), method="linear", fill_value=np.nan)

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                colorscale=colorscale,
                name=name,
                opacity=opacity,
                showscale=False,
            )
        )

    # Pontos de dados reais
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(size=6, opacity=0.9),
            name=f"{name} (Dados)",
            text=[
                f"{name}<br>Clientes: {c}<br>Servidores: {s}<br>Tempo: {t:.4f}s"
                for c, s, t in zip(x, y, z)
            ],
            hovertemplate="%{text}<extra></extra>",
        )
    )


def _add_overlapped_surface_messages_plotly(fig, data, name, colorscale, opacity):
    """Adiciona superfície 3D sobreposta para clientes vs mensagens"""
    if data.empty:
        return

    x = data["clients"].values
    y = data["messages"].values
    z = data["mean"].values

    # Criar grid para interpolação
    if len(x) > 3:
        clients_range = np.linspace(x.min(), x.max(), 15)
        messages_range = np.linspace(y.min(), y.max(), 10)
        X, Y = np.meshgrid(clients_range, messages_range)

        Z = griddata((x, y), z, (X, Y), method="linear", fill_value=np.nan)

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                colorscale=colorscale,
                name=name,
                opacity=opacity,
                showscale=False,
            )
        )

    # Pontos de dados reais
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(size=6, opacity=0.9),
            name=f"{name} (Dados)",
            text=[
                f"{name}<br>Clientes: {c}<br>Mensagens: {m}<br>Tempo: {t:.4f}s"
                for c, m, t in zip(x, y, z)
            ],
            hovertemplate="%{text}<extra></extra>",
        )
    )


def _create_performance_difference_chart(stats, results_dir):
    """Cria gráfico 3D focado APENAS na diferença de performance entre Python e Go"""
    print("Criando gráfico de diferença de performance...")

    # Dados agregados para comparação
    comparison_data = (
        stats.groupby(["clients", "servers", "implementation"])["mean"]
        .mean()
        .reset_index()
    )

    py_data = comparison_data[comparison_data["implementation"] == "Python"]
    go_data = comparison_data[comparison_data["implementation"] == "Go"]

    # Criar figura única focada APENAS na diferença
    fig = go.Figure()

    # Diferença de performance (Go - Python)
    if not py_data.empty and not go_data.empty:
        merged = pd.merge(
            py_data, go_data, on=["clients", "servers"], suffixes=("_py", "_go")
        )
        if not merged.empty:
            diff = merged["mean_go"] - merged["mean_py"]

            # Adicionar APENAS pontos de diferença
            fig.add_trace(
                go.Scatter3d(
                    x=merged["clients"],
                    y=merged["servers"],
                    z=diff,
                    mode="markers",
                    marker=dict(
                        size=10,
                        color=diff,
                        colorscale="RdBu_r",  # Vermelho = Go mais lento, Azul = Go mais rápido
                        opacity=0.8,
                        showscale=True,
                        colorbar=dict(
                            title="Diferença (s)<br>Vermelho: Go mais lento<br>Azul: Go mais rápido",
                        ),
                        cmin=diff.min(),
                        cmax=diff.max(),
                    ),
                    name="Diferença de Performance",
                    text=[
                        f"<b>Diferença: {d:.4f}s</b><br>"
                        f"Clientes: {c}<br>"
                        f"Servidores: {s}<br>"
                        f"Python: {py:.4f}s<br>"
                        f"Go: {go:.4f}s<br>"
                        f"<span style='color:{'blue' if d < 0 else 'red'}'>Go é {'mais rápido' if d < 0 else 'mais lento'}</span>"
                        for c, s, d, py, go in zip(
                            merged["clients"],
                            merged["servers"],
                            diff,
                            merged["mean_py"],
                            merged["mean_go"],
                        )
                    ],
                    hovertemplate="%{text}<extra></extra>",
                )
            )

            # Adicionar superfície de diferença se temos dados suficientes
            if len(merged) > 5:
                clients_range = np.linspace(
                    merged["clients"].min(), merged["clients"].max(), 15
                )
                servers_range = np.linspace(
                    merged["servers"].min(), merged["servers"].max(), 10
                )
                clients_grid, servers_grid = np.meshgrid(clients_range, servers_range)

                # Interpolar diferenças
                diff_surface = griddata(
                    (merged["clients"], merged["servers"]),
                    diff,
                    (clients_grid, servers_grid),
                    method="linear",
                    fill_value=np.nan,
                )

                # Adicionar superfície de diferença
                fig.add_trace(
                    go.Surface(
                        x=clients_grid,
                        y=servers_grid,
                        z=diff_surface,
                        colorscale="RdBu_r",
                        name="Superfície de Diferença",
                        opacity=0.6,
                        showscale=False,
                    )
                )

    # Layout otimizado para diferença de performance
    fig.update_layout(
        title="Diferença de Performance: Go vs Python<br><sub>Valores negativos = Go mais rápido | Valores positivos = Go mais lento</sub>",
        scene=dict(
            xaxis_title="Número de Clientes",
            yaxis_title="Número de Servidores",
            zaxis_title="Diferença de Tempo (s)<br>Go - Python",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            bgcolor="rgba(240,240,240,0.8)",
        ),
        width=1000,
        height=700,
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    filename = f"{results_dir}/diferenca_performance_go_vs_python.html"
    plot(fig, filename=filename, auto_open=False)
    print(f"✓ Gráfico de diferença de performance: {filename}")


def generate_server_load_analysis(file_py, file_go):
    """
    Gera análise específica de carga por servidor.
    Foca na relação clientes vs servidores para análise de infraestrutura.
    """
    print("--- Gerando Análise de Carga por Servidor ---")

    # Carregar dados
    try:
        df_py = pd.read_csv(file_py)
        df_go = pd.read_csv(file_go)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado: {e.filename}")
        return

    # Preparar dados
    df_py["implementation"] = "Python"
    df_go["implementation"] = "Go"
    df_combined = pd.concat([df_py, df_go], ignore_index=True)

    # Renomear colunas
    df_combined.rename(
        columns={
            "num_servers": "servers",
            "num_clients": "clients", 
            "num_messages": "messages",
        },
        inplace=True,
    )

    # Limpeza de dados
    df_combined["response_time"] = pd.to_numeric(
        df_combined["response_time"], errors="coerce"
    )
    df_combined.dropna(subset=["response_time"], inplace=True)

    # Remover outliers
    grouped = df_combined.groupby(["servers", "clients", "messages", "implementation"])
    df_combined["z_score"] = grouped["response_time"].transform(
        lambda x: np.abs((x - x.mean()) / x.std()) if x.std() > 0 else 0
    )
    df_cleaned = df_combined[df_combined["z_score"] <= 3]

    # Calcular estatísticas agregadas
    stats = (
        df_cleaned.groupby(["servers", "clients", "messages", "implementation"])[
            "response_time"
        ]
        .agg(["mean", "std"])
        .reset_index()
    )

    RESULTS_DIR = "analysis_results_interactive"
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # Análise geral de infraestrutura: clientes vs servidores
    infrastructure_stats = (
        stats.groupby(["clients", "servers", "implementation"])["mean"]
        .mean()
        .reset_index()
    )

    fig = go.Figure()

    py_infra = infrastructure_stats[infrastructure_stats["implementation"] == "Python"]
    go_infra = infrastructure_stats[infrastructure_stats["implementation"] == "Go"]

    if not py_infra.empty:
        _add_overlapped_surface(fig, py_infra, "Python", "Blues", 0.6)

    if not go_infra.empty:
        _add_overlapped_surface(fig, go_infra, "Go", "Reds", 0.6)

    fig.update_layout(
        title="Análise de Infraestrutura - Clientes vs Servidores<br><sub>Otimização de recursos | Azul=Python, Vermelho=Go</sub>",
        scene=dict(
            xaxis_title="Número de Clientes",
            yaxis_title="Número de Servidores", 
            zaxis_title="Tempo Médio (s)",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        ),
        width=1000,
        height=700,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    filename = f"{RESULTS_DIR}/infraestrutura_clientes_vs_servidores.html"
    plot(fig, filename=filename, auto_open=False)
    print(f"✓ Análise de infraestrutura: {filename}")

    print(f"\n🎯 Análise de carga por servidor salva em: {RESULTS_DIR}/")
    print("🔍 Este gráfico mostra:")
    print("   • Como a performance varia com número de servidores")
    print("   • Otimização de recursos de infraestrutura")
    print("   • Ponto ideal de servidores vs clientes")



def generate_overlapped_comparison(file_py, file_go):
    """
    Gera gráficos 3D com superfícies sobrepostas de Python e Go
    para comparação direta no mesmo espaço.
    """
    print("--- Gerando Gráficos 3D Sobrepostos Python vs Go ---")

    # Carregar dados
    try:
        df_py = pd.read_csv(file_py)
        df_go = pd.read_csv(file_go)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado: {e.filename}")
        return

    # Preparar dados
    df_py["implementation"] = "Python"
    df_go["implementation"] = "Go"
    df_combined = pd.concat([df_py, df_go], ignore_index=True)

    # Renomear colunas
    df_combined.rename(
        columns={
            "num_servers": "servers",
            "num_clients": "clients",
            "num_messages": "messages",
        },
        inplace=True,
    )

    # Limpeza de dados
    df_combined["response_time"] = pd.to_numeric(
        df_combined["response_time"], errors="coerce"
    )
    df_combined.dropna(subset=["response_time"], inplace=True)

    # Remover outliers
    grouped = df_combined.groupby(["servers", "clients", "messages", "implementation"])
    df_combined["z_score"] = grouped["response_time"].transform(
        lambda x: np.abs((x - x.mean()) / x.std()) if x.std() > 0 else 0
    )
    df_cleaned = df_combined[df_combined["z_score"] <= 3]

    # Calcular estatísticas agregadas
    stats = (
        df_cleaned.groupby(["servers", "clients", "messages", "implementation"])[
            "response_time"
        ]
        .agg(["mean", "std"])
        .reset_index()
    )

    RESULTS_DIR = "analysis_results_interactive"
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # 1. Gráficos sobrepostos por número de mensagens
    unique_messages = sorted(stats["messages"].unique())

    for msg_count in unique_messages:
        msg_data = stats[stats["messages"] == msg_count]

        fig = go.Figure()

        # Dados Python e Go
        py_data = msg_data[msg_data["implementation"] == "Python"]
        go_data = msg_data[msg_data["implementation"] == "Go"]

        # Adicionar superfícies sobrepostas
        if not py_data.empty:
            _add_overlapped_surface(fig, py_data, "Python", "Blues", 0.6)

        if not go_data.empty:
            _add_overlapped_surface(fig, go_data, "Go", "Reds", 0.6)

        # Layout
        fig.update_layout(
            title=f"Comparação Sobreposta 3D - {msg_count} Mensagem(s)<br><sub>Azul = Python | Vermelho = Go | Superfícies mais baixas = melhor performance</sub>",
            scene=dict(
                xaxis_title="Número de Clientes",
                yaxis_title="Número de Servidores",
                zaxis_title="Tempo Médio (s)",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            ),
            width=1000,
            height=700,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        filename = f"{RESULTS_DIR}/overlapped_3d_messages_{msg_count}.html"
        plot(fig, filename=filename, auto_open=False)
        print(f"✓ Gráfico sobreposto salvo: overlapped_3d_messages_{msg_count}.html")

    # 2. Gráfico sobreposto final: clientes vs mensagens
    final_stats = (
        stats.groupby(["clients", "messages", "implementation"])["mean"]
        .mean()
        .reset_index()
    )

    fig = go.Figure()

    py_final = final_stats[final_stats["implementation"] == "Python"]
    go_final = final_stats[final_stats["implementation"] == "Go"]

    if not py_final.empty:
        _add_overlapped_surface_messages(fig, py_final, "Python", "Blues", 0.6)

    if not go_final.empty:
        _add_overlapped_surface_messages(fig, go_final, "Go", "Reds", 0.6)

    fig.update_layout(
        title="Comparação Sobreposta 3D - Clientes vs Mensagens<br><sub>Azul = Python | Vermelho = Go | Superfícies mais baixas = melhor performance</sub>",
        scene=dict(
            xaxis_title="Número de Clientes",
            yaxis_title="Número de Mensagens",
            zaxis_title="Tempo Médio (s)",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        ),
        width=1000,
        height=700,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    filename = f"{RESULTS_DIR}/overlapped_3d_final.html"
    plot(fig, filename=filename, auto_open=False)
    print(f"✓ Gráfico sobreposto final salvo: overlapped_3d_final.html")

    # 3. Gráfico comparativo geral sobreposto
    comparison_data = (
        stats.groupby(["clients", "servers", "implementation"])["mean"]
        .mean()
        .reset_index()
    )

    fig = go.Figure()

    py_comp = comparison_data[comparison_data["implementation"] == "Python"]
    go_comp = comparison_data[comparison_data["implementation"] == "Go"]

    if not py_comp.empty:
        _add_overlapped_surface(fig, py_comp, "Python", "Blues", 0.6)

    if not go_comp.empty:
        _add_overlapped_surface(fig, go_comp, "Go", "Reds", 0.6)

    fig.update_layout(
        title="Comparação Sobreposta Geral - Clientes vs Servidores<br><sub>Azul = Python | Vermelho = Go | Superfícies mais baixas = melhor performance</sub>",
        scene=dict(
            xaxis_title="Número de Clientes",
            yaxis_title="Número de Servidores",
            zaxis_title="Tempo Médio (s)",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        ),
        width=1000,
        height=700,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    filename = f"{RESULTS_DIR}/overlapped_3d_general.html"
    plot(fig, filename=filename, auto_open=False)
    print(f"✓ Gráfico sobreposto geral salvo: overlapped_3d_general.html")

    print(f"\n🎯 Gráficos sobrepostos salvos em: {RESULTS_DIR}/")
    print("🔍 Nos gráficos sobrepostos, você pode:")
    print("   • Ver diretamente qual implementação é mais rápida")
    print("   • A superfície mais baixa representa melhor performance")
    print("   • Azul = Python, Vermelho = Go")


def _add_overlapped_surface(fig, data, name, colorscale, opacity):
    """Adiciona superfície 3D sobreposta para clientes vs servidores"""
    if data.empty:
        return

    x = data["clients"].values
    y = data["servers"].values
    z = data["mean"].values

    # Criar grid para interpolação
    if len(x) > 3:
        clients_range = np.linspace(x.min(), x.max(), 25)
        servers_range = np.linspace(y.min(), y.max(), 25)
        X, Y = np.meshgrid(clients_range, servers_range)

        # Interpolar dados
        Z = griddata((x, y), z, (X, Y), method="linear", fill_value=np.nan)

        # Adicionar superfície
        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                colorscale=colorscale,
                name=name,
                opacity=opacity,
                showscale=True,
                colorbar=dict(
                    title=f"{name}<br>Tempo (s)", x=0.9 if name == "Go" else 0.02
                ),
            )
        )

    # Adicionar pontos de dados reais
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=6, opacity=0.9, color="darkblue" if name == "Python" else "darkred"
            ),
            name=f"{name} (Dados)",
            text=[
                f"{name}<br>Clientes: {c}<br>Servidores: {s}<br>Tempo: {t:.4f}s"
                for c, s, t in zip(x, y, z)
            ],
            hovertemplate="%{text}<extra></extra>",
        )
    )


def _add_overlapped_surface_messages(fig, data, name, colorscale, opacity):
    """Adiciona superfície 3D sobreposta para clientes vs mensagens"""
    if data.empty:
        return

    x = data["clients"].values
    y = data["messages"].values
    z = data["mean"].values

    # Criar grid para interpolação
    if len(x) > 3:
        clients_range = np.linspace(x.min(), x.max(), 25)
        messages_range = np.linspace(y.min(), y.max(), 25)
        X, Y = np.meshgrid(clients_range, messages_range)

        Z = griddata((x, y), z, (X, Y), method="linear", fill_value=np.nan)

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                colorscale=colorscale,
                name=name,
                opacity=opacity,
                showscale=True,
                colorbar=dict(
                    title=f"{name}<br>Tempo (s)", x=0.9 if name == "Go" else 0.02
                ),
            )
        )

    # Pontos de dados reais
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=6, opacity=0.9, color="darkblue" if name == "Python" else "darkred"
            ),
            name=f"{name} (Dados)",
            text=[
                f"{name}<br>Clientes: {c}<br>Mensagens: {m}<br>Tempo: {t:.4f}s"
                for c, m, t in zip(x, y, z)
            ],
            hovertemplate="%{text}<extra></extra>",
        )
    )


if __name__ == "__main__":
    print("🚀 Gerando análise 3D de performance...")
    print("📊 Gráficos otimizados com nomes descritivos")
    print("")

    # Verificar se os arquivos existem
    files = ["requests_python.csv", "requests_go.csv"]
    for file in files:
        if not os.path.exists(file):
            print(f"❌ Erro: Arquivo {file} não encontrado!")
            print("Execute primeiro o deploy.sh para gerar os dados.")
            sys.exit(1)

    # Gerar análise completa de performance
    print("1️⃣ Gerando análise de performance por carga de mensagens...")
    generate_performance_analysis_3d("requests_python.csv", "requests_go.csv")

    print("\n2️⃣ Gerando análise de infraestrutura...")
    generate_server_load_analysis("requests_python.csv", "requests_go.csv")

    print("\n🎉 Análise 3D completa gerada com sucesso!")
    print("📁 Verifique a pasta: analysis_results_interactive/")
    print("\n📊 Gráficos gerados:")
    print("   🔹 clientes_vs_servidores_Xmsgs.html - Performance por carga de mensagens")
    print("   🔹 escalabilidade_clientes_vs_mensagens.html - Análise de escalabilidade")
    print("   🔹 diferenca_performance_go_vs_python.html - APENAS diferença de performance")
    print("   🔹 infraestrutura_clientes_vs_servidores.html - Otimização de infraestrutura")
    print("\n🌐 Abra qualquer arquivo .html no navegador para visualizar")
