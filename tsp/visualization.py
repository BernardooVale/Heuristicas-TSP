"""
Funções utilitárias para geração de gráficos, boxplots, heatmaps e fronteira de Pareto.
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns


def plot_box_candle_with_mean(df: pd.DataFrame, metric: str, ylabel: str, title: str, output_path: str):
    """Gera gráfico boxplot comparativo incluindo marcadores com a média."""
    plt.figure(figsize=(12, 6))

    heuristics = df["heuristic"].unique()
    data = [df[df["heuristic"] == h][metric].values for h in heuristics]
    means = [np.mean(vals) for vals in data]

    # Boxplot (Caixa com Q1, Mediana, Q3, Whiskers com Min e Max)
    plt.boxplot(data, tick_labels=heuristics, patch_artist=True,
                showmeans=False,
                whis=[0, 100],
                boxprops=dict(facecolor="#D1E8E2", color="#116466", linewidth=1.5),
                whiskerprops=dict(color="#116466", linewidth=1.5, linestyle="--"),
                capprops=dict(color="#116466", linewidth=2),
                medianprops=dict(color="#D9B08C", linewidth=2.5))

    # Sobreposição do Caso Médio
    x_coords = list(range(1, len(heuristics) + 1))
    plt.plot(x_coords, means, color="#FF6F59", marker="D", markersize=9, linewidth=2,
             linestyle="-", label="Caso Médio (Média Aritmética)", zorder=6)

    for x, m in zip(x_coords, means):
        if metric == "time_ms":
            txt = f"{m:.2f} ms"
        elif metric == "relative_cost":
            txt = f"{m:.2f}x"
        else:
            txt = f"{m:,.0f}"
        plt.annotate(txt, (x, m), textcoords="offset points", xytext=(0, 10),
                     ha="center", fontsize=9, fontweight="bold", color="#FF6F59")

    plt.title(title, fontsize=13, fontweight="bold")
    plt.xlabel("Heurística", fontsize=11, fontweight="bold")
    plt.ylabel(ylabel, fontsize=11, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", frameon=True)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_pareto_front(df_summary: pd.DataFrame, output_path: str):
    """Gera gráfico da Fronteira de Pareto entre Custo Relativo e Tempo de Execução."""
    plt.figure(figsize=(10, 7))

    x = df_summary["mean_relative_cost"].values
    y = df_summary["mean_time_ms"].values
    labels = df_summary["heuristic"].values

    # Identifica pontos de Pareto (min x, min y)
    pareto_mask = []
    for i in range(len(df_summary)):
        is_dominated = False
        for j in range(len(df_summary)):
            if i != j:
                if (x[j] <= x[i] and y[j] <= y[i]) and (x[j] < x[i] or y[j] < y[i]):
                    is_dominated = True
                    break
        pareto_mask.append(not is_dominated)

    colors = ["#E63946" if is_p else "#457B9D" for is_p in pareto_mask]
    plt.scatter(x, y, c=colors, s=160, edgecolors="black", linewidth=1.5, zorder=5)

    pareto_pts = sorted([(x[i], y[i], labels[i]) for i in range(len(x)) if pareto_mask[i]], key=lambda pt: pt[0])
    if len(pareto_pts) > 1:
        px = [p[0] for p in pareto_pts]
        py = [p[1] for p in pareto_pts]
        plt.plot(px, py, color="#E63946", linestyle="--", linewidth=2, label="Fronteira de Pareto (Não Dominadas)")

    for xi, yi, lab, is_p in zip(x, y, labels, pareto_mask):
        weight = "bold" if is_p else "normal"
        color = "#990000" if is_p else "#1D3557"
        plt.annotate(f" {lab}", (xi, yi), textcoords="offset points", xytext=(6, 4),
                     fontsize=10, fontweight=weight, color=color)

    plt.title("Análise Multiobjetivo: Qualidade da Rota vs Tempo de Execução", fontsize=13, fontweight="bold")
    plt.xlabel("Custo Médio Relativo (Normalizado pela melhor heurística da instância)", fontsize=11, fontweight="bold")
    plt.ylabel("Tempo Médio de Execução (ms)", fontsize=11, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left")
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_heatmaps(df: pd.DataFrame, output_dir: str = "graficos"):
    """Gera heatmaps comparativos de custo relativo e tempo de execução."""
    os.makedirs(output_dir, exist_ok=True)

    dims = df.drop_duplicates(subset=["instance"]).set_index("instance")["dimension"]

    # 1. Pivot table de custo relativo
    pivot_rel = df.pivot(index="instance", columns="heuristic", values="relative_cost")
    pivot_rel["dim"] = dims
    pivot_rel = pivot_rel.sort_values(by="dim").drop(columns=["dim"])

    plt.figure(figsize=(12, 10))
    sns.heatmap(pivot_rel, annot=True, fmt=".3f", cmap="YlGnBu",
                cbar_kws={'label': 'Custo Relativo (1.000 = Melhor Heurística)'}, linewidths=0.5)
    plt.title("Heatmap Comparativo de Qualidade da Solução\n(Custo Normalizado por Instância)", fontsize=13, fontweight='bold')
    plt.xlabel("Heurística", fontsize=11, fontweight='bold')
    plt.ylabel("Instância TSP (Ordenada por nº de vértices)", fontsize=11, fontweight='bold')
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "heatmap_custo_relativo.png"), dpi=300)
    plt.close()

    # 2. Pivot table de tempo (ms)
    pivot_time = df.pivot(index="instance", columns="heuristic", values="time_ms")
    pivot_time["dim"] = dims
    pivot_time = pivot_time.sort_values(by="dim").drop(columns=["dim"])

    plt.figure(figsize=(12, 10))
    sns.heatmap(pivot_time, annot=True, fmt=".2f", cmap="Oranges",
                cbar_kws={'label': 'Tempo de Execução (ms)'}, linewidths=0.5)
    plt.title("Heatmap Comparativo de Tempo Computacional (ms)", fontsize=13, fontweight='bold')
    plt.xlabel("Heurística", fontsize=11, fontweight='bold')
    plt.ylabel("Instância TSP (Ordenada por nº de vértices)", fontsize=11, fontweight='bold')
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "heatmap_tempo_execucao.png"), dpi=300)
    plt.close()
