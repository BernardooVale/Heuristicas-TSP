"""
Implementação de Metaheurísticas e Busca Local para o TSP.
Baseado nas diretrizes de David S. Johnson & Lyle A. McGeoch:
- Simulated Annealing (SA)
- Busca Local 2-Opt Clássica (Iterated Local Search com Don't-Look Bits)
"""

import math
import random
from typing import List, Optional, Tuple, Callable
from tsp.core import TSPInstance
from tsp.heuristics import heuristic_h4_nearest_neighbor, heuristic_h5_farthest_insertion
from tsp.operators import two_opt_swap, two_opt_cost_delta


def get_initial_tour(instance: TSPInstance, method: str = "random", seed: Optional[int] = 42) -> List[int]:
    """
    Gera a rota inicial conforme a hipótese experimental:
    - 'random': permutação aleatória dos vértices
    - 'farthest_insertion': construtiva de alta qualidade (H5)
    - 'nearest_neighbor': heurística gulosa clássica rápida (H4)
    """
    if seed is not None:
        random.seed(seed)

    if method == "random":
        tour = list(instance.node_ids)
        random.shuffle(tour)
        return tour
    elif method == "farthest_insertion":
        return heuristic_h5_farthest_insertion(instance)
    elif method == "nearest_neighbor":
        return heuristic_h4_nearest_neighbor(instance)
    else:
        raise ValueError(f"Método de rota inicial desconhecido: {method}")


def local_search_2opt_accelerated(
    tour: List[int],
    instance: TSPInstance,
    max_iterations: int = 500,
    use_dont_look: bool = True
) -> Tuple[List[int], int]:
    """
    Busca Local 2-Opt acelerada por Don't-Look Bits e avaliação O(1) de delta.
    Garante convergência rápida a um ótimo local de 2-Opt (2-ótimo).
    """
    n = len(tour)
    current_tour = list(tour)
    current_cost = instance.calculate_tour_cost(current_tour)

    # Don't look bits
    dont_look = [False] * n

    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        for i in range(n):
            if use_dont_look and dont_look[i]:
                continue

            city_improved = False
            # Varre possíveis cortes 2-opt envolvendo i
            for k in range(i + 2, n if i > 0 else n - 1):
                delta = two_opt_cost_delta(current_tour, i, k, instance)
                if delta < 0:
                    current_tour = two_opt_swap(current_tour, i, k)
                    current_cost += delta
                    improved = True
                    city_improved = True

                    if use_dont_look:
                        dont_look[i] = False
                        dont_look[k] = False
                        dont_look[(i - 1) % n] = False
                        dont_look[(k + 1) % n] = False
                    break

            if use_dont_look and not city_improved:
                dont_look[i] = True

    return current_tour, current_cost


def simulated_annealing(
    instance: TSPInstance,
    initial_tour: Optional[List[int]] = None,
    alpha: float = 0.98,
    initial_temp: Optional[float] = None,
    final_temp: float = 1e-3,
    steps_per_temp: Optional[int] = None,
    seed: Optional[int] = 42
) -> List[int]:
    """
    Simulated Annealing (SA) para o TSP com resfriamento geométrico T_k+1 = alpha * T_k.
    Vizinhança baseada no operador 2-opt com cálculo em O(1) de delta.
    Critério de aceitação de Metropolis: exp(-delta / T).
    """
    if seed is not None:
        random.seed(seed)

    n = instance.dimension
    if initial_tour is None:
        current_tour = get_initial_tour(instance, method="random", seed=seed)
    else:
        current_tour = list(initial_tour)

    current_cost = instance.calculate_tour_cost(current_tour)
    best_tour = list(current_tour)
    best_cost = current_cost

    # Estimativa de temperatura inicial se não fornecida
    # Amostra movimentos para calibrar T0 de forma que a taxa de aceitação inicial seja ~80%
    if initial_temp is None:
        deltas = []
        for _ in range(min(100, n * 2)):
            i = random.randint(1, n - 2)
            k = random.randint(i + 1, n - 1)
            d = two_opt_cost_delta(current_tour, i, k, instance)
            if d > 0:
                deltas.append(d)
        if deltas:
            avg_delta = sum(deltas) / len(deltas)
            initial_temp = -avg_delta / math.log(0.8)
        else:
            initial_temp = 100.0

    if steps_per_temp is None:
        # Padrão: proportional ao tamanho da instância
        steps_per_temp = max(100, n * 5)

    temp = initial_temp

    while temp > final_temp:
        for _ in range(steps_per_temp):
            i = random.randint(1, n - 2)
            k = random.randint(i + 1, n - 1)
            if (k + 1) % n == i - 1:
                continue

            delta = two_opt_cost_delta(current_tour, i, k, instance)

            # Critério de Metropolis
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_tour = two_opt_swap(current_tour, i, k)
                current_cost += delta

                if current_cost < best_cost:
                    best_cost = current_cost
                    best_tour = list(current_tour)

        temp *= alpha

    return best_tour


def classical_2opt(
    instance: TSPInstance,
    initial_tour: Optional[List[int]] = None,
    seed: Optional[int] = 42
) -> List[int]:
    """
    Busca Local Clássica 2-Opt pura.
    """
    if initial_tour is None:
        tour = get_initial_tour(instance, method="random", seed=seed)
    else:
        tour = list(initial_tour)

    best_tour, _ = local_search_2opt_accelerated(tour, instance, max_iterations=1000)
    return best_tour
