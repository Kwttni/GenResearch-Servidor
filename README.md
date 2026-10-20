# GenResearch-Servidor

Este projeto foi desenvolvido para a Atividade 2 da disciplina de Sistemas Operacionais 2026.2.

O GenResearch-Servidor é uma implementação simplificada de um sistema de Recuperação Aumentada por Geração (RAG). O objetivo do projeto é analisar como o Sistema Operacional se comporta ao executar tarefas que exigem muitos recursos computacionais, principalmente em aplicações de Inteligência Artificial.

Durante os experimentos, são avaliados aspectos como uso de memória RAM e memória virtual, paginação, leitura e escrita em disco, mapeamento de arquivos com `mmap`, uso de cache e sincronização entre threads, utilizando mecanismos como mutexes e semáforos.

## Tecnologias utilizadas

- **Linguagem:** Python 3.14+
- **Concorrência:** `threading` e `multiprocessing`, incluindo o modelo produtor-consumidor.
- **Sincronização:** `threading.Lock` e `threading.Semaphore`.
- **Armazenamento:** SQLite (`genresearch.db`) e matrizes NumPy (`vetores.npy`).
- **Memória e I/O:** `mmap` e cache LRU.
- **Monitoramento:** `vmstat`, `iostat`, `free`, `ps`, `top`, `strace`, `resource` e `time`.

## Estrutura do projeto

```text
GenResearch-Servidor/
├── dataset/               # Arquivo CSV utilizado nos experimentos
├── resultados/            # Métricas e logs gerados durante os testes
├── ambiente.py            # Coleta informações do hardware e do SO
├── config.py              # Configurações gerais do projeto
├── experimentos.py        # Executa os experimentos C1 a C6 e a Parte D
├── graficos.py            # Gera gráficos dos resultados
├── ingestao.py            # Processa os textos e gera os vetores
├── metricas.py            # Mede o uso de RAM, CPU e Page Faults
├── servidor.py            # Implementa filas, cache LRU e simulação de RAG
├── sinc_demo.py           # Demonstra condições de corrida e uso de locks
├── vetores.py             # Implementa operações matemáticas e hash dos embeddings
├── Makefile               # Facilita a execução dos comandos
└── requirements.txt       # Lista as dependências do Python
```

## Instalação e configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/Kwttni/GenResearch-Servidor.git
cd GenResearch-Servidor
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Preparar o dataset

Baixe o arquivo `reviews_0-250.csv` no Kaggle e coloque-o dentro da pasta `dataset/`.

Disponível em: https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews

## Como executar os experimentos

O projeto utiliza um `Makefile` para facilitar a execução das etapas.

### 1. Limpar os resultados anteriores

```bash
make limpar
```

Remove os dados de testes anteriores para preparar o ambiente para uma nova execução.

### 2. Registrar as informações do sistema

```bash
make ambiente
```

Registra informações sobre o processador, a memória RAM, o kernel e os discos disponíveis.

### 3. Preparar os dados

```bash
make preparar
```

Lê o arquivo CSV, divide os textos em partes menores (*chunks*), gera os vetores (*embeddings*) e cria os arquivos `genresearch.db` e `vetores.npy`.

### 4. Executar e monitorar os experimentos

```bash
make monitorar
```

Executa os experimentos C1 a C6 e a Parte D, enquanto ferramentas de monitoramento coletam informações sobre o uso dos recursos do sistema. Os resultados são registrados no arquivo `brutos.csv`.

### 5. Coletar informações do Sistema Operacional

```bash
make evidencias-so
```

Coleta informações sobre threads, chamadas de sistema (*syscalls*) e uso de memória para ajudar na análise dos resultados.

### 6. Gerar os gráficos

```bash
make graficos
```

Utiliza os dados de `brutos.csv` para gerar gráficos sobre latência, vazão, uso de RAM (RSS) e taxa de acerto do cache.

## Experimentos realizados

- **C1 e C2:** Comparam a leitura de arquivos usando `read()` e o mapeamento de memória com `mmap`.
- **C3:** Analisa o comportamento das threads, a capacidade de atender consultas simultâneas e os efeitos da limitação do tamanho da fila.
- **C4:** Compara as estratégias de cache LRU e FIFO e seus impactos no desempenho.
- **C5:** Avalia o comportamento do sistema sob alta pressão de memória, observando paginação, uso de swap e *Page Faults*.
- **C6 e Parte D:** Investigam situações como limites de memória, saturação de filas e condições de corrida causadas pela ausência de mecanismos de sincronização.

## Autoria

Desenvolvido por **Mariana Silva Costa** para fins acadêmicos.
