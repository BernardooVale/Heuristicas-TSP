"""
Execução do benchmark comparativo entre Metaheurísticas e as Top-2 Heurísticas (H1 e H5).
Gera relatórios em CSV e gráficos sem sobrescrever os dados originais.
"""

import os
import glob
import time
import pandas as pd
from tsp.core import read_tsp_file
from tsp.metaheuristics import simulated_annealing, classical_2opt
from tsp.heuristics import heuristic_h5_farthest_insertion
from tsp.visualization import plot_box_candle_with_mean, plot_pareto_front, plot_heatmaps


def run_metaheuristics_comparison(base_dir: str = "."):
    # 1. Carrega métricas existentes das heurísticas
    orig_csv = os.path.join(base_dir, "resultados", "metricas_tsp.csv")
    if not os.path.exists(orig_csv):
        raise FileNotFoundError(f"Arquivo de métricas original não encontrado em: {orig_csv}")

    df_orig = pd.read_csv(orig_csv)

    # Filtra apenas as Top 2 heurísticas (H1 - Centroid-Based e H5 - Farthest Insertion)
    df_top2 = df_orig[df_orig["heuristic"].isin(["H1 (Centroid-Based)", "H5 (Farthest Insertion)"])].copy()

    # 2. Localiza instâncias TSP
    instances_paths = []
    instances_paths.extend(glob.glob(os.path.join(base_dir, "*.tsp")))
    instances_paths.extend(glob.glob(os.path.join(base_dir, "EUC_2D", "*.tsp")))
    instances_paths = sorted(list(set(instances_paths)))

    print(f"Total de instâncias para rodar metaheurísticas: {len(instances_paths)}")

    records = []

    for path in instances_paths:
        instance = read_tsp_file(path)
        print(f"Processando instância: {instance.name} (Vértices: {instance.dimension})")

        # Pré-computa rota inicial H5 para as abordagens warm-start
        h5_tour = heuristic_h5_farthest_insertion(instance)

        # Configuração das variantes a avaliar:
        # Hipótese A: Inicialização Aleatória (Random Start)
        # Hipótese B: Inicialização com Heurística (Warm Start / Low-temp Start conforme Johnson & McGeoch)
        experiments = [
            ("2-Opt (Random Start)", lambda inst: classical_2opt(inst, seed=42)),
            ("2-Opt (from H5)", lambda inst: classical_2opt(inst, initial_tour=h5_tour)),
            ("SA (Random Start)", lambda inst: simulated_annealing(inst, alpha=0.98, seed=42)),
            ("SA (from H5)", lambda inst: simulated_annealing(inst, initial_tour=h5_tour, initial_temp=50.0, alpha=0.95, seed=42)),
        ]

        for alg_name, alg_fn in experiments:
            start_time = time.perf_counter()
            tour = alg_fn(instance)
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

    df_meta = pd.DataFrame(records)

    # 3. Consolidação com as Top-2 Heurísticas
    df_combined = pd.concat([df_top2[["instance", "type", "dimension", "heuristic", "cost", "time_ms"]], df_meta], ignore_index=True)

    # Recalcula custo relativo baseado no melhor custo encontrado entre esses métodos
    best_per_inst = df_combined.groupby("instance")["cost"].transform("min")
    df_combined["relative_cost"] = df_combined["cost"] / best_per_inst

    # Salva CSVs específicos sem sobrescrever os originais
    res_dir = os.path.join(base_dir, "resultados")
    plots_dir = os.path.join(base_dir, "graficos", "metaheuristicas")
    os.makedirs(res_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    csv_combined_path = os.path.join(res_dir, "comparativo_metaheuristicas.csv")
    df_combined.to_csv(csv_combined_path, index=False)
    print(f"\n[OK] CSV comparativo salvo em: {csv_combined_path}")

    # Resumo estatístico
    df_summary = df_combined.groupby("heuristic").agg(
        mean_cost=("cost", "mean"),
        mean_relative_cost=("relative_cost", "mean"),
        mean_time_ms=("time_ms", "mean")
    ).reset_index()
    csv_summary_path = os.path.join(res_dir, "resumo_metaheuristicas.csv")
    df_summary.to_csv(csv_summary_path, index=False)
    print(f"[OK] CSV de resumo salvo em: {csv_summary_path}")

    # 4. Geração dos Gráficos Comparativos
    print("\nGerando gráficos comparativos...")

    # Boxplot Custo Relativo
    plot_box_candle_with_mean(
        df=df_combined,
        metric="relative_cost",
        ylabel="Custo Relativo (1.0 = Melhor da Instância)",
        title="Comparativo de Custo Relativo: Metaheurísticas vs Top-2 Heurísticas",
        output_path=os.path.join(plots_dir, "boxplot_custo_relativo_metaheuristicas.png")
    )

    # Boxplot Tempo de Execução
    plot_box_candle_with_mean(
        df=df_combined,
        metric="time_ms",
        ylabel="Tempo de Execução (ms)",
        title="Comparativo de Tempo: Metaheurísticas vs Top-2 Heurísticas",
        output_path=os.path.join(plots_dir, "boxplot_tempo_metaheuristicas.png")
    )

    # Fronteira de Pareto
    plot_pareto_front(
        df_summary=df_summary,
        output_path=os.path.join(plots_dir, "pareto_metaheuristicas.png")
    )

    # Heatmaps
    plot_heatmaps(
        df=df_combined,
        output_dir=plots_dir
    )

    print(f"\n[OK] Todos os gráficos salvos com sucesso na pasta: {plots_dir}")


if __name__ == "__main__":
    run_metaheuristics_comparison()
