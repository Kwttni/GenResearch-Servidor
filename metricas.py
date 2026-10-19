"""
Funções para acompanhar tempo, memória e atividade do processo.
"""

import resource
import time
from pathlib import Path
import numpy as np


def mem_info():
    """
    Lê os dados de memória disponíveis no Linux e converte para MB.
    """

    dados = {}
    caminho = Path("/proc/meminfo")

    if not caminho.exists():
        return dados
    
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        partes = linha.split()

        if len(partes) >= 2 and partes[1].isdigit():
            dados[partes[0].rstrip(":")] = int(partes[1]) / 1024

    return dados


def status_proc():
    """
    Retorna o uso de memória do processo atual em MB.
    """

    rss = vsz = 0.0

    caminho = Path("/proc/self/status")

    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():

            if linha.startswith("VmRSS:"):
                rss = float(linha.split()[1]) / 1024

            elif linha.startswith("VmSize:"):
                vsz = float(linha.split()[1]) / 1024

    return {"rss": rss, "vsz": vsz}


def gera_resumo(nome, valores):
    """
    Calcula estatísticas para uma lista de medidas.
    """

    valores = list(valores)

    if not valores:
        return {f"{nome}_media": 0.0, f"{nome}_mediana": 0.0, f"{nome}_p95": 0.0, f"{nome}_max": 0.0}
    
    return {f"{nome}_media": float(np.mean(valores)), f"{nome}_mediana": float(np.median(valores)),
            f"{nome}_p95": float(np.percentile(valores, 95)), f"{nome}_max": float(np.max(valores))}


class Medicao:
    """
    Registra tempo, memória máxima e falhas de página durante um trecho.
    """

    def __enter__(self):
        self.inicio = time.perf_counter()
        self.uso_inicial = resource.getrusage(resource.RUSAGE_SELF)
        self.memoria_inicial = status_proc()

        return self

    def __exit__(self, tipo, valor, rastreamento):
        uso_final = resource.getrusage(resource.RUSAGE_SELF)
        memoria_final = status_proc()
        self.resultado = {
            "tempo_s": time.perf_counter() - self.inicio,
            "minflt": max(0, uso_final.ru_minflt - self.uso_inicial.ru_minflt),
            "majflt": max(0, uso_final.ru_majflt - self.uso_inicial.ru_majflt),
            "rss_max_mb": max(self.memoria_inicial["rss"], memoria_final["rss"]),
            "vsz_max_mb": max(self.memoria_inicial["vsz"], memoria_final["vsz"]),
        }

        try:
            io = Path("/proc/self/io").read_text(encoding="utf-8").splitlines()
            dados_io = {linha.split(":")[0]: int(linha.split(":")[1].strip()) for linha in io if ":" in linha}
            self.resultado["rchar"] = dados_io.get("rchar", 0)
            self.resultado["read_bytes"] = dados_io.get("read_bytes", 0)

        except (OSError, ValueError):
            self.resultado["rchar"] = 0
            self.resultado["read_bytes"] = 0
            
        return False
