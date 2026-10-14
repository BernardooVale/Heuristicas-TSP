"""
Módulo principal do pacote TSP.
"""

from tsp.core import (
    TSPInstance,
    read_tsp_file,
    calc_dist_att,
    calc_dist_euc_2d,
    nint,
)
from tsp.utils import (
    DisjointSet,
    cheapest_insertion_step,
)
from tsp.heuristics import (
    HEURISTICS,
    heuristic_h1_centroid,
    heuristic_h2_eccentricity,
    heuristic_h3_hybrid,
    heuristic_h4_nearest_neighbor,
    heuristic_h5_farthest_insertion,
    heuristic_h6_greedy_edge,
)
__all__ = [
    "TSPInstance",
    "read_tsp_file",
    "calc_dist_att",
    "calc_dist_euc_2d",
    "nint",
    "DisjointSet",
    "cheapest_insertion_step",
    "HEURISTICS",
    "heuristic_h1_centroid",
    "heuristic_h2_eccentricity",
    "heuristic_h3_hybrid",
    "heuristic_h4_nearest_neighbor",
    "heuristic_h5_farthest_insertion",
    "heuristic_h6_greedy_edge",
]

# Imports opcionais de benchmark e gráficos (dependem de pandas/matplotlib/seaborn)
try:
    from tsp.benchmark import run_benchmark
    from tsp.visualization import (
        plot_box_candle_with_mean,
        plot_pareto_front,
        plot_heatmaps,
    )
    __all__ += [
        "run_benchmark",
        "plot_box_candle_with_mean",
        "plot_pareto_front",
        "plot_heatmaps",
    ]
except ImportError:
    pass

