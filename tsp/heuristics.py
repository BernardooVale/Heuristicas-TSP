"""
Implementação das heurísticas construtivas para o Caixeiro Viajante (TSP).
"""

from typing import List, Dict, Callable
from tsp.core import TSPInstance, calc_dist_att, calc_dist_euc_2d
from tsp.utils import DisjointSet, cheapest_insertion_step


def heuristic_h1_centroid(instance: TSPInstance) -> List[int]:
    """
    H1 — Centroid-Based Insertion:
    Calcula centróide geométrico (média X, média Y).
    Ordena vértices por distância ao centróide (decrescente).
    Insere na rota sempre o mais periférico primeiro, usando cheapest insertion.
    """
    dist_fn = calc_dist_att if instance.edge_weight_type == "ATT" else calc_dist_euc_2d

    mean_x = sum(coord[0] for coord in instance.nodes.values()) / instance.dimension
    mean_y = sum(coord[1] for coord in instance.nodes.values()) / instance.dimension
    center = (mean_x, mean_y)

    dist_to_center = {v: dist_fn(instance.nodes[v], center) for v in instance.node_ids}
    sorted_nodes = sorted(instance.node_ids, key=lambda v: dist_to_center[v], reverse=True)

    if len(sorted_nodes) <= 2:
        return sorted_nodes

    tour = [sorted_nodes[0], sorted_nodes[1]]
    for v in sorted_nodes[2:]:
        cheapest_insertion_step(tour, v, instance)

    return tour


def heuristic_h2_eccentricity(instance: TSPInstance) -> List[int]:
    """
    H2 — Eccentricity Insertion:
    Calcula excentricidade de cada vértice como a soma das distâncias para todos os outros.
    Ordena decrescente e insere via cheapest insertion.
    """
    eccentricity = {
        v: sum(instance.get_distance(v, u) for u in instance.node_ids if u != v)
        for v in instance.node_ids
    }
    sorted_nodes = sorted(instance.node_ids, key=lambda v: eccentricity[v], reverse=True)

    if len(sorted_nodes) <= 2:
        return sorted_nodes

    tour = [sorted_nodes[0], sorted_nodes[1]]
    for v in sorted_nodes[2:]:
        cheapest_insertion_step(tour, v, instance)

    return tour


def heuristic_h3_hybrid(instance: TSPInstance) -> List[int]:
    """
    H3 — Hybrid Insertion (α=β=0.5):
    Combina H1 e H2 com normalização min-max:
    score(v) = 0.5 * norm(dist(v, centro)) + 0.5 * norm(exc(v))
    """
    dist_fn = calc_dist_att if instance.edge_weight_type == "ATT" else calc_dist_euc_2d
    mean_x = sum(coord[0] for coord in instance.nodes.values()) / instance.dimension
    mean_y = sum(coord[1] for coord in instance.nodes.values()) / instance.dimension
    center = (mean_x, mean_y)

    dist_to_center = {v: dist_fn(instance.nodes[v], center) for v in instance.node_ids}
    eccentricity = {
        v: sum(instance.get_distance(v, u) for u in instance.node_ids if u != v)
        for v in instance.node_ids
    }

    min_c, max_c = min(dist_to_center.values()), max(dist_to_center.values())
    range_c = (max_c - min_c) if max_c > min_c else 1.0

    min_e, max_e = min(eccentricity.values()), max(eccentricity.values())
    range_e = (max_e - min_e) if max_e > min_e else 1.0

    scores = {}
    for v in instance.node_ids:
        norm_c = (dist_to_center[v] - min_c) / range_c
        norm_e = (eccentricity[v] - min_e) / range_e
        scores[v] = 0.5 * norm_c + 0.5 * norm_e

    sorted_nodes = sorted(instance.node_ids, key=lambda v: scores[v], reverse=True)

    if len(sorted_nodes) <= 2:
        return sorted_nodes

    tour = [sorted_nodes[0], sorted_nodes[1]]
    for v in sorted_nodes[2:]:
        cheapest_insertion_step(tour, v, instance)

    return tour


def heuristic_h4_nearest_neighbor(instance: TSPInstance, start_node: int = None) -> List[int]:
    """
    H4 — Nearest Neighbor:
    Começa num vértice (por padrão primeiro nó), sempre visita o vizinho não visitado mais próximo.
    """
    if start_node is None:
        start_node = instance.node_ids[0]

    unvisited = set(instance.node_ids)
    unvisited.remove(start_node)

    tour = [start_node]
    current = start_node

    while unvisited:
        next_node = min(unvisited, key=lambda u: instance.get_distance(current, u))
        tour.append(next_node)
        unvisited.remove(next_node)
        current = next_node

    return tour


def heuristic_h5_farthest_insertion(instance: TSPInstance) -> List[int]:
    """
    H5 — Farthest Insertion:
    Inicializa a rota com os 2 vértices mais distantes entre si.
    A cada passo seleciona o vértice k que maximiza min(d(k, r) para r na rota),
    e insere k na posição cheapest.
    """
    nodes = instance.node_ids
    max_d = -1
    best_pair = (nodes[0], nodes[1])
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            d = instance.get_distance(nodes[i], nodes[j])
            if d > max_d:
                max_d = d
                best_pair = (nodes[i], nodes[j])

    tour = [best_pair[0], best_pair[1]]
    in_tour = set(tour)
    unvisited = [u for u in nodes if u not in in_tour]

    min_dist_to_tour = {u: min(instance.get_distance(u, r) for r in tour) for u in unvisited}

    while unvisited:
        k = max(unvisited, key=lambda u: min_dist_to_tour[u])
        cheapest_insertion_step(tour, k, instance)
        unvisited.remove(k)
        for u in unvisited:
            d_u_k = instance.get_distance(u, k)
            if d_u_k < min_dist_to_tour[u]:
                min_dist_to_tour[u] = d_u_k

    return tour


def heuristic_h6_greedy_edge(instance: TSPInstance) -> List[int]:
    """
    H6 — Greedy Edge:
    Ordena todas as arestas por custo crescente.
    Adiciona aresta se:
      1. grau(u) < 2 e grau(v) < 2
      2. não cria ciclo prematuro (union-find) a não ser que seja a última aresta (n-ésima).
    Reconstrói o ciclo ao final a partir do grafo de adjacências 2-regular.
    """
    nodes = instance.node_ids
    n = instance.dimension

    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            u, v = nodes[i], nodes[j]
            edges.append((instance.get_distance(u, v), u, v))
    edges.sort(key=lambda e: e[0])

    degree = {u: 0 for u in nodes}
    adj: Dict[int, List[int]] = {u: [] for u in nodes}
    uf = DisjointSet(nodes)

    selected_edges = 0
    for cost, u, v in edges:
        if degree[u] < 2 and degree[v] < 2:
            root_u = uf.find(u)
            root_v = uf.find(v)

            if root_u != root_v or selected_edges == n - 1:
                uf.union(u, v)
                adj[u].append(v)
                adj[v].append(u)
                degree[u] += 1
                degree[v] += 1
                selected_edges += 1
                if selected_edges == n:
                    break

    tour = [nodes[0]]
    curr = nodes[0]
    prev = None

    for _ in range(n - 1):
        neighbors = adj[curr]
        next_node = neighbors[0] if neighbors[0] != prev else neighbors[1]
        tour.append(next_node)
        prev = curr
        curr = next_node

    return tour


# Dicionário mapeando os nomes e funções das 6 heurísticas
HEURISTICS: Dict[str, Callable[[TSPInstance], List[int]]] = {
    "H1 (Centroid-Based)": heuristic_h1_centroid,
    "H2 (Eccentricity)": heuristic_h2_eccentricity,
    "H3 (Hybrid-Score)": heuristic_h3_hybrid,
    "H4 (Nearest Neighbor)": heuristic_h4_nearest_neighbor,
    "H5 (Farthest Insertion)": heuristic_h5_farthest_insertion,
    "H6 (Greedy Edge)": heuristic_h6_greedy_edge,
}
