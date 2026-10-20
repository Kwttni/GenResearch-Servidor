"""
Gera gráficos a partir dos dados da última execução.
"""

import csv
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from config import PASTA_RESULTADOS, ARQ_ULTIMA_EXCE, ARQ_BRUTOS, GRAFICOS


def pegar_resultados():
    arqv_ultima_exec = PASTA_RESULTADOS / ARQ_ULTIMA_EXCE

    if arqv_ultima_exec.exists():
        pasta = Path(arqv_ultima_exec.read_text(encoding="utf-8").strip())

        if (pasta / ARQ_BRUTOS).exists():
            return pasta

    return PASTA_RESULTADOS


def gerar_graficos():
    pasta = pegar_resultados()
    arqv_dados = pasta / ARQ_BRUTOS

    if not arqv_dados.exists():
        (PASTA_RESULTADOS / GRAFICOS).write_text("Não foi encontrado o arquivo brutos.csv.\n", encoding="utf-8")
        return

    dados = pd.read_csv(arqv_dados)

    arqv_criados = []
    colunas_num = [coluna for coluna in ("tempo_total_s", "vazao_req_s", "latencia_p95", "rss_max_mb", "cache_hits", "cache_misses")
                   if coluna in dados.columns]

    for coluna in colunas_num:
        resumo = dados.groupby(["exp", "config"], dropna=False)[coluna].mean().reset_index()

        if resumo.empty:
            continue

        resumo["rotulo"] = resumo["exp"].astype(str) + " - " + resumo["config"].astype(str)
        figura, eixo = plt.subplots(figsize=(11, 6))
        eixo.bar(resumo["rotulo"], resumo[coluna])
        eixo.set_title(f"Média de {coluna}")
        eixo.set_ylabel(coluna)
        eixo.tick_params(axis="x", rotation=75)
        figura.tight_layout()
        caminho = pasta / f"grafico_{coluna}.png"
        figura.savefig(caminho, dpi=150)
        plt.close(figura)
        arqv_criados.append(str(caminho))

    (PASTA_RESULTADOS / GRAFICOS).write_text("Gráficos criados:\n" + "\n".join(arqv_criados) + "\n", encoding="utf-8")


if __name__ == "__main__":
    gerar_graficos()