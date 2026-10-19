"""
Executa uma demonstração do servidor e salva as métricas em JSON.
"""

import argparse
import json
from pathlib import Path
from servidor import Servidor, gera_consultas


def demonstrar(quant, trabalhadores, custo_resp, usar_mmap = False, usar_ollama = False):
    consultas = gera_consultas(quant, "mista")
    servidor = Servidor(n_trab = trabalhadores, 
                        custo_resp = custo_resp,
                        usa_mmap = usar_mmap,
                        usa_ollama = usar_ollama)

    return servidor.consultar(consultas)


def main():
    analisador = argparse.ArgumentParser(description = "Executa uma demonstração do servidor.")
    analisador.add_argument("--trabalhadores", type=int, default=4)
    analisador.add_argument("--n", type=int, default=400)
    analisador.add_argument("--custo", type=float, default=0.05)
    analisador.add_argument("--mmap", action="store_true")
    analisador.add_argument("--ollama", action="store_true")
    analisador.add_argument("--saida", default="resultados/demo_saida.json")

    args = analisador.parse_args()
    res = demonstrar(args.n, args.trabalhadores, args.custo, args.mmap, args.ollama)

    caminho = Path(args.saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()