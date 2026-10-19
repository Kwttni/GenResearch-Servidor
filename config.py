"""
Configura os caminhos e o registro de eventos usados pelo projeto.
"""

from pathlib import Path
import logging

CSV_SEPHORA = "dataset/reviews_0-250.csv"
PASTA_RESULTADOS = Path("resultados")
ARQ_DB = "genresearch.db"
ARQ_IDX = "vetores.npy"
ARQ_META = "meta.json"
ARQ_LOG = "genresearch.log"
ARQ_AMBIENTE = "ambiente.txt"
ARQ_ULTIMA_EXCE = "ULTIMA_EXECUCAO.txt"
ARQ_ANDAMENTO = "andamento.log"
ARQ_BRUTOS = "brutos.csv"
GRAFICOS = "graficos.log"
DIM = 1024

PASTA_RESULTADOS.mkdir(exist_ok=True)

registro = logging.getLogger("genresearch")
registro.setLevel(logging.INFO)
registro.propagate = False

if not registro.handlers:
    manipulador = logging.FileHandler(ARQ_LOG, encoding="utf-8")
    manipulador.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    registro.addHandler(manipulador)


def salva_no_log(nivel, mensagem):
    """
    Salva uma mensagem no arquivo de log, sem imprimir no terminal.
    """
    
    metodo = getattr(registro, nivel.lower(), registro.info)
    metodo(mensagem)
