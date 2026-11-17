# Flowshop Analyzer

Ferramenta híbrida em **C++20** e **Python** para resolução, benchmark e visualização de heurísticas aplicadas ao **Permutation Flowshop Scheduling Problem (PFSP)** utilizando instâncias clássicas da OR-Library (`instancias.txt`).

Esta ferrameta foi criada para a apresentação da disciplina de Complexidade e Algoritmos, do prof. dr. Luis Henrique Sacchi, do IFSP — Campus Salto, no ano de 2026.

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
│       └── tabu_search.hpp           # Cabeçalho nativo da Busca Tabu
├── src/
│   ├── solver_api.cpp                # Despachante de algoritmos e conversão FFI
│   └── tabu_search.cpp               # Implementação da Busca Tabu (vizinhança de inserção)
└── python/
    └── src/
        └── flowshop_analyzer/
            ├── __init__.py
            ├── _ffi.py               # Bindings ctypes para a biblioteca compartilhada C++
            ├── parser.py             # Leitor das instâncias no formato OR-Library
            ├── plotting.py           # Geração de curvas de convergência e gráficos de Gantt
            └── cli.py                # Interface de linha de comando (Typer + Rich)
```

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

3. Crie o ambiente virtual e instale as dependências Python:

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

Executa a Busca Tabu para uma instância específica, permitindo comparar diferentes valores de _Tabu Tenure_ na mesma curva de convergência e exportar o gráfico de Gantt do melhor escalonamento encontrado:

```bash
uv run flowshop-analyzer solve car1 -t 5 -t 15 -t 0 -i 300 -o plots/car1_tenures.png -g plots/car1_gantt.png
```

### 3. Executar benchmark completo

Avalia o desempenho e o makespan ($C_{\max}$) em todas as instâncias do arquivo:

```bash
uv run flowshop-analyzer benchmark -i 300
```

### 4. Executar o binário C++ puro (opcional)

Caso queira rodar a implementação C++ diretamente sem a camada Python:

```bash
# Linux / macOS
./build/bin/flowshop_runner

# Windows
.\build\bin\flowshop_runner.exe
```

## Referência de Parâmetros da CLI (`solve`)

| Opção          | Abreviação | Descrição                                                                  | Padrão           |
| :------------- | :--------- | :------------------------------------------------------------------------- | :--------------- |
| `--file`       | `-f`       | Caminho para o arquivo de instâncias da OR-Library                         | `instancias.txt` |
| `--algo`       | `-a`       | Algoritmo a executar (pode ser repetido)                                   | `tabu_original`  |
| `--tenure`     | `-t`       | Tamanho da lista tabu (`0` = automático $\max(5, \lfloor 10N/11 \rfloor)$) | `0`              |
| `--iterations` | `-i`       | Número máximo de iterações da Busca Tabu                                   | `300`            |
| `--output`     | `-o`       | Caminho para salvar o gráfico de convergência (`.png`)                     | Nenhum           |
| `--gantt`      | `-g`       | Caminho para salvar o gráfico de Gantt por máquina (`.png`)                | Nenhum           |
