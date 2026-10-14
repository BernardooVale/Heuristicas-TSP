# Framework de Heurísticas para o Problema do Caixeiro Viajante (TSP)
# Traveling Salesman Problem (TSP) Heuristics Framework

> **Quick Navigation / Navegação Rápida:**
> - [🇧🇷 Versão em Português](#-relatório-técnico-resolução-do-caixeiro-viajante-tsp-com-heurísticas-construtivas)
> - [🇺🇸 English Version](#-technical-report-traveling-salesman-problem-tsp-constructive-heuristics)

---

# 🇧🇷 Relatório Técnico: Resolução do Caixeiro Viajante (TSP) com Heurísticas Construtivas

## 1. Visão Geral do Projeto

O Problema do Caixeiro Viajante (*Traveling Salesman Problem* — TSP) consiste em encontrar o circuito hamiltoniano de menor custo que visita todos os vértices de um grafo exatamente uma vez e retorna ao vértice de partida. Por ser um problema NP-Difícil (*NP-Hard*), métodos exatos tornam-se intratáveis à medida que o número de vértices cresce, demandando o uso de **heurísticas construtivas** capazes de entregar soluções de alta qualidade em tempo polinomial.

Este projeto implementou um framework em Python que:
1. **Lê instâncias padrão TSPLIB**: Suporta as formulações de pesos de arestas **EUC_2D** (distância euclidiana bidimensional) e **ATT** (distância pseudo-euclidiana com correção inteira).
2. **Avalia 6 Heurísticas Construtivas**:
   - **3 Heurísticas Autorais**: 
     - Centroid-Based Insertion (H1)
     - Eccentricity Insertion (H2)
     - Hybrid-Score Insertion (H3)
   - **3 Heurísticas Clássicas da Literatura**:
     - Nearest Neighbor (H4)
     - Farthest Insertion (H5)
     - Greedy Edge (H6)
3. **Mede e Compara Desempenho**: Coleta tempo de execução computacional em milissegundos ($ms$) e custo final do circuito percorrido em 21 instâncias benchmark (48 a 200 nós).
4. **Visualização Estatística**: Gera gráficos estilo vela/boxplot com caso médio sobreposto, heatmaps comparativos (custo relativo e tempo de execução) e análise de dominância via Fronteira de Pareto.

---

## 2. Modelagem e Fórmulas de Distância

As coordenadas dos vértices $(x_i, y_i)$ são lidas e mantidas com precisão contínua em ponto flutuante (`float`). O cálculo das distâncias entre dois vértices $i$ e $j$ segue rigorosamente a especificação oficial da **TSPLIB**:

### 2.1. Distância Pseudo-Euclidiana (`ATT`)
Utilizada na instância `att48.tsp`:
$$\Delta x = x_i - x_j, \quad \Delta y = y_i - y_j$$
$$r_{ij} = \sqrt{\frac{\Delta x^2 + \Delta y^2}{10.0}}$$
$$t_{ij} = \text{nint}(r_{ij})$$
$$d_{ij} = \begin{cases} t_{ij} + 1, & \text{se } t_{ij} < r_{ij} \\ t_{ij}, & \text{caso contrário} \end{cases}$$
*Onde $\text{nint}(z) = \lfloor z + 0.5 \rfloor$.*

### 2.2. Distância Euclidiana 2D (`EUC_2D`)
Utilizada nas instâncias do diretório `EUC_2D/`:
$$d_{ij} = \text{nint}\left(\sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}\right)$$

---

## 3. Lógica e Motivação das 3 Heurísticas Autorais

Todas as três heurísticas autorais utilizam o princípio da **Inserção Mais Barata (*Cheapest Insertion*)** para posicionar os nós no circuito, minimizando o desvio local da rota:
$$\Delta(i, v, j) = d(i, v) + d(v, j) - d(i, j)$$

A inovação reside no critério de **ordenação global de inserção dos vértices**:

---

### H1 — Centroid-Based Insertion (Inserção Baseada em Centróide)
* **Motivação Geométrica**: Em problemas euclidianos, vértices localizados na periferia da nuvem de pontos têm poucas alternativas de arestas sem cruzar o interior do grafo. Se deixados para o final, inseri-los força o circuito a esticar arestas já consolidadas através de grandes distâncias, gerando cruzamentos graves. Ao construir primeiro o "esqueleto" ou envoltória externa dos nós periféricos, os vértices internos são posteriormente absorvidos com desvios locais mínimos.
* **Algoritmo**:
  1. Calcula o centróide médio das coordenadas:
     $$\mathbf{C} = \left(\frac{1}{n}\sum_{i=1}^n x_i, \; \frac{1}{n}\sum_{i=1}^n y_i\right)$$
  2. Atribui a prioridade de cada vértice $v$ como a distância ao centro:
     $$\text{prioridade}(v) = \text{dist}(v, \mathbf{C})$$
  3. Ordena todos os nós em ordem decrescente de prioridade.
  4. Inicia o circuito fechado com os 2 vértices mais distantes do centro e insere os demais sucessivamente via *cheapest insertion*.

---

### H2 — Eccentricity Insertion (Inserção por Excentricidade)
* **Motivação Topológica**: A heurística H1 depende da existência de coordenadas cartesianas $(X, Y)$. Para matrizes arbitrárias ou espaços não-euclidianos, o conceito de centróide perde o sentido. A excentricidade captura a noção de "periferia" puramente a partir da matriz de distâncias. Nós com maior soma total de distâncias estão na borda do grafo e devem ser fixados no circuito logo no início.
* **Algoritmo**:
  1. Calcula a excentricidade de cada vértice $v$:
     $$\text{exc}(v) = \sum_{u \in V, u \neq v} d(v, u)$$
  2. Define $\text{prioridade}(v) = \text{exc}(v)$.
  3. Ordena os vértices em ordem decrescente de excentricidade.
  4. Inicia com os 2 nós mais excêntricos e insere os restantes via *cheapest insertion*.

---

### H3 — Hybrid Insertion ($\alpha = \beta = 0.5$)
* **Motivação e Obrigatoriedade da Normalização**: Une a intuição espacial de H1 com a robustez topológica global de H2. A normalização Min-Max é **mandatória**, pois a distância ao centróide é de ordem linear $O(L)$, enquanto a excentricidade é um somatório de $n$ distâncias, de ordem $O(n \cdot L)$. Sem a normalização no intervalo $[0, 1]$, a excentricidade dominaria completamente o cálculo.
* **Algoritmo**:
  1. Normaliza ambas as grandezas para o intervalo $[0, 1]$:
     $$\text{norm}(X) = \frac{X - X_{\min}}{X_{\max} - X_{\min}}$$
  2. Calcula o score balanceado:
     $$\text{score}(v) = 0.5 \cdot \text{norm}(\text{dist}(v, \mathbf{C})) + 0.5 \cdot \text{norm}(\text{exc}(v))$$
  3. Ordena em ordem decrescente do score e insere via *cheapest insertion*.

---

## 4. Heurísticas da Literatura para Comparação

* **H4 — Nearest Neighbor (Rosenkrantz et al., 1977)**: Inicia em um vértice arbitrário e caminha iterativamente para o vizinho não visitado mais próximo ($O(n^2)$). É extremamente veloz, mas suscetível a fechamentos finais ruins.
* **H5 — Farthest Insertion (Christofides, 1976)**: Inicializa a rota com o par de vértices mais distantes entre si. A cada passo, seleciona o vértice não visitado cuja distância mínima à rota atual seja máxima ($\max \min d(k, r)$) e o insere na posição mais barata. Considerada uma das melhores heurísticas construtivas da literatura.
* **H6 — Greedy Edge (Bentley, 1992)**: Ordena todas as arestas por custo crescente e as adiciona iterativamente usando *Union-Find*, impedindo graus $\ge 3$ e subtours prematuros.

---

## 5. Resultados Numéricos Globais

Resumo estatístico consolidado nas 21 instâncias benchmark:

| Heurística | Custo Médio Absoluto | Custo Médio Relativo | Tempo Médio ($ms$) | Desempenho / Análise |
| :--- | :---: | :---: | :---: | :--- |
| **H5 (Farthest Insertion)** | **35.429** | **1.002x** | 5.56 ms | **Melhor qualidade média de rota** |
| **H1 (Centroid-Based)** | **36.292** | **1.038x** | **3.35 ms** | **Melhor custo-benefício (Fronteira de Pareto)** |
| **H2 (Eccentricity)** | 36.335 | 1.038x | 4.90 ms | Soluções de alta qualidade, agnóstica a coordenadas |
| **H3 (Hybrid-Score)** | 36.395 | 1.039x | 4.95 ms | Alta robustez combinada |
| **H6 (Greedy Edge)** | 39.437 | 1.097x | 4.77 ms | Qualidade intermediária |
| **H4 (Nearest Neighbor)** | 41.117 | 1.161x | **1.19 ms** | **Mais rápida, porém rotas ~16% piores** |

---

## 6. Explicação dos Gráficos Gerados

Os gráficos consolidados encontram-se salvos no diretório `graficos/`:

### 6.1. Heatmap de Qualidade da Solução (`graficos/heatmap_custo_relativo.png`)
* **O que representa**: Matriz cruzando as 21 instâncias (linhas, ordenadas da menor para a maior em número de nós) com as 6 heurísticas (colunas).
* **Métrica**: Custo Relativo normalizado pelo melhor resultado obtido naquela instância ($1.000$ = vitória/ótimo encontrado).
* **Interpretação**:
  - Mostra que **H5** obtém $1.000$ na grande maioria das instâncias.
  - As autorais **H1, H2 e H3** operam estavelmente entre $1.01$ e $1.05$ (apenas $1\%$ a $5\%$ de gap em relação ao melhor método), superando com ampla folga o *Nearest Neighbor* (H4) e o *Greedy Edge* (H6).

### 6.2. Heatmap de Tempo Computacional (`graficos/heatmap_tempo_execucao.png`)
* **O que representa**: O tempo de CPU em milissegundos ($ms$) gasto por cada heurística para resolver cada instância individualmente.
* **Interpretação**:
  - Revela a escalabilidade polinomial dos métodos conforme $n$ cresce de 48 para 200 vértices.
  - **H1** demonstra vantagem consistente de velocidade sobre H2, H3 e H5 nas instâncias maiores, pois o cálculo do centróide tem custo linear $O(n)$, enquanto o farthest insertion e a excentricidade demandam operações contínuas de ordem quadrática.

### 6.3. Boxplot / Estilo Vela com Caso Médio de Custo (`graficos/boxplot_custo_relativo.png`)
* **O que representa**: A distribuição estatística do custo relativo de cada heurística.
* **Componentes**:
  - **Caixa**: Delimitada pelo Primeiro Quartil (Q1 - 25%) e Terceiro Quartil (Q3 - 75%), com a linha central indicando a **Mediana**.
  - **Whiskers (Hastes)**: Estendem-se do mínimo real ao máximo real observado nos testes.
  - **Linha Laranja com Diamantes (Caso Médio)**: Média aritmética sobreposta explicitamente à vela.
* **Interpretação**: Evidencia a consistência de H1, H2 e H3 (caixas muito estreitas em torno de $1.038$), em contraste com a alta variabilidade e dispersão de H4.

### 6.4. Boxplot com Caso Médio de Tempo (`graficos/boxplot_tempo_execucao.png`)
* **O que representa**: A distribuição estatística dos tempos de execução em milissegundos.
* **Interpretação**: Ilustra como H1 economiza tempo de máquina em relação a H5 e H2 mantendo qualidade praticamente idêntica.

### 6.5. Fronteira de Pareto Multiobjetivo (`graficos/fronteira_pareto.png`)
* **O que representa**: O trade-off entre **Custo Relativo Médio** ($X$) e **Tempo Médio de Execução** ($Y$).
* **Soluções Não Dominadas (Fronteira de Pareto)**:
  - **H4 (Nearest Neighbor)**: Solução não dominada em latência pura ($1.19$ ms).
  - **H1 (Centroid-Based)**: Ponto de inflexão ótimo da curva: entrega rotas com qualidade quase idêntica à de H5 gastando quase metade do tempo computacional ($3.35$ ms vs $5.56$ ms).
  - **H5 (Farthest Insertion)**: Solução não dominada em qualidade pura de rota ($1.002\times$).
  - As heurísticas H2, H3 e H6 situam-se no interior dominado pela fronteira em média.

---

## 7. Como Reproduzir os Experimentos (Guia Passo a Passo)

Para quem acabou de clonar ou baixar o projeto do zero:

### Pré-requisitos
- **Python 3.10+** instalado no sistema.

### Passo 1: Abrir o terminal no diretório do projeto
```bash
cd heu_e_met_tsp_instances
```

### Passo 2: Criar e ativar um ambiente virtual (`venv`)
- **No Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **No Linux / macOS (Bash):**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Passo 3: Instalar as dependências necessárias
Instale os pacotes listados em `requirements.txt` (`matplotlib`, `pandas`, `numpy`, `seaborn`):
```bash
pip install -r requirements.txt
```

### Passo 4: Executar a simulação completa
```bash
python tsp_framework.py
```

### Saídas Geradas Automaticamente:
- **Tabelas de dados**: Salvas em `resultados/metricas_tsp.csv` e `resultados/resumo_heurísticas.csv`.
- **Gráficos estatísticos**: Salvos na pasta `graficos/`:
  - `heatmap_custo_relativo.png`
  - `heatmap_tempo_execucao.png`
  - `boxplot_custo_relativo.png`
  - `boxplot_tempo_execucao.png`
  - `fronteira_pareto.png`

---
---

# 🇺🇸 Technical Report: Traveling Salesman Problem (TSP) Constructive Heuristics

## 1. Project Overview

The Traveling Salesman Problem (TSP) asks for the minimum-cost Hamiltonian cycle visiting every node in a graph exactly once and returning to the origin. Being NP-Hard, exact methods become computationally intractable as instance sizes grow, requiring polynomial-time **constructive heuristics** capable of delivering high-quality solutions.

This project implements an extensible Python framework that:
1. **Parses Standard TSPLIB Instances**: Supports edge weight types **EUC_2D** (2D Euclidean distances) and **ATT** (pseudo-Euclidean distances with integer rounding).
2. **Evaluates 6 Constructive Heuristics**:
   - **3 Authorial/Novel Heuristics**:
     - Centroid-Based Insertion (H1)
     - Eccentricity Insertion (H2)
     - Hybrid-Score Insertion (H3)
   - **3 Classical Literature Heuristics**:
     - Nearest Neighbor (H4)
     - Farthest Insertion (H5)
     - Greedy Edge (H6)
3. **Benchmarks Execution Time & Tour Cost**: Measures CPU execution time in milliseconds ($ms$) and total cycle distance across 21 benchmark instances (48 to 200 nodes).
4. **Statistical Visualization**: Produces candlestick/boxplot charts with overlaid mean cases, comparative heatmaps (relative cost and execution time), and Pareto Frontier dominance analysis.

---

## 2. Distance Modeling & Formulations

Node coordinates $(x_i, y_i)$ are parsed and preserved with floating-point precision (`float`). Edge distance calculations strictly follow the **TSPLIB** official specification:

### 2.1. Pseudo-Euclidean Distance (`ATT`)
Used in `att48.tsp`:
$$\Delta x = x_i - x_j, \quad \Delta y = y_i - y_j$$
$$r_{ij} = \sqrt{\frac{\Delta x^2 + \Delta y^2}{10.0}}$$
$$t_{ij} = \text{nint}(r_{ij})$$
$$d_{ij} = \begin{cases} t_{ij} + 1, & \text{if } t_{ij} < r_{ij} \\ t_{ij}, & \text{otherwise} \end{cases}$$
*Where $\text{nint}(z) = \lfloor z + 0.5 \rfloor$.*

### 2.2. 2D Euclidean Distance (`EUC_2D`)
Used in all instances within the `EUC_2D/` directory:
$$d_{ij} = \text{nint}\left(\sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}\right)$$

---

## 3. Logic & Rationale of the 3 Authorial Heuristics

All three proposed heuristics employ the **Cheapest Insertion** step to locate the optimal position for a node within the current closed tour:
$$\Delta(i, v, j) = d(i, v) + d(v, j) - d(i, j)$$

The novelty lies in the **global prioritization order** in which vertices are inserted:

---

### H1 — Centroid-Based Insertion
* **Geometric Motivation**: In Euclidean spaces, vertices on the outer boundary of the point cloud have very limited routing flexibility without crossing through the center. Leaving peripheral nodes for the end forces long detour edges that slice across established tours. Building the outer structural "hull" first allows interior vertices to be smoothly integrated later with minimal local distortion.
* **Algorithm**:
  1. Compute geometric centroid coordinates:
     $$\mathbf{C} = \left(\frac{1}{n}\sum_{i=1}^n x_i, \; \frac{1}{n}\sum_{i=1}^n y_i\right)$$
  2. Assign vertex priority as distance to the centroid:
     $$\text{priority}(v) = \text{dist}(v, \mathbf{C})$$
  3. Sort all nodes in descending order of priority.
  4. Initialize the closed cycle with the 2 most peripheral nodes and insert remaining vertices via *cheapest insertion*.

---

### H2 — Eccentricity Insertion
* **Topological Motivation**: H1 relies on explicit Cartesian $(X, Y)$ coordinates. For general distance matrices or non-Euclidean spaces, geometric centroids are undefined. Node eccentricity measures centrality purely using graph distances: nodes with higher total distance sums are topologically peripheral and should be seeded first.
* **Algorithm**:
  1. Compute vertex eccentricity:
     $$\text{exc}(v) = \sum_{u \in V, u \neq v} d(v, u)$$
  2. Assign $\text{priority}(v) = \text{exc}(v)$.
  3. Sort nodes in descending eccentricity.
  4. Initialize with the 2 most eccentric nodes and insert remaining nodes via *cheapest insertion*.

---

### H3 — Hybrid Insertion ($\alpha = \beta = 0.5$)
* **Motivation & Min-Max Normalization**: Combines the explicit spatial awareness of H1 with the global graph distance structure of H2. Min-Max normalization is **mandatory**: centroid distances scale linearly $O(L)$, while eccentricity is a sum of $n$ distances scaling as $O(n \cdot L)$. Without normalizing both features into $[0, 1]$, eccentricity would overwhelmingly dominate the score.
* **Algorithm**:
  1. Normalize both metrics into $[0, 1]$:
     $$\text{norm}(X) = \frac{X - X_{\min}}{X_{\max} - X_{\min}}$$
  2. Compute balanced priority score:
     $$\text{score}(v) = 0.5 \cdot \text{norm}(\text{dist}(v, \mathbf{C})) + 0.5 \cdot \text{norm}(\text{exc}(v))$$
  3. Sort descending by score and insert via *cheapest insertion*.

---

## 4. Literature Benchmark Heuristics

* **H4 — Nearest Neighbor (Rosenkrantz et al., 1977)**: Starts at an initial node and greedily transitions to the closest unvisited neighbor ($O(n^2)$). Fast, but suffers severely from catastrophic closing edges.
* **H5 — Farthest Insertion (Christofides, 1976)**: Starts with the mutually farthest pair. Iteratively picks the unvisited vertex maximizing the minimum distance to the current tour ($\max \min d(k, r)$) and inserts it via cheapest insertion. Widely considered one of the top constructive heuristics for TSP.
* **H6 — Greedy Edge (Bentley, 1992)**: Sorts all edges by ascending cost and incorporates them using *Union-Find*, preventing node degrees $\ge 3$ and premature subtours.

---

## 5. Global Benchmark Results

Summary statistics across all 21 benchmark instances:

| Heuristic | Mean Absolute Cost | Mean Relative Cost | Mean CPU Time ($ms$) | Performance Summary |
| :--- | :---: | :---: | :---: | :--- |
| **H5 (Farthest Insertion)** | **35,429** | **1.002x** | 5.56 ms | **Best solution quality** |
| **H1 (Centroid-Based)** | **36,292** | **1.038x** | **3.35 ms** | **Best trade-off (Pareto Frontier)** |
| **H2 (Eccentricity)** | 36,335 | 1.038x | 4.90 ms | High quality, coordinate-agnostic |
| **H3 (Hybrid-Score)** | 36,395 | 1.039x | 4.95 ms | Balanced and robust |
| **H6 (Greedy Edge)** | 39,437 | 1.097x | 4.77 ms | Intermediate quality |
| **H4 (Nearest Neighbor)** | 41,117 | 1.161x | **1.19 ms** | **Fastest, but tours are ~16% worse** |

---

## 6. Generated Visualizations Guide

All charts are saved in the `graficos/` directory:

### 6.1. Solution Quality Heatmap (`graficos/heatmap_custo_relativo.png`)
* Matrix of 21 instances (rows, ordered by node count) vs 6 heuristics (columns).
* Metric: Relative Cost normalized against the instance best ($1.000$ = optimal among tested heuristics).
* Demonstrates that H1, H2, and H3 consistently achieve $1.01$ to $1.05$, substantially outperforming Nearest Neighbor (H4) and Greedy Edge (H6).

### 6.2. Execution Time Heatmap (`graficos/heatmap_tempo_execucao.png`)
* CPU runtime in milliseconds ($ms$) per instance-heuristic combination.
* Displays polynomial scaling up to $n=200$. H1 is markedly faster than H5 and H2 on larger graphs due to its $O(n)$ centroid preprocessing step.

### 6.3. Relative Cost Candlestick/Boxplot (`graficos/boxplot_custo_relativo.png`)
* Statistical distribution of relative costs (Q1, Median, Q3, Min, Max, and overlaid Mean Case in orange).
* Highlights the tight confidence intervals and predictability of H1, H2, and H3 compared to the high variance of H4.

### 6.4. Execution Time Candlestick/Boxplot (`graficos/boxplot_tempo_execucao.png`)
* Distribution of computation times showing H1's significant speed advantage over H5 and H2.

### 6.5. Multi-Objective Pareto Frontier (`graficos/fronteira_pareto.png`)
* Trade-off between **Mean Relative Cost** ($X$) and **Mean Runtime** ($Y$).
* **Non-Dominated Solutions (Pareto Set)**:
  - **H4**: Pure low-latency choice ($1.19$ ms).
  - **H1**: Ideal elbow point (almost identical quality to H5 in nearly half the computation time).
  - **H5**: Pure solution-quality choice ($1.002\times$).

---

## 7. How to Reproduce Experiments (Step-by-Step Guide)

For fresh repository clones:

### Prerequisites
- **Python 3.10+**

### Step 1: Open terminal in project root
```bash
cd Heuristicas-TSP
```

### Step 2: Create and activate a virtual environment (`venv`)
- **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **Linux / macOS (Bash):**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install required dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the benchmarking simulation
```bash
python tsp_heuristics_framework.py
```

All CSV metric tables in `resultados/` and visual plots in `graficos/` will be regenerated automatically.
