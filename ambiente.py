"""
Coleta informações do ambiente salva em um arquivo.
"""

from pathlib import Path
import os
import platform
import subprocess
import datetime
from config import PASTA_RESULTADOS, ARQ_AMBIENTE


def saida_comando(comando):
    """
    Executa um comando de consulta e devolve o texto, se estiver disponível.
    """

    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=5, check=False)
        return resultado.stdout.strip() or resultado.stderr.strip() or "Informação indisponível"
    
    except (OSError, subprocess.SubprocessError):
        return "Comando indisponível neste ambiente"


def coletar_ambiente(pasta_saida = PASTA_RESULTADOS):
    """
    Cria o resumo do ambiente e grava no arquivo "ambiente.txt".
    """

    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)

    informacoes = [
        f"Data da coleta: {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"Sistema operacional: {platform.platform()}",
        f"Versão do Python: {platform.python_version()}",
        f"Quantidade de CPUs lógicas: {os.cpu_count() or 'Não identificada'}",
        "", "Processador (lscpu):", saida_comando(["lscpu"]),
        "", "Memória (free -h):", saida_comando(["free", "-h"]),
        "", "Kernel (uname -a):", saida_comando(["uname", "-a"]),
        "", "Disco (df -h .):", saida_comando(["df", "-h", "."]),
    ]

    caminho = pasta / ARQ_AMBIENTE

    caminho.write_text("\n".join(informacoes) + "\n", encoding="utf-8")

    return str(caminho)


if __name__ == "__main__":
    coletar_ambiente()
