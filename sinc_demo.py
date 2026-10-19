"""
Demonstra problemas comuns de sincronização entre threads.
"""

import json
import threading
import time
from pathlib import Path
from queue import Queue


def atuliza_sem_bloqueio(quant=10000):
    cont = {"valor": 0}

    def atualizar():
        for _ in range(quant):
            valor_atual = cont["valor"]
            time.sleep(0)
            cont["valor"] = valor_atual + 1

    inicio = time.perf_counter()
    threads = [threading.Thread(target=atualizar) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return {
        "atualizacoes_perdidas": max(0, quant * 4 - cont["valor"]),
        "tempo_s": time.perf_counter() - inicio,
    }


def atualiza_com_bloqueio(quant=10000):
    cont = {"valor": 0}
    bloqueio = threading.Lock()

    def atualizar():
        for _ in range(quant):
            with bloqueio:
                cont["valor"] += 1

    inicio = time.perf_counter()
    threads = [threading.Thread(target=atualizar) for _ in range(4)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return {
        "atualizacoes_perdidas": max(0, quant * 4 - cont["valor"]),
        "tempo_s": time.perf_counter() - inicio,
    }


def testar_fila():
    fila = Queue(maxsize=2)
    inicio = time.perf_counter()
    fila.put("primeiro")
    fila.put("segundo")
    bloqueio_detectado = fila.full()
    fila.get()
    fila.put("terceiro")

    return {
        "fila_max": 2,
        "deadlock_detectado": int(bloqueio_detectado),
        "recuperado": int(not fila.empty()),
        "tempo_s": time.perf_counter() - inicio,
    }


def roda_tudo():
    """
    Retorna os resultados das variações para o relatório dos experimentos.
    """

    sem_bloqueio = atuliza_sem_bloqueio()
    com_bloqueio = atualiza_com_bloqueio()
    fila = testar_fila()

    return [
        ("atualizacao_sem_bloqueio", sem_bloqueio),
        ("atualizacao_com_bloqueio", com_bloqueio),
        ("fila_limitada", fila),
    ]


def main():
    Path("resultados").mkdir(exist_ok=True)
    res = {nome: dados for nome, dados in roda_tudo()}
    Path("resultados/sinc_demo.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()