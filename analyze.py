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


def generate_interactive_3d_plots(file_py, file_go):
    """
    Gera gráficos 3D verdadeiramente interativos usando Plotly.
    Os gráficos são salvos como arquivos HTML que abrem no navegador.
    """
    print("--- Gerando Gráficos 3D Interativos com Plotly ---")

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

    # 1. Gráficos por número de mensagens
    unique_messages = sorted(stats["messages"].unique())

    for msg_count in unique_messages:
        msg_data = stats[stats["messages"] == msg_count]

        # Criar subplot
        fig = sp.make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "surface"}, {"type": "surface"}]],
            subplot_titles=["Python", "Go"],
            horizontal_spacing=0.1,
        )

        # Python data
        py_data = msg_data[msg_data["implementation"] == "Python"]
        if not py_data.empty:
            _add_plotly_surface(fig, py_data, "Python", "blues", 1, 1)

        # Go data
        go_data = msg_data[msg_data["implementation"] == "Go"]
        if not go_data.empty:
            _add_plotly_surface(fig, go_data, "Go", "reds", 1, 2)

        # Layout
        fig.update_layout(
            title=f"Análise 3D Interativa - {msg_count} Mensagem(s)",
            scene=dict(
                xaxis_title="Número de Clientes",
                yaxis_title="Número de Servidores",
                zaxis_title="Tempo Médio (s)",
            ),
            scene2=dict(
                xaxis_title="Número de Clientes",
                yaxis_title="Número de Servidores",
                zaxis_title="Tempo Médio (s)",
            ),
            width=1200,
            height=600,
        )

        # Salvar arquivo HTML
        filename = f"{RESULTS_DIR}/interactive_3d_messages_{msg_count}.html"
        plot(fig, filename=filename, auto_open=False)
        print(f"✓ Gráfico 3D interativo salvo: {filename}")

    # 2. Gráfico final: clientes vs mensagens
    final_stats = (
        stats.groupby(["clients", "messages", "implementation"])["mean"]
        .mean()
        .reset_index()
    )

    fig = sp.make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "surface"}, {"type": "surface"}]],
        subplot_titles=["Python - Clientes vs Mensagens", "Go - Clientes vs Mensagens"],
        horizontal_spacing=0.1,
    )

    # Python data
    py_final = final_stats[final_stats["implementation"] == "Python"]
    if not py_final.empty:
        _add_plotly_surface_messages(fig, py_final, "Python", "blues", 1, 1)

    # Go data
    go_final = final_stats[final_stats["implementation"] == "Go"]
    if not go_final.empty:
        _add_plotly_surface_messages(fig, go_final, "Go", "reds", 1, 2)

    fig.update_layout(
        title="Análise 3D - Clientes vs Mensagens",
        scene=dict(
            xaxis_title="Número de Clientes",
            yaxis_title="Número de Mensagens",
            zaxis_title="Tempo Médio (s)",
        ),
        scene2=dict(
            xaxis_title="Número de Clientes",
            yaxis_title="Número de Mensagens",
            zaxis_title="Tempo Médio (s)",
        ),
        width=1200,
        height=600,
    )

    filename = f"{RESULTS_DIR}/interactive_3d_final.html"
    plot(fig, filename=filename, auto_open=False)
    print(f"✓ Gráfico 3D final interativo salvo: {filename}")

    # 3. Gráfico comparativo direto
    _create_comparison_3d_plotly(stats, RESULTS_DIR)

    print(f"\n🎯 Todos os gráficos 3D interativos salvos em: {RESULTS_DIR}/")
    print("\n📋 INSTRUÇÕES PARA VISUALIZAR:")
    print("1. Abra o gerenciador de arquivos")
    print(f"2. Navegue até: {os.path.abspath(RESULTS_DIR)}")
    print("3. Clique duplo em qualquer arquivo .html")
    print("4. Ou copie o caminho e cole no navegador:")

    for file in os.listdir(RESULTS_DIR):
        if file.endswith(".html"):
            full_path = os.path.abspath(os.path.join(RESULTS_DIR, file))
            print(f"   file://{full_path}")

    print("\n🖱️  Controles do gráfico:")
    print("   • Arrastar: Rotacionar")
    print("   • Scroll: Zoom")
    print("   • Shift+Arrastar: Pan")
    print("   • Hover: Ver valores")


def _add_plotly_surface(fig, data, name, colorscale, row, col):
    """Adiciona superfície 3D ao subplot"""
    if data.empty:
        return

    x = data["clients"].values
    y = data["servers"].values
    z = data["mean"].values

    # Criar grid para interpolação
    if len(x) > 3:
        clients_range = np.linspace(x.min(), x.max(), 20)
        servers_range = np.linspace(y.min(), y.max(), 20)
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
                opacity=0.8,
                showscale=True,
            ),
            row=row,
            col=col,
        )

    # Adicionar pontos de dados reais
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(size=8, opacity=0.9),
            name=f"{name} (Dados Reais)",
            text=[
                f"Clientes: {c}<br>Servidores: {s}<br>Tempo: {t:.4f}s"
                for c, s, t in zip(x, y, z)
            ],
            hovertemplate="%{text}<extra></extra>",
        ),
        row=row,
        col=col,
    )


def _add_plotly_surface_messages(fig, data, name, colorscale, row, col):
    """Adiciona superfície 3D para clientes vs mensagens"""
    if data.empty:
        return

    x = data["clients"].values
    y = data["messages"].values
    z = data["mean"].values

    # Criar grid para interpolação
    if len(x) > 3:
        clients_range = np.linspace(x.min(), x.max(), 20)
        messages_range = np.linspace(y.min(), y.max(), 20)
        X, Y = np.meshgrid(clients_range, messages_range)

        Z = griddata((x, y), z, (X, Y), method="linear", fill_value=np.nan)

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                colorscale=colorscale,
                name=name,
                opacity=0.8,
                showscale=True,
            ),
            row=row,
            col=col,
        )

    # Pontos de dados reais
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(size=8, opacity=0.9),
            name=f"{name} (Dados Reais)",
            text=[
                f"Clientes: {c}<br>Mensagens: {m}<br>Tempo: {t:.4f}s"
                for c, m, t in zip(x, y, z)
            ],
            hovertemplate="%{text}<extra></extra>",
        ),
        row=row,
        col=col,
    )


def _create_comparison_3d_plotly(stats, results_dir):
    """Cria gráfico 3D comparativo usando Plotly"""
    print("Criando gráfico comparativo 3D...")

    # Dados agregados para comparação
    comparison_data = (
        stats.groupby(["clients", "servers", "implementation"])["mean"]
        .mean()
        .reset_index()
    )

    # Criar figura com 3 subplots
    fig = sp.make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "scatter3d"}, {"type": "scatter3d"}, {"type": "scatter3d"}]],
        subplot_titles=[
            "Comparação Direta",
            "Diferença de Performance",
            "Distribuição Geral",
        ],
        horizontal_spacing=0.05,
    )

    py_data = comparison_data[comparison_data["implementation"] == "Python"]
    go_data = comparison_data[comparison_data["implementation"] == "Go"]

    # Subplot 1: Comparação direta
    if not py_data.empty:
        fig.add_trace(
            go.Scatter3d(
                x=py_data["clients"],
                y=py_data["servers"],
                z=py_data["mean"],
                mode="markers",
                marker=dict(size=8, color="blue", opacity=0.8),
                name="Python",
                text=[
                    f"Python<br>Clientes: {c}<br>Servidores: {s}<br>Tempo: {t:.4f}s"
                    for c, s, t in zip(
                        py_data["clients"], py_data["servers"], py_data["mean"]
                    )
                ],
                hovertemplate="%{text}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    if not go_data.empty:
        fig.add_trace(
            go.Scatter3d(
                x=go_data["clients"],
                y=go_data["servers"],
                z=go_data["mean"],
                mode="markers",
                marker=dict(size=8, color="red", opacity=0.8),
                name="Go",
                text=[
                    f"Go<br>Clientes: {c}<br>Servidores: {s}<br>Tempo: {t:.4f}s"
                    for c, s, t in zip(
                        go_data["clients"], go_data["servers"], go_data["mean"]
                    )
                ],
                hovertemplate="%{text}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # Subplot 2: Diferença de performance
    if not py_data.empty and not go_data.empty:
        merged = pd.merge(
            py_data, go_data, on=["clients", "servers"], suffixes=("_py", "_go")
        )
        if not merged.empty:
            diff = merged["mean_go"] - merged["mean_py"]
            fig.add_trace(
                go.Scatter3d(
                    x=merged["clients"],
                    y=merged["servers"],
                    z=diff,
                    mode="markers",
                    marker=dict(
                        size=8,
                        color=diff,
                        colorscale="RdBu",
                        opacity=0.8,
                        showscale=True,
                        colorbar=dict(title="Diferença (s)"),
                    ),
                    name="Diferença (Go - Python)",
                    text=[
                        f"Diferença: {d:.4f}s<br>Clientes: {c}<br>Servidores: {s}"
                        for c, s, d in zip(merged["clients"], merged["servers"], diff)
                    ],
                    hovertemplate="%{text}<extra></extra>",
                ),
                row=1,
                col=2,
            )

    # Subplot 3: Distribuição geral
    all_data = comparison_data.copy()
    colors = [
        "blue" if impl == "Python" else "red" for impl in all_data["implementation"]
    ]

    fig.add_trace(
        go.Scatter3d(
            x=all_data["clients"],
            y=all_data["servers"],
            z=all_data["mean"],
            mode="markers",
            marker=dict(size=8, color=colors, opacity=0.8),
            name="Distribuição",
            text=[
                f"{impl}<br>Clientes: {c}<br>Servidores: {s}<br>Tempo: {t:.4f}s"
                for c, s, t, impl in zip(
                    all_data["clients"],
                    all_data["servers"],
                    all_data["mean"],
                    all_data["implementation"],
                )
            ],
            hovertemplate="%{text}<extra></extra>",
        ),
        row=1,
        col=3,
    )

    # Layout
    fig.update_layout(
        title="Comparação 3D Interativa: Python vs Go",
        scene=dict(
            xaxis_title="Clientes",
            yaxis_title="Servidores",
            zaxis_title="Tempo Médio (s)",
        ),
        scene2=dict(
            xaxis_title="Clientes",
            yaxis_title="Servidores",
            zaxis_title="Diferença (s)",
        ),
        scene3=dict(
            xaxis_title="Clientes",
            yaxis_title="Servidores",
            zaxis_title="Tempo Médio (s)",
        ),
        width=1800,
        height=600,
    )

    filename = f"{results_dir}/comparison_3d_interactive.html"
    plot(fig, filename=filename, auto_open=False)
    print(f"✓ Gráfico comparativo 3D interativo salvo: {filename}")


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
    if len(sys.argv) != 2:
        print("Uso: python analyze.py <comando>")
        print("Comandos disponíveis:")
        print("  interactive  - Gráficos 3D lado a lado")
        print("  overlapped   - Gráficos 3D sobrepostos (comparação direta)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "interactive":
        generate_interactive_3d_plots("requests_python.csv", "requests_go.csv")
    elif command == "overlapped":
        generate_overlapped_comparison("requests_python.csv", "requests_go.csv")
    else:
        print("Comando inválido. Use 'interactive' ou 'overlapped'.")
        sys.exit(1)
