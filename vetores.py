"""
Cria vetores de texto para os testes de busca do projeto.
"""

import hashlib
import re
import numpy as np
from config import DIM, salva_no_log


def vetor_por_hash(texto, dimensao = DIM):
    """
    Cria um vetor determinístico por palavras, sem precisar baixar um modelo.
    """

    vetor = np.zeros(dimensao, dtype = np.float32)

    palavras = normalizar_texto(texto).split()
    for palavra in palavras:
        resumo = hashlib.sha256(palavra.encode("utf-8")).digest()
        indice = int.from_bytes(resumo[:4], "little") % dimensao
        sinal = 1.0 if resumo[4] % 2 == 0 else -1.0
        vetor[indice] += sinal

    return normalizar_vetor(vetor)


def normalizar_vetor(vetor):
    norma = float(np.linalg.norm(vetor))

    return vetor / norma if norma else vetor


def vetor_ollama(texto, modelo = "mxbai-embed-large"):
    """
    Tenta usar o modelo local do Ollama e usa hash se não estiver disponível.
    """

    try:
        import ollama
        resposta = ollama.embed(model=modelo, input=texto)
        
        return normalizar_vetor(np.asarray(resposta["embeddings"][0], dtype=np.float32))
    
    except Exception as erro:
        salva_no_log("INFO", f"Embedding local indisponível; usando vetor por hash ({erro})")

        return vetor_por_hash(texto)


def vet_lote(textos, usar_ollama = False):
    """
    Transforma uma lista de textos em uma matriz de vetores.
    """

    funcao_vetor = vetor_ollama if usar_ollama else vetor_por_hash

    vetores = [funcao_vetor(texto) for texto in textos]

    if not vetores:
        return np.empty((0, DIM), dtype=np.float32)
    
    dimensao = len(vetores[0])

    return np.vstack([v if len(v) == dimensao else np.resize(v, dimensao) for v in vetores]).astype(np.float32)


def vetor_consulta(texto, metadados = None):
    """
    Cria o vetor de uma consulta usando o mesmo modo do índice.
    """

    usar_ollama = bool((metadados or {}).get("modo") == "ollama")
    vetor = vetor_ollama(texto) if usar_ollama else vetor_por_hash(texto, int((metadados or {}).get("dim", DIM)))

    return vetor


def normalizar_texto(texto):
    """
    Deixa o texto em minúsculas e remove espaços repetidos.
    """

    return re.sub(r"\s+", " ", str(texto).lower()).strip()

