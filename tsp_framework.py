"""

Autoria: Bernardo Vale dos Santos Bento

Comandos para rodar o arquivo (supondo que python 3 já esteja instalado e configurado nas variáveis de ambiente):

Primeiro comando para Windows, segundo para Linux/MacOS

Mínimo:
pip install pandas numpy matplotlib seaborn && python tsp_framework.py
ou
pip install pandas numpy matplotlib seaborn && python3 tsp_framework.py

Recomendado:
python -m venv venv && venv/Scripts/activate && pip install pandas numpy matplotlib seaborn && python tsp_framework.py
ou
python3 -m venv venv && source venv/bin/activate && pip install pandas numpy matplotlib seaborn && python3 tsp_framework.py

"""

import os
import math
import time
import glob
from typing import List, Tuple, Dict, Callable
import seaborn as sns

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# ==============================================================================
# CÁLCULO DE DISTÂNCIAS (TSPLIB: ATT e EUC_2D)
# ==============================================================================

def nint(x: float) -> int:
    return int(x + 0.5)

def calc_dist_att(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> int:
    xd = coord1[0] - coord2[0]
    yd = coord1[1] - coord2[1]
    rij = math.sqrt((xd * xd + yd * yd) / 10.0)
    tij = nint(rij)
    if tij < rij:
        return tij + 1
    return tij

def calc_dist_euc_2d(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> int:
    xd = coord1[0] - coord2[0]
    yd = coord1[1] - coord2[1]
    return nint(math.sqrt(xd * xd + yd * yd))

# ==============================================================================
# GRAFO
# ==============================================================================

class TSPInstance:
    
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
        return self.dist_matrix[u][v]

    def calculate_tour_cost(self, tour: List[int]) -> int:
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

# ==============================================================================
# ESTRUTURA AUXILIAR UNION-FIND (PARA H6 - GREEDY EDGE)
# ==============================================================================

class DisjointSet:
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

# ==============================================================================
# FUNÇÃO AUXILIAR DE INSERÇÃO MAIS BARATA (CHEAPEST INSERTION)
# ==============================================================================
def cheapest_insertion_step(tour: List[int], node: int, instance: TSPInstance) -> None:
    
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

# ==============================================================================
# IMPLEMENTAÇÃO DAS 6 HEURÍSTICAS
# ==============================================================================

# H1: Centroid-Based Insertion
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

    # Prioridade = dist(v, centro) decrescente
    dist_to_center = {v: dist_fn(instance.nodes[v], center) for v in instance.node_ids}
    sorted_nodes = sorted(instance.node_ids, key=lambda v: dist_to_center[v], reverse=True)

    if len(sorted_nodes) <= 2:
        return sorted_nodes

    # Inicializa rota com os 2 mais distantes do centro
    tour = [sorted_nodes[0], sorted_nodes[1]]

    # Insere os demais na ordem decrescente de distância ao centro via cheapest insertion
    for v in sorted_nodes[2:]:
        cheapest_insertion_step(tour, v, instance)

    return tour

# H2: Eccentricity Insertion
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

# H3: Hybrid Insertion (alpha = beta = 0.5)
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

    # Normalização Min-Max: (x - min) / (max - min)
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

# H4: Nearest Neighbor
def heuristic_h4_nearest_neighbor(instance: TSPInstance, start_node: int = None) -> List[int]:
    """
    H4 — Nearest Neighbor:
    Começa num vértice (por padrão aleatório ou 1º), sempre visita o vizinho não visitado mais próximo.
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

# H5: Farthest Insertion
def heuristic_h5_farthest_insertion(instance: TSPInstance) -> List[int]:
    """
    H5 — Farthest Insertion:
    Inicializa a rota com os 2 vértices mais distantes entre si.
    A cada passo seleciona o vértice k que maximiza min(d(k, r) para r na rota),
    e insere k na posição cheapest.
    """
    # Encontra o par com maior distância
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

    # Mantém array com a distância mínima de cada nó não visitado até a rota
    min_dist_to_tour = {u: min(instance.get_distance(u, r) for r in tour) for u in unvisited}

    while unvisited:
        # Seleciona k = argmax min_dist_to_tour
        k = max(unvisited, key=lambda u: min_dist_to_tour[u])

        # Insere na melhor posição
        cheapest_insertion_step(tour, k, instance)

        # Atualiza estruturas
        unvisited.remove(k)
        for u in unvisited:
            d_u_k = instance.get_distance(u, k)
            if d_u_k < min_dist_to_tour[u]:
                min_dist_to_tour[u] = d_u_k

    return tour

# H6: Greedy Edge
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

    # Lista todas as arestas únicas e ordena por custo
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

            # Se não cria ciclo fechado OU se é a última aresta para fechar o ciclo completo
            if root_u != root_v or selected_edges == n - 1:
                uf.union(u, v)
                adj[u].append(v)
                adj[v].append(u)
                degree[u] += 1
                degree[v] += 1
                selected_edges += 1
                if selected_edges == n:
                    break

    # Reconstrói a rota seguindo as adjacências
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

# ==============================================================================
# GERAÇÃO DE GRÁFICOS E VISUALIZAÇÕES AVANÇADAS
# ==============================================================================

def plot_box_candle_with_mean(df: pd.DataFrame, metric: str, ylabel: str, title: str, output_path: str):
    
    plt.figure(figsize=(12, 6))

    heuristics = df["heuristic"].unique()
    data = [df[df["heuristic"] == h][metric].values for h in heuristics]
    means = [np.mean(vals) for vals in data]

    # Boxplot (Caixa com Q1, Mediana, Q3, Whiskers com Min e Max)
    bp = plt.boxplot(data, tick_labels=heuristics, patch_artist=True,
                     showmeans=False,
                     whis=[0, 100],  # Min e Max reais
                     boxprops=dict(facecolor="#D1E8E2", color="#116466", linewidth=1.5),
                     whiskerprops=dict(color="#116466", linewidth=1.5, linestyle="--"),
                     capprops=dict(color="#116466", linewidth=2),
                     medianprops=dict(color="#D9B08C", linewidth=2.5))

    # Sobreposição do Caso Médio com linha e pontos destacados
    x_coords = list(range(1, len(heuristics) + 1))
    plt.plot(x_coords, means, color="#FF6F59", marker="D", markersize=9, linewidth=2,
             linestyle="-", label="Caso Médio (Média Aritmética)", zorder=6)

    # Anotação com o valor da média
    for x, m in zip(x_coords, means):
        if metric == "time_ms":
            txt = f"{m:.2f} ms"
        elif metric == "relative_cost":
            txt = f"{m:.2f}x"
        else:
            txt = f"{m:,.0f}"
        plt.annotate(txt, (x, m), textcoords="offset points", xytext=(0, 10),
                     ha="center", fontsize=9, fontweight="bold", color="#FF6F59")

    plt.title(title, fontsize=13, fontweight="bold")
    plt.xlabel("Heurística", fontsize=11, fontweight="bold")
    plt.ylabel(ylabel, fontsize=11, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", frameon=True)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

def plot_pareto_front(df_summary: pd.DataFrame, output_path: str):
    
    plt.figure(figsize=(10, 7))

    x = df_summary["mean_relative_cost"].values
    y = df_summary["mean_time_ms"].values
    labels = df_summary["heuristic"].values

    # Identifica pontos de Pareto (min x, min y)
    pareto_mask = []
    for i in range(len(df_summary)):
        is_dominated = False
        for j in range(len(df_summary)):
            if i != j:
                # Se outro ponto for menor ou igual em ambos e estritamente menor em pelo menos um
                if (x[j] <= x[i] and y[j] <= y[i]) and (x[j] < x[i] or y[j] < y[i]):
                    is_dominated = True
                    break
        pareto_mask.append(not is_dominated)

    colors = ["#E63946" if is_p else "#457B9D" for is_p in pareto_mask]

    plt.scatter(x, y, c=colors, s=160, edgecolors="black", linewidth=1.5, zorder=5)

    # Liga os pontos da Fronteira de Pareto
    pareto_pts = sorted([(x[i], y[i], labels[i]) for i in range(len(x)) if pareto_mask[i]], key=lambda pt: pt[0])
    if len(pareto_pts) > 1:
        px = [p[0] for p in pareto_pts]
        py = [p[1] for p in pareto_pts]
        plt.plot(px, py, color="#E63946", linestyle="--", linewidth=2, label="Fronteira de Pareto (Não Dominadas)")

    for xi, yi, lab, is_p in zip(x, y, labels, pareto_mask):
        weight = "bold" if is_p else "normal"
        color = "#990000" if is_p else "#1D3557"
        plt.annotate(f" {lab}", (xi, yi), textcoords="offset points", xytext=(6, 4),
                     fontsize=10, fontweight=weight, color=color)

    plt.title("Análise Multiobjetivo: Qualidade da Rota vs Tempo de Execução", fontsize=13, fontweight="bold")
    plt.xlabel("Custo Médio Relativo (Normalizado pela melhor heurística da instância)", fontsize=11, fontweight="bold")
    plt.ylabel("Tempo Médio de Execução (ms)", fontsize=11, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left")
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

def plot_heatmaps(df: pd.DataFrame):

    # 1. Pivot table de custo relativo
    pivot_rel = df.pivot(index="instance", columns="heuristic", values="relative_cost")
    # Ordena instâncias por dimensão para melhor legibilidade
    dims = df.drop_duplicates(subset=["instance"]).set_index("instance")["dimension"]
    pivot_rel["dim"] = dims
    pivot_rel = pivot_rel.sort_values(by="dim").drop(columns=["dim"])

    plt.figure(figsize=(12, 10))
    sns.heatmap(pivot_rel, annot=True, fmt=".3f", cmap="YlGnBu", cbar_kws={'label': 'Custo Relativo (1.000 = Melhor Heurística)'}, linewidths=0.5)
    plt.title("Heatmap Comparativo de Qualidade da Solução\n(Custo Normalizado por Instância)", fontsize=13, fontweight='bold')
    plt.xlabel("Heurística", fontsize=11, fontweight='bold')
    plt.ylabel("Instância TSP (Ordenada por nº de vértices)", fontsize=11, fontweight='bold')
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig("graficos/heatmap_custo_relativo.png", dpi=300)
    plt.close()

    # 2. Pivot table de tempo (ms)
    pivot_time = df.pivot(index="instance", columns="heuristic", values="time_ms")
    pivot_time["dim"] = dims
    pivot_time = pivot_time.sort_values(by="dim").drop(columns=["dim"])

    plt.figure(figsize=(12, 10))
    sns.heatmap(pivot_time, annot=True, fmt=".2f", cmap="Oranges", cbar_kws={'label': 'Tempo de Execução (ms)'}, linewidths=0.5)
    plt.title("Heatmap Comparativo de Tempo Computacional (ms)", fontsize=13, fontweight='bold')
    plt.xlabel("Heurística", fontsize=11, fontweight='bold')
    plt.ylabel("Instância TSP (Ordenada por nº de vértices)", fontsize=11, fontweight='bold')
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig("graficos/heatmap_tempo_execucao.png", dpi=300)
    plt.close()

# ==============================================================================
# PIPELINE DE SIMULAÇÃO COMPLETO
# ==============================================================================

def run_simulation(base_dir: str = "."):
    
    instances_paths = []
    instances_paths.extend(glob.glob(os.path.join(base_dir, "*.tsp")))
    instances_paths.extend(glob.glob(os.path.join(base_dir, "EUC_2D", "*.tsp")))
    instances_paths = sorted(list(set(instances_paths)))

    print(f"Total de instâncias TSP encontradas: {len(instances_paths)}")
    print(f"Total de heurísticas a avaliar: {len(HEURISTICS)}\n")

    records = []

    for path in instances_paths:
        instance = read_tsp_file(path)
        print(f"--- Processando Instância: {instance.name} (Vértices: {instance.dimension}, Tipo: {instance.edge_weight_type}) ---")

        for h_name, h_func in HEURISTICS.items():
            start_time = time.perf_counter()
            tour = h_func(instance)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            cost = instance.calculate_tour_cost(tour)

            records.append({
                "instance": instance.name,
                "type": instance.edge_weight_type,
                "dimension": instance.dimension,
                "heuristic": h_name,
                "cost": cost,
                "time_ms": elapsed_ms
            })
            print(f"  > {h_name:<22} | Custo: {cost:<9} | Tempo: {elapsed_ms:.2f} ms")

    df = pd.DataFrame(records)

    # Custo relativo em relação à melhor solução encontrada para cada instância
    best_per_inst = df.groupby("instance")["cost"].transform("min")
    df["relative_cost"] = df["cost"] / best_per_inst

    # Salva dados coletados em CSV
    os.makedirs("resultados", exist_ok=True)
    df.to_csv("resultados/metricas_tsp.csv", index=False)
    print("\nResultados numéricos salvos em 'resultados/metricas_tsp.csv'.")

    # Resumo para curva de pareto
    df_summary = df.groupby("heuristic").agg(
        mean_cost=("cost", "mean"),
        mean_relative_cost=("relative_cost", "mean"),
        mean_time_ms=("time_ms", "mean")
    ).reset_index()
    df_summary.to_csv("resultados/resumo_heurísticas.csv", index=False)

    # Geração dos Gráficos
    print("\nGerando gráficos...")

    # 1. Heatmaps Comparativos entre Instâncias e Heurísticas
    print(" - Gerando Heatmaps Comparativos...")
    plot_heatmaps(df)

    # 2. Gráfico Box/Candle com Média - Custo Relativo
    print(" - Gerando Boxplot/Candle de Custo...")
    plot_box_candle_with_mean(
        df=df,
        metric="relative_cost",
        ylabel="Custo Relativo (1.0 = Melhor da Instância)",
        title="Distribuição do Custo Relativo por Heurística (Quartis, Min, Max e Caso Médio)",
        output_path="graficos/boxplot_custo_relativo.png"
    )

    # 3. Gráfico Box/Candle com Média - Tempo de Execução (ms)
    print(" - Gerando Boxplot/Candle de Tempo...")
    plot_box_candle_with_mean(
        df=df,
        metric="time_ms",
        ylabel="Tempo de Execução (ms)",
        title="Distribuição do Tempo de Execução por Heurística (Quartis, Min, Max e Caso Médio)",
        output_path="graficos/boxplot_tempo_execucao.png"
    )

    # 4. Curva de Pareto Multiobjetivo
    print(" - Gerando Curva de Fronteira de Pareto...")
    plot_pareto_front(
        df_summary=df_summary,
        output_path="graficos/fronteira_pareto.png"
    )

    # Remove o comparativo antigo se existir
    if os.path.exists("graficos/comparativo_custos.png"):
        try:
            os.remove("graficos/comparativo_custos.png")
        except Exception:
            pass

if __name__ == "__main__":
    run_simulation()