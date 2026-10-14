"""
Autoria: Bernardo Vale dos Santos Bento

Script de entrada para compatibilidade e execução do benchmark de heurísticas para o TSP.
O código do projeto foi modularizado no pacote `tsp/`.
"""

from tsp.core import (
    nint,
    calc_dist_att,
    calc_dist_euc_2d,
    TSPInstance,
    read_tsp_file,
)
from tsp.utils import (
    DisjointSet,
    cheapest_insertion_step,
)
from tsp.heuristics import (
    heuristic_h1_centroid,
    heuristic_h2_eccentricity,
    heuristic_h3_hybrid,
    heuristic_h4_nearest_neighbor,
    heuristic_h5_farthest_insertion,
    heuristic_h6_greedy_edge,
    HEURISTICS,
)
from tsp.visualization import (
    plot_box_candle_with_mean,
    plot_pareto_front,
    plot_heatmaps,
)
from tsp.benchmark import run_benchmark


def run_simulation(base_dir: str = "."):
    """Função compatível com a interface anterior."""
    run_benchmark(base_dir=base_dir)


if __name__ == "__main__":
    run_simulation()