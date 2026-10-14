"""
Módulo para avaliação experimental, benchmark e coleta de métricas.
"""

import os
import glob
import time
from typing import Dict, Callable, List, Optional, Tuple
import pandas as pd

from tsp.core import TSPInstance, read_tsp_file
from tsp.heuristics import HEURISTICS
from tsp.visualization import plot_box_candle_with_mean, plot_pareto_front, plot_heatmaps


def run_benchmark(
    base_dir: str = ".",
    algorithms: Optional[Dict[str, Callable[[TSPInstance], List[int]]]] = None,
    results_dir: str = "resultados",
    plots_dir: str = "graficos"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executa o benchmark de algoritmos sobre instâncias TSP encontradas no diretório.
    Gera relatórios em CSV e gráficos.
    """
    if algorithms is None:
        algorithms = HEURISTICS

    instances_paths = []
    instances_paths.extend(glob.glob(os.path.join(base_dir, "*.tsp")))
    instances_paths.extend(glob.glob(os.path.join(base_dir, "EUC_2D", "*.tsp")))
    instances_paths = sorted(list(set(instances_paths)))

    print(f"Total de instâncias TSP encontradas: {len(instances_paths)}")
    print(f"Total de algoritmos a avaliar: {len(algorithms)}\n")

    records = []

    for path in instances_paths:
        instance = read_tsp_file(path)
        print(f"--- Processando Instância: {instance.name} (Vértices: {instance.dimension}, Tipo: {instance.edge_weight_type}) ---")

        for alg_name, alg_func in algorithms.items():
            start_time = time.perf_counter()
            tour = alg_func(instance)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            cost = instance.calculate_tour_cost(tour)

            records.append({
                "instance": instance.name,
                "type": instance.edge_weight_type,
                "dimension": instance.dimension,
                "heuristic": alg_name,
                "cost": cost,
                "time_ms": elapsed_ms
            })
            print(f"  > {alg_name:<25} | Custo: {cost:<9} | Tempo: {elapsed_ms:.2f} ms")

    df = pd.DataFrame(records)

    # Custo relativo em relação à melhor solução encontrada para cada instância
    best_per_inst = df.groupby("instance")["cost"].transform("min")
    df["relative_cost"] = df["cost"] / best_per_inst

    # Salva dados coletados em CSV
    os.makedirs(results_dir, exist_ok=True)
    csv_metrics_path = os.path.join(results_dir, "metricas_tsp.csv")
    df.to_csv(csv_metrics_path, index=False)
    print(f"\nResultados numéricos salvos em '{csv_metrics_path}'.")

    # Resumo para análise multiobjetivo
    df_summary = df.groupby("heuristic").agg(
        mean_cost=("cost", "mean"),
        mean_relative_cost=("relative_cost", "mean"),
        mean_time_ms=("time_ms", "mean")
    ).reset_index()
    csv_summary_path = os.path.join(results_dir, "resumo_heurísticas.csv")
    df_summary.to_csv(csv_summary_path, index=False)

    # Geração dos Gráficos
    print("\nGerando gráficos...")
    os.makedirs(plots_dir, exist_ok=True)

    print(" - Gerando Heatmaps Comparativos...")
    plot_heatmaps(df, output_dir=plots_dir)

    print(" - Gerando Boxplot/Candle de Custo...")
    plot_box_candle_with_mean(
        df=df,
        metric="relative_cost",
        ylabel="Custo Relativo (1.0 = Melhor da Instância)",
        title="Distribuição do Custo Relativo por Heurística (Quartis, Min, Max e Caso Médio)",
        output_path=os.path.join(plots_dir, "boxplot_custo_relativo.png")
    )

    print(" - Gerando Boxplot/Candle de Tempo...")
    plot_box_candle_with_mean(
        df=df,
        metric="time_ms",
        ylabel="Tempo de Execução (ms)",
        title="Distribuição do Tempo de Execução por Heurística (Quartis, Min, Max e Caso Médio)",
        output_path=os.path.join(plots_dir, "boxplot_tempo_execucao.png")
    )

    print(" - Gerando Curva de Fronteira de Pareto...")
    plot_pareto_front(
        df_summary=df_summary,
        output_path=os.path.join(plots_dir, "fronteira_pareto.png")
    )

    # Limpeza de gráfico antigo se existir
    old_chart = os.path.join(plots_dir, "comparativo_custos.png")
    if os.path.exists(old_chart):
        try:
            os.remove(old_chart)
        except Exception:
            pass

    return df, df_summary
