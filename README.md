# Flowshop Analyzer

Ferramenta híbrida em **C++20** e **Python** para resolução, benchmark e visualização de heurísticas aplicadas ao **Permutation Flowshop Scheduling Problem (PFSP)** utilizando instâncias clássicas da OR-Library (`instancias.txt`).

Esta ferramenta foi criada para a apresentação da disciplina de Complexidade e Algoritmos, do prof. dr. Luis Henrique Sacchi, do IFSP — Campus Salto, no ano de 2026.

**Integrantes:**

- Eduardo Martins Corrêa
- Fábio Haruo de Freitas Nishioka
- Seren Iketani
- Yasmin Sampieri Tonello Cury

## Estrutura do Projeto

```text
flowshop-analyzer/
├── Makefile
├── pyproject.toml
├── instancias.txt
├── apps/
│   └── main.cpp                      # Executável C++ independente
├── include/
│   └── flowshop_analyzer/
│       ├── solver_api.h              # Interface C ABI para integração via ctypes
│       └── tabu_search.hpp           # Declarações das variantes de Busca Tabu
├── src/
│   ├── solver_api.cpp                # Despachante de algoritmos e conversão FFI
│   ├── tabu_search.cpp               # Busca Tabu com vizinhança de inserção (tabu_original)
│   ├── tabu_optimized.cpp            # Busca Tabu com reutilização de scratch buffers (tabu_optimized)
│   └── tabu_neh.cpp                  # Busca Tabu com solução inicial via heurística NEH (tabu_neh)
├── python/
│   └── src/
│       └── flowshop_analyzer/
│           ├── __init__.py
│           ├── _ffi.py               # Bindings ctypes para a biblioteca compartilhada C++
│           ├── parser.py             # Leitor das instâncias no formato OR-Library
│           ├── plotting.py           # Geração de curvas de convergência e gráficos de Gantt
│           └── cli.py                # Interface de linha de comando (Typer + Rich)
└── tests/
    └── test_solver.py                # Suíte de testes automatizados com pytest
```

## Algoritmos Disponíveis

- **`tabu_original`**: Busca Tabu baseada em vizinhança de inserção clássica com solução inicial sequencial ($0 \dots N-1$).
- **`tabu_optimized`**: Variante com comportamento determinístico e desempate idênticos a `tabu_original`, porém eliminando alocações dinâmicas de memória (heap) no laço interno por meio de reutilização de buffers pré-alocados.
- **`tabu_neh`**: Variante que constrói a solução inicial através da heurística clássica NEH (ordenação decrescente de tempo total de processamento seguida de inserções parciais gulosas) e, em seguida, executa o laço de Busca Tabu otimizado.

## Pré-requisitos

- **Compilador C++20 (`g++`) e `make`:**
    - **Linux (Ubuntu/Debian):** `sudo apt install build-essential`
    - **Windows:** Instale o [MSYS2](https://www.msys2.org/) (com `mingw-w64-ucrt-x86_64-gcc` e `make`) e adicione o diretório `bin` ao `PATH`.
- **Python 3.11+ e `uv`:**
    - Siga as instruções oficiais de instalação do [uv](https://docs.astral.sh/uv/getting-started/installation/).

## Instalação e Compilação

1. Clone o repositório e acesse a pasta do projeto:

```bash
git clone <url-do-repositorio>
cd flowshop-analyzer
```

2. Compile a biblioteca compartilhada C++ (`libflowshop.so` no Linux, `libflowshop.dylib` no macOS ou `libflowshop.dll` no Windows) e o executável nativo:

```bash
make
```

3. Crie o ambiente virtual e instale as dependências Python (incluindo dependências de desenvolvimento):

```bash
uv sync
```

## Como Usar

### 1. Listar instâncias disponíveis

Exibe todas as 31 instâncias carregadas de `instancias.txt` (`car1`–`car8`, `hel1`–`hel2` e `reC01`–`reC41`), com número de tarefas ($N$) e máquinas ($M$):

```bash
uv run flowshop-analyzer list-instances
```

### 2. Resolver uma instância e gerar gráficos

Executa a Busca Tabu para uma instância específica, permitindo comparar diferentes algoritmos ou valores de _Tabu Tenure_ na mesma curva de convergência e exportar o gráfico de Gantt do melhor escalonamento encontrado:

```bash
uv run flowshop-analyzer solve car1 -a tabu_original -a tabu_neh -t 0 -i 300 -o plots/car1_tenures.png -g plots/car1_gantt.png
```

### 3. Executar benchmark completo e exportar para CSV

Avalia o desempenho e o makespan ($C_{\max}$) em todas as 31 instâncias do arquivo, com suporte à comparação direta entre algoritmos e exportação de métricas via `--csv`:

```bash
# Benchmark de um único algoritmo
uv run flowshop-analyzer benchmark -a tabu_optimized -i 300 -c benchmark_single.csv

# Comparação entre múltiplos algoritmos com cálculo de speedup relativo
uv run flowshop-analyzer benchmark -a tabu_original -a tabu_optimized -a tabu_neh -i 300 -c benchmark_comparison.csv
```

### 4. Executar os testes automatizados

Para rodar a suíte completa de testes com o `pytest`:

```bash
uv run pytest
```

Para saída detalhada:

```bash
uv run pytest -v
```

### 5. Executar o binário C++ puro (opcional)

Caso queira rodar a implementação C++ diretamente sem a camada Python:

```bash
# Linux / macOS
./build/bin/flowshop_runner

# Windows
.\build\bin\flowshop_runner.exe
```

## Referência de Parâmetros da CLI

### Comando `solve`

| Opção          | Abreviação | Descrição                                                                            | Padrão           |
| :------------- | :--------- | :----------------------------------------------------------------------------------- | :--------------- |
| `--file`       | `-f`       | Caminho para o arquivo de instâncias da OR-Library                                   | `instancias.txt` |
| `--algo`       | `-a`       | Algoritmo(s) a executar (`tabu_original`, `tabu_optimized`, `tabu_neh`)             | `tabu_original`  |
| `--tenure`     | `-t`       | Tamanho da lista tabu (`0` = automático $\max(5, \lfloor 10N/11 \rfloor)$)           | `0`              |
| `--iterations` | `-i`       | Número máximo de iterações da Busca Tabu                                             | `300`            |
| `--output`     | `-o`       | Caminho para salvar o gráfico de convergência (`.png`)                               | Nenhum           |
| `--gantt`      | `-g`       | Caminho para salvar o gráfico de Gantt por máquina (`.png`)                          | Nenhum           |

### Comando `benchmark`

| Opção          | Abreviação | Descrição                                                                            | Padrão           |
| :------------- | :--------- | :----------------------------------------------------------------------------------- | :--------------- |
| `--file`       | `-f`       | Caminho para o arquivo de instâncias da OR-Library                                   | `instancias.txt` |
| `--algo`       | `-a`       | Algoritmo(s) a comparar (`tabu_original`, `tabu_optimized`, `tabu_neh`, repetível)   | `tabu_original`  |
| `--tenure`     | `-t`       | Tamanho da lista tabu (`0` = automático)                                             | `0`              |
| `--iterations` | `-i`       | Número máximo de iterações por instância                                             | `300`            |
| `--csv`        | `-c`       | Caminho para salvar a tabela completa de métricas em formato CSV (`.csv`)            | Nenhum           |
