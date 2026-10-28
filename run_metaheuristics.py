"""
Execução do benchmark comparativo entre Metaheurísticas e as Top-2 Heurísticas (H1 e H5).
Gera relatórios em CSV e gráficos sem sobrescrever os dados originais.
Funciona de forma independente, calculando H1 e H5 sob demanda caso 'metricas_tsp.csv' não exista.
"""

import os
import glob
import time
import pandas as pd
from tsp.core import read_tsp_file
from tsp.metaheuristics import simulated_annealing, classical_2opt
from tsp.heuristics import heuristic_h1_centroid, heuristic_h5_farthest_insertion
from tsp.visualization import plot_box_candle_with_mean, plot_pareto_front, plot_heatmaps


def run_metaheuristics_comparison(base_dir: str = "."):
    # 1. Localiza instâncias TSP
    instances_paths = []
    instances_paths.extend(glob.glob(os.path.join(base_dir, "*.tsp")))
    instances_paths.extend(glob.glob(os.path.join(base_dir, "EUC_2D", "*.tsp")))
    instances_paths = sorted(list(set(instances_paths)))

    if not instances_paths:
        raise FileNotFoundError("Nenhuma instância .tsp encontrada no diretório raiz ou em EUC_2D/")

    print(f"Total de instâncias para rodar metaheurísticas: {len(instances_paths)}")

    # 2. Carrega métricas existentes das heurísticas caso existam
    orig_csv = os.path.join(base_dir, "resultados", "metricas_tsp.csv")
    existing_top2 = {}
    if os.path.exists(orig_csv):
        print(f"[INFO] Arquivo '{orig_csv}' encontrado. Carregando dados de H1 e H5 já computados...")
        df_orig = pd.read_csv(orig_csv)
        df_top2 = df_orig[df_orig["heuristic"].isin(["H1 (Centroid-Based)", "H5 (Farthest Insertion)"])]
        for _, row in df_top2.iterrows():
            existing_top2[(row["instance"], row["heuristic"])] = {
                "cost": row["cost"],
                "time_ms": row["time_ms"]
            }
    else:
        print(f"[AVISO] Arquivo '{orig_csv}' não encontrado. As heurísticas H1 e H5 serão executadas diretamente.")

    records = []

    for path in instances_paths:
        instance = read_tsp_file(path)
        print(f"\nProcessando instância: {instance.name} (Vértices: {instance.dimension})")

        # Computa ou recupera H1 (Centroid-Based)
        if (instance.name, "H1 (Centroid-Based)") in existing_top2:
            h1_data = existing_top2[(instance.name, "H1 (Centroid-Based)")]
            h1_cost = h1_data["cost"]
            h1_time = h1_data["time_ms"]
        else:
            t0 = time.perf_counter()
            h1_tour = heuristic_h1_centroid(instance)
            h1_time = (time.perf_counter() - t0) * 1000.0
            h1_cost = instance.calculate_tour_cost(h1_tour)

        records.append({
            "instance": instance.name,
            "type": instance.edge_weight_type,
            "dimension": instance.dimension,
            "heuristic": "H1 (Centroid-Based)",
            "cost": h1_cost,
            "time_ms": h1_time
        })
        print(f"  > {'H1 (Centroid-Based)':<25} | Custo: {h1_cost:<9} | Tempo: {h1_time:.2f} ms")

        # Computa rota H5 (necessária para warm-start e registro de H5)
        t0 = time.perf_counter()
        h5_tour = heuristic_h5_farthest_insertion(instance)
        h5_calc_time = (time.perf_counter() - t0) * 1000.0
        h5_cost = instance.calculate_tour_cost(h5_tour)

        # Se já existia tempo de benchmark original para H5, mantém para consistência
        if (instance.name, "H5 (Farthest Insertion)") in existing_top2:
            h5_time = existing_top2[(instance.name, "H5 (Farthest Insertion)")]["time_ms"]
            h5_cost = existing_top2[(instance.name, "H5 (Farthest Insertion)")]["cost"]
        else:
            h5_time = h5_calc_time

        records.append({
            "instance": instance.name,
            "type": instance.edge_weight_type,
            "dimension": instance.dimension,
            "heuristic": "H5 (Farthest Insertion)",
            "cost": h5_cost,
            "time_ms": h5_time
        })
        print(f"  > {'H5 (Farthest Insertion)':<25} | Custo: {h5_cost:<9} | Tempo: {h5_time:.2f} ms")

        # Configuração das variantes de metaheurística:
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

    df_combined = pd.DataFrame(records)

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

    # 3. Geração dos Gráficos Comparativos
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
