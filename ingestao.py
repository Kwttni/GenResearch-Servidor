"""
Prepara textos do CSV_SEPHORA extraindo colunas específicas, fragmenta,
gera vetores e metadados e armazena-os.
"""

import argparse
import csv
import json
import sqlite3
from pathlib import Path
import numpy as np
from config import ARQ_DB, ARQ_IDX, ARQ_META, CSV_SEPHORA, DIM, salva_no_log
from vetores import vet_lote

TAM_TRECHO = 500
SOBREPOS = 60


def ler_csv(csv, limite=None):
    """
    Lê do CSV da Sephora as colunas: brand_name, product_name, review_title e review_text.
    """

    caminho = Path(csv)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho}")

    docs = []
    with caminho.open("r", encoding="utf-8-sig", newline="") as arqv:
        leitor = csv.DictReader(arqv)
        if not leitor.fieldnames:
            return docs

        for numero, linha in enumerate(leitor):
            brand_name = str(linha.get("brand_name", "")).strip()
            product_name = str(linha.get("product_name", "")).strip()
            review_title = str(linha.get("review_title", "")).strip()
            review_text = str(linha.get("review_text", "")).strip()

            partes = []
            if brand_name:
                partes.append(f"Marca: {brand_name}")
            if product_name:
                partes.append(f"Produto: {product_name}")
            if review_title:
                partes.append(f"Título: {review_title}")
            if review_text:
                partes.append(f"Avaliação: {review_text}")

            texto_completo = " | ".join(partes)

            if texto_completo:
                docs.append({"id": numero, "texto": texto_completo})

            if limite and len(docs) >= limite:
                break

    return docs


def fragmentar_texto(documentos):
    """
    Divide cada texto em pedaços menores.
    """

    trechos = []
    for docs in documentos:
        texto = docs["texto"]

        i = 0
        while i < len(texto):
            trecho = texto[i:i + TAM_TRECHO].strip()
            if trecho:
                trechos.append({"id": len(trechos), "texto": trecho, "documento_id": docs["id"]})
            if i + TAM_TRECHO >= len(texto):
                break
            i += TAM_TRECHO - SOBREPOS

    return trechos


def preparar_dados(csv=CSV_SEPHORA, limite=None, usar_ollama=False):
    """
    Cria os arquivos que o servidor usa para recuperar os trechos a partir do CSV.
    """

    docs = ler_csv(csv, limite)
    trechos = fragmentar_texto(docs)

    if not trechos:
        raise ValueError("Nenhum texto válido foi encontrado para preparar o índice.")

    textos = [trecho["texto"] for trecho in trechos]
    matriz_vetores = vet_lote(textos, usar_ollama=usar_ollama)

    if matriz_vetores.shape[1] != DIM:
        metadados_dimensao = int(matriz_vetores.shape[1])

    else:
        metadados_dimensao = DIM

    # Armazena os textos e metadados.
    conexao = sqlite3.connect(ARQ_DB)
    try:
        conexao.execute("DROP TABLE IF EXISTS chunks")
        conexao.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, texto TEXT NOT NULL, documento_id INTEGER)")
        conexao.executemany(
            "INSERT INTO chunks (id, texto, documento_id) VALUES (?, ?, ?)",
            [(trecho["id"], trecho["texto"], trecho["documento_id"]) for trecho in trechos]
        )

        conexao.commit()

    finally:
        conexao.close()

    # Armazena os indices de vetores.
    np.save(ARQ_IDX, matriz_vetores)

    metadados = {
        "modo": "ollama" if usar_ollama else "simulado",
        "dim": metadados_dimensao,
        "documentos": len(docs),
        "trechos": len(trechos),
        "tamanho_trecho": TAM_TRECHO,
        "sobreposicao": SOBREPOS
    }

    # armazena os metadados da ingestão.
    Path(ARQ_META).write_text(json.dumps(metadados, ensure_ascii=False, indent=2), encoding="utf-8")
    salva_no_log("INFO", f"Preparação concluída: {len(docs)} documentos e {len(trechos)} trechos.")

    Path("resultados").mkdir(exist_ok=True)
    Path("resultados/ingestao.txt").write_text(
        f"Documentos: {len(docs)}\nTrechos: {len(trechos)}\nBanco: {ARQ_DB}\nÍndice: {ARQ_IDX}\nMetadados: {ARQ_META}\n",
        encoding="utf-8"
    )
    return metadados


def main():
    analisador = argparse.ArgumentParser(description="Prepara o banco e os vetores usando apenas os dados do CSV.")
    analisador.add_argument("--csv", default=CSV_SEPHORA, help="Caminho para o arquivo CSV")
    analisador.add_argument("--limite", type=int, default=None, help="Limite de linhas/documentos a ler")
    analisador.add_argument("--ollama", action="store_true", help="Usar Ollama para gerar embeddings")
    args = analisador.parse_args()

    preparar_dados(argumentos.csv, args.limite, args.ollama)


if __name__ == "__main__":
    main()