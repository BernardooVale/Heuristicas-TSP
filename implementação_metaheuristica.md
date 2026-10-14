# Mapeamento de Metaheurísticas e Abordagens para o Problema do Caxeiro Viajante (TSP)

> *Baseado no Capítulo 8 do livro "Local Search in Combinatorial Optimization" (David S. Johnson & Lyle A. McGeoch)*

---

## 1. Visão Geral & Propósito do Documento

Este documento mapeia os conceitos, estruturas de dados vitais, mecanismos de busca e trade-offs algorítmicos das heurísticas e metaheurísticas aplicadas ao **Travelling Salesman Problem (TSP)** apresentadas no Capítulo 8. O objetivo é servir como uma referência conceitual clara para que um agente autônomo ou sistema de software possa projetar, selecionar e adaptar implementações eficientes do TSP.

---

## 2. Busca Local Clássica e Vizinhanças de Troca (2-Opt, 3-Opt e Variantes)

### 2.1 Módulos Fundamentais de Vizinhança

- **2-Opt**: Seleciona duas arestas distintas da rota $(t_1, t_2)$ e $(t_4, t_3)$, remove-as e reconecta invertendo o subcaminho intermediário para formar uma nova rota válida. Em instâncias euclidianas planas, este movimento elimina cruzamentos de arestas.
- **3-Opt**: Remove até três arestas da rota e avalia as 8 possíveis reconexões dos três segmentos resultantes (1 é a rota original e 7 representam reconfigurações e/ou inversões de sub-rotas).

### 2.2 Variantes e Extensões da Vizinhança

- **2.5-Opt (Bentley)**: Expande o 2-Opt ao avaliar a realocação de uma única cidade $t_3$ para uma posição entre dois vizinhos $t_1$ e $t_2$ em outra parte da rota. Oferece cerca de 50% do ganho de qualidade do 3-Opt com custo computacional reduzido (cerca de 30-40% mais lento que o 2-Opt simples).
- **Or-Opt (Or)**: Restringe os movimentos do 3-Opt à remoção de pequenos segmentos contínuos (1, 2 ou 3 cidades consecutivas) e sua reinserção entre vizinhos em outro ponto do tour. É uma generalização do 2.5-Opt.
- **4-Opt e Movimento Double-Bridge**:
  - Remove 4 arestas, dividindo a rota em 4 segmentos em ordem: $A_1, A_2, A_3, A_4$.
  - O movimento **Double-Bridge** altera a ordem para $A_1, A_4, A_3, A_2$ sem inverter a orientação de nenhum dos 4 segmentos.
  - **Propriedade Chave**: É um movimento *não-sequencial*. Não pode ser decomposto em uma sequência de trocas 2-Opt ou 3-Opt melhorantes. Por essa razão, é o operador de perturbação/mutação ideal para escapar de mínimos locais sem destruir a estrutura global da rota.
- **Dynasearch**: Utiliza programação dinâmica para identificar e aplicar simultaneamente um conjunto de movimentos 2-Opt ou 2.5-Opt mutuamente independentes (cidades não sobrepostas) em um único passo de otimização.

### 2.3 Técnicas de Aceleração e Poda de Vizinhança (Obrigatórias em Implementações)

Sem aceleração, a busca $k$-Opt exige tempo $O(N^k)$. Para atingir tempo subquadrático $o(N^2)$ na prática:

1. **Listas de Vizinhos ($k$-Nearest Neighbor Lists)**:
   - Para cada cidade $c$, mantém-se uma lista ordenada com suas $k$ cidades mais próximas (tipicamente $k=20$). A busca por candidatos a troca limita-se a essa vizinhança restrita.
2. **Don't-Look Bits**:
   - Um bit booleano é mantido para cada cidade. Se nenhuma aresta incidente na cidade $c$ foi alterada nas buscas recentes, seu bit é ativado (1) e ela é ignorada em verificações subsequentes. Quando uma troca altera as arestas de $c$, o bit das suas vizinhas é resetado para (0).
3. **Restrição "One-Tree" (Gain Criterion)**:
   - Restringe os candidatos $t_i$ exigindo que o ganho parcial acumulado ao longo da sequência de trocas seja mantido positivo em cada etapa intermediária.

---

## 3. Tabu Search e o Algoritmo de Lin-Kernighan (LK)

### 3.1 Tabu Search Simples no TSP

- **Mecanismo de Busca**: Permite movimentos de piora (*uphill moves*) quando preso em um mínimo local, selecionando o melhor vizinho não-tabu.
- **Memória Tabu**: Registra atributos de movimentações recentes (ex.: arestas deletadas, inseridas ou pares de arestas) em uma fila FIFO durante $T$ iterações, proibindo sua reintrodução.
- **Critério de Aspiração**: Sobrescreve o bloqueio tabu se o movimento produzir uma rota melhor do que a melhor solução já encontrada no histórico (*global best*).
- **Desempenho**: Implementações diretas de Tabu Search puro em 2-Opt ou 3-Opt exigem $O(N^2)$ por iteração e até $O(N^3)$ a $O(N^4)$ no total, tornando-se lentas sem uma arquitetura híbrida ou paralelização.

### 3.2 Algoritmo de Lin-Kernighan (LK) - A Busca Local de Profundidade Variável

- **Conceito de Vizinhança Variável**: Em vez de fixar $k$, o algoritmo constrói dinamicamente uma sequência de trocas de arestas $k$-Opt de profundidade arbitrária em um único passo de busca.
- **Estrutura de Busca LK**:
  - Trata a solução temporária como um *Caminho Hamiltoniano Ancorado* com um extremo fixo $t_1$ e um extremo móvel $t_{2i}$.
  - Realiza operações de "rotação" no caminho mantendo a condição de ganho positivo acumulado (*one-tree condition*).
  - **Mecanismo Tabu Nativo**: Durante uma mesma busca LK, arestas que foram adicionadas não podem ser deletadas e arestas deletadas não podem ser adicionadas. Não há limites de tamanho ou níveis de aspiração externos.
- **Reinício por Intensificação (Champion Tour)**:
  - Mantém uma rota "campeã" (*champion tour*). Novas buscas LK são iniciadas sistematicamente a partir de variações 3-Opt/4-Opt derivadas da rota campeã atual.
- **Desempenho**: Atinge rotas a cerca de $1.5\%$ do limite de Held-Karp em tempo subquadrático, processando instâncias de até 1.000.000 de cidades em menos de uma hora em implementações otimizadas.

---

## 4. Simulated Annealing (SA) e Suas Variantes

### 4.1 Estrutura Geral do Annealing

- **Regra de Aceitação Estocástica**:
  - Movimentos que melhoram a rota ($\Delta \le 0$) são sempre aceitos.
  - Movimentos que pioram a rota ($\Delta > 0$) são aceitos com probabilidade $P = e^{-\Delta / T}$, onde $T$ é o parâmetro de temperatura.
- **Cooling Schedule (Esquema de Resfriamento)**: A temperatura diminui gradualmente ($T_{k+1} = \alpha \cdot T_k$, com $\alpha \approx 0.95 - 0.99$).

### 4.2 Otimizações Cruciais para Viabilidade Prática

- **Início em Baixa Temperatura (Low-Temperature Starts)**:
  - Iniciar o SA em temperaturas altas a partir de rotas aleatórias destrói qualquer estrutura de boa qualidade. A abordagem otimizada parte de rotas de boa qualidade (via Greedy/Nearest Neighbor) e inicia o resfriamento a uma temperatura reduzida.
- **Poda Dinâmica de Vizinhança (Dynamic Pruning)**:
  - À medida que $T$ diminui, restringe a busca de candidatos $t_3$ apenas a cidades para as quais a probabilidade de aceitação $e^{-\Delta / T}$ seja maior que um limiar mínimo (ex.: $0.01$).
- **Geração Permutada de Movimentos**:
  - Substitui a amostragem aleatória pura de vizinhos por varreduras em listas permutadas sem reposição a cada temperatura, reduzindo redundâncias.
- **Variantes Determinísticas baseadas em Limiares**:
  - **Great Deluge Algorithm (GDA)**: Substitui a probabilidade por um nível de "água" $W$ que desce monotonicamente. Aceita qualquer movimento cuja rota resultante não ultrapasse $W$.
  - **Record-to-Record Travel (RTR)**: Aceita pioras desde que o comprimento da nova rota não exceda o recorde atual somado a uma margem de tolerância que diminui ao longo da execução.
  - **Threshold Accepting (TA)**: Aceita um movimento pior se $\Delta \le \text{Threshold}(T)$.

---

## 5. Algoritmos Genéticos (GA) e Iterated Lin-Kernighan (ILK)

### 5.1 Estrutura de Algoritmos Genéticos para o TSP

- **Representação**: Vetor de permutação (caminho).
- **Mapeamento de Crossover**:
  - *Heuristic Crossover*: Constrói a rota do filho escolhendo a cada passo a aresta mais curta entre as presentes nos dois pais a partir da cidade atual.
  - *Subpath Crossover (Mühlenbein)*: Copia um subcaminho contínuo de um pai (doador) e estende o restante da rota favorecendo arestas do outro pai (receptor).
- **Importância da Busca Local**: A aplicação de busca local (2-Opt/3-Opt/LK) após os operadores de cruzamento/mutação é fundamental. GAs sem busca local performam mal no TSP.

### 5.2 Iterated Lin-Kernighan (ILK) / Chained Local Optimization

- **Conceito Partenogenético**: É uma metaheurística evolutiva com população de tamanho 1, combinando perturbação e busca local em cadeia.
- **Fluxo do Algoritmo por Iteração**:
  1. **Mutação (Perturbação)**: Aplica um movimento **Double-Bridge 4-Opt** aleatório sobre a solução corrente $S$.
  2. **Busca Local Otimizada (LK)**: Executa a busca Lin-Kernighan sobre a solução alterada.
     - *Otimização Crítica de Fila Ativa*: A fila de cidades ativas para início da busca LK é inicializada **apenas** com as 8 cidades diretamente afetadas pela mutação Double-Bridge. Isso reduz drasticamente o tempo de cada iteração.
  3. **Critério de Aceitação**: Se a rota otimizada $S'$ for melhor ou igual a $S$, faz-se $S = S'$. Caso contrário, descarta-se $S'$ e tenta-se uma nova perturbação.
- **Desempenho**: É a metaheurística mais eficiente do capítulo. Alcança soluções entre $0.2\%$ e $0.5\%$ do ótimo em tempo subquadrático, sendo a escolha recomendada para implementação de ponta.

### 5.3 Abordagens Multiparentais e Branch-Width

- **União de Arestas**: Coleta a união de arestas das melhores rotas geradas por múltiplas execuções de ILK. O grafo resultante é muito esparso.
- **Otimização Exata via Branch-Width**: Se o subgrafo possui *branch-width* delimitado, aplica-se programação dinâmica para encontrar o tour ótimo **restrito às arestas do grafo**, superando a qualidade do ILK em instâncias muito difíceis.

---

## 6. Redes Neurais Artificialmente Aplicadas ao TSP

### 6.1 Modelos baseados em Programação Inteira (Hopfield-Tank / Potts)

- **Conceito**: Mapeia o problema em $N^2$ neurônios $x_{ik}$ (cidade $i$ na posição $k$). Uma função de energia penaliza violações de factibilidade e minimiza a distância total.
- **Problemas Práticos**: Mapeamentos diretos falham com frequência em produzir rotas válidas para $N > 30$. Alta sensibilidade a parâmetros de ajuste e alto custo computacional ($\Omega(N^3)$ a $\Omega(N^4)$ em simulação sequencial).

### 6.2 Redes Neurais Geométricas (Elastic Nets e SOM)

- **Elastic Nets (Durbin & Willshaw)**: Uma cadeia fechada de pontos elásticos no plano geométrico é iterativamente atraída pelas cidades através de dinâmica de campo médio, deformando-se até se alinhar aos vértices das cidades.
- **Self-Organizing Maps (SOM / Kohonen)**: Um anel de neurônios ajusta seus pesos em rodadas competitivas para se aproximar de cidades selecionadas aleatoriamente.
- **Avaliação Geral**: Redes neurais puras não superam a qualidade nem o tempo do 2-Opt ou 3-Opt simples. Contudo, a lógica de deformação geométrica pode ser adaptada como geradora de rotas iniciais ou em problemas com restrições contínuas de sensores.

---

## 7. Matriz Comparativa e Diretrizes de Arquitetura para Agentes

| Abordagem | Qualidade Relativa (Excess vs Held-Karp) | Complexidade Computacional Prática | Complexidade de Código | Recomendação de Arquitetura |
| :--- | :--- | :--- | :--- | :--- |
| **2-Opt (com Neighbor Lists)** | $\approx 4.5\% - 5.0\%$ | $o(N^2)$ subquadrático | Baixa | Baseline rápido para otimização inicial. |
| **3-Opt (com Neighbor Lists)** | $\approx 2.5\% - 3.0\%$ | $o(N^2)$ subquadrático | Média | Excelente equilíbrio custo/benefício sem LK. |
| **Lin-Kernighan (LK)** | $\approx 1.5\%$ | $o(N^2)$ subquadrático | Alta | Otimizador local de alta performance. |
| **Simulated Annealing (SA2/SA3)** | $\approx 1.1\% - 1.5\%$ | Subquadrático (com poda) | Média | Alternativa metaheurística quando LK não estiver disponível. |
| **Iterated Lin-Kernighan (ILK)** | $\approx 0.2\% - 0.5\%$ | Subquadrático | Média-Alta | **Estado da arte prática para alta precisão e desempenho.** |
| **Redes Neurais (Hopfield/Elastic)** | $> 5.0\% - 10.0\%$ | $O(N^3) - O(N^4)$ | Média-Alta | Não recomendado para solvers gerais de TSP. |

### Diretrizes de Implementação para Agentes Autônomos

1. **Pilar Fundamental (Infraestrutura)**: Toda implementação deve obrigatoriamente construir **$k$-Nearest Neighbor Lists** ($k=20$) e manter **Don't-Look Bits** antes de rodar os loops de otimização.
2. **Padrão Recomendado (Pipeline em 3 Camadas)**:
   - **Camada 1 (Rota Inicial)**: Algoritmo Greedy ou Nearest Neighbor ($O(N \log N)$ com neighbor lists).
   - **Camada 2 (Busca Local Base)**: Lin-Kernighan ou 3-Opt.
   - **Camada 3 (Metaheurística de Perturbação)**: Iterated Lin-Kernighan (ILK) com perturbação **Double-Bridge 4-Opt** reativando apenas as 8 cidades modificadas.