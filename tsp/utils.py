"""
Estruturas de dados auxiliares e utilitários para algoritmos do TSP.
"""

from typing import List
from tsp.core import TSPInstance


class DisjointSet:
    """Estrutura Union-Find (Disjoint Set Union) com union-by-rank e path compression."""

    def __init__(self, elements: List[int]):
        self.parent = {x: x for x in elements}
        self.rank = {x: 0 for x in elements}

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1
            return True
        return False


def cheapest_insertion_step(tour: List[int], node: int, instance: TSPInstance) -> None:
    """Insere o nó na rota existente na posição que minimiza o custo incremental (delta)."""
    m = len(tour)
    best_cost = float('inf')
    best_pos = 1

    for idx in range(m):
        u = tour[idx]
        v = tour[(idx + 1) % m]
        delta = instance.get_distance(u, node) + instance.get_distance(node, v) - instance.get_distance(u, v)
        if delta < best_cost:
            best_cost = delta
            best_pos = idx + 1

    tour.insert(best_pos, node)
