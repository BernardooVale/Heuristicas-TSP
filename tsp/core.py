"""
Módulo de estruturas básicas e carregamento de instâncias TSP.
"""

import os
import math
from typing import Tuple, Dict, List


def nint(x: float) -> int:
    """Arredonda para o inteiro mais próximo seguindo a especificação TSPLIB."""
    return int(x + 0.5)


def calc_dist_att(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> int:
    """Cálculo de distância pseudo-euclidiana (ATT) segundo a TSPLIB."""
    xd = coord1[0] - coord2[0]
    yd = coord1[1] - coord2[1]
    rij = math.sqrt((xd * xd + yd * yd) / 10.0)
    tij = nint(rij)
    if tij < rij:
        return tij + 1
    return tij


def calc_dist_euc_2d(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> int:
    """Cálculo de distância Euclidiana 2D inteira (EUC_2D) segundo a TSPLIB."""
    xd = coord1[0] - coord2[0]
    yd = coord1[1] - coord2[1]
    return nint(math.sqrt(xd * xd + yd * yd))


class TSPInstance:
    """Representa uma instância do TSP com nós, distâncias e avaliação de soluções."""

    def __init__(self, name: str, edge_weight_type: str, nodes: Dict[int, Tuple[float, float]]):
        self.name = name
        self.edge_weight_type = edge_weight_type.upper()
        self.nodes = nodes  # id: (x, y) com floats
        self.node_ids = list(nodes.keys())
        self.dimension = len(nodes)
        self.dist_matrix: Dict[int, Dict[int, int]] = {}
        self._build_graph()

    def _build_graph(self):
        dist_fn = calc_dist_att if self.edge_weight_type == "ATT" else calc_dist_euc_2d
        for u in self.node_ids:
            self.dist_matrix[u] = {}
            for v in self.node_ids:
                if u == v:
                    self.dist_matrix[u][v] = 0
                else:
                    self.dist_matrix[u][v] = dist_fn(self.nodes[u], self.nodes[v])

    def get_distance(self, u: int, v: int) -> int:
        """Retorna a distância pré-computada entre os nós u e v."""
        return self.dist_matrix[u][v]

    def calculate_tour_cost(self, tour: List[int]) -> int:
        """Calcula o custo total de um ciclo Hamiltoniano (tour)."""
        if not tour:
            return 0
        cost = 0
        n = len(tour)
        for i in range(n):
            u = tour[i]
            v = tour[(i + 1) % n]
            cost += self.dist_matrix[u][v]
        return cost


def read_tsp_file(file_path: str) -> TSPInstance:
    """Lê um arquivo .tsp compatível com TSPLIB e retorna um objeto TSPInstance."""
    name = ""
    edge_weight_type = ""
    nodes = {}

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]

    for line in lines[:6]:
        if line.startswith("NAME"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                name = parts[1].strip()
        elif line.startswith("EDGE_WEIGHT_TYPE"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                edge_weight_type = parts[1].strip()

    if not edge_weight_type:
        edge_weight_type = "ATT" if "att" in os.path.basename(file_path).lower() else "EUC_2D"

    for line in lines[6:]:
        if not line or "EOF" in line:
            break
        parts = line.split()
        if len(parts) >= 3:
            node_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            nodes[node_id] = (x, y)

    return TSPInstance(name=name, edge_weight_type=edge_weight_type, nodes=nodes)
