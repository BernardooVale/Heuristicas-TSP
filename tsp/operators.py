"""
Operadores e movimentos de busca local para TSP (úteis para meta-heurísticas).
"""

from typing import List, Tuple
from tsp.core import TSPInstance


def two_opt_swap(tour: List[int], i: int, k: int) -> List[int]:
    """
    Aplica movimento 2-opt invertendo o segmento entre i e k (inclusive).
    Ex: [A, B, C, D, E] com i=1, k=3 -> [A, D, C, B, E]
    """
    return tour[:i] + tour[i:k + 1][::-1] + tour[k + 1:]


def two_opt_cost_delta(tour: List[int], i: int, k: int, instance: TSPInstance) -> int:
    """
    Calcula a variação de custo em O(1) de aplicar 2-opt entre i e k.
    Delta < 0 significa melhora na solução.
    """
    n = len(tour)
    u1, u2 = tour[i - 1], tour[i]
    v1, v2 = tour[k], tour[(k + 1) % n]

    # Removendo arestas (u1, u2) e (v1, v2), adicionando (u1, v1) e (u2, v2)
    old_dist = instance.get_distance(u1, u2) + instance.get_distance(v1, v2)
    new_dist = instance.get_distance(u1, v1) + instance.get_distance(u2, v2)
    return new_dist - old_dist


def local_search_2opt(tour: List[int], instance: TSPInstance, max_iterations: int = 1000) -> Tuple[List[int], int]:
    """
    Busca local 2-opt clássica (First-Improvement ou Best-Improvement).
    Pode ser reutilizada em ILS, VNS, GRASP, Memetic Algorithms, etc.
    """
    best_tour = list(tour)
    best_cost = instance.calculate_tour_cost(best_tour)
    n = len(best_tour)

    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        for i in range(1, n - 1):
            for k in range(i + 1, n):
                # Evita arestas adjacentes no ciclo que não alteram a topologia
                if (k + 1) % n == i - 1:
                    continue

                delta = two_opt_cost_delta(best_tour, i, k, instance)
                if delta < 0:
                    best_tour = two_opt_swap(best_tour, i, k)
                    best_cost += delta
                    improved = True
                    break  # First improvement
            if improved:
                break

    return best_tour, best_cost
