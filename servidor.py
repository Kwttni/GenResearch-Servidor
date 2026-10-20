import collections
import json
import os
import pathlib
import random
import sqlite3
import threading
import time
import numpy as np
from config import DIM, ARQ_DB, ARQ_IDX, ARQ_META, salva_no_log
from vetores import vetor_consulta, normalizar_texto
from metricas import Medicao, gera_resumo

PRODUTOS_TESTE = ["moisturizer", "foundation", "lipstick", "sunscreen", "serum", "mascara", "cleanser",
                  "eye cream", "perfume", "primer", "blush", "shampoo"]

CARACT_TESTE = ["dry skin", "oily skin", "sensitive skin", "long lasting", "fragrance free", "natural finish",
                "acne prone", "for winter", "travel size", "gift idea"]

MODELOS_CONSULTA = ["{p} {a}", "best {p} {a}", "{a} {p} recommendation"]


def gera_consultas(quant, modo="mista", taxa_repeticao=0.5, seed=1):
    """
    Gera consultas variadas para os testes do trabalho.
    """

    gerador_aleatorio = random.Random(seed)
    todas_consultas = [f"{p} {a}" for p in PRODUTOS_TESTE for a in CARACT_TESTE]
    gerador_aleatorio.shuffle(todas_consultas)

    if modo == "repetidas":
        return [todas_consultas[i % 5] for i in range(quant)]

    if modo == "distintas":
        return [todas_consultas[i % len(todas_consultas)] for i in range(quant)]

    if modo == "parafrases":
        saida = []
        for i in range(quant):
            base = todas_consultas[(i // 3) % len(todas_consultas)]
            prod = next(x for x in PRODUTOS_TESTE if base.startswith(x))
            saida.append(MODELOS_CONSULTA[i % 3].format(p=prod, a=base[len(prod) + 1:]))

        return saida

    saida, n = [], 0
    for _ in range(quant):
        if saida and gerador_aleatorio.random() < taxa_repeticao:
            saida.append(gerador_aleatorio.choice(saida))

        else:
            saida.append(todas_consultas[n % len(todas_consultas)])
            n += 1

    return saida


class ErroServico(Exception): pass


class Buffer:
    """
    Fila limitada com semáforos e mutex para controle de concorrência.
    """

    def __init__(self, capacidade):
        self.capacidade = capacidade
        self.itens = collections.deque()
        self.vazios = threading.Semaphore(capacidade)
        self.cheios = threading.Semaphore(0)
        self.mutex = threading.Lock()
        self.max_tam = 0
        self.soma_tam = 0
        self.quant_amostras = 0
        self.bloqueio_produtores = 0.0
        self.total_saidas = 0

    def adicionar_na_fila(self, item, timeout=None):
        """
        Insere um item na fila compartilhada. Se estiver cheia, aguarda até o tempo limite.
        """

        tempo_inicio = time.perf_counter()

        if not self.vazios.acquire(timeout=timeout):
            return False

        tempo_espera = time.perf_counter() - tempo_inicio

        with self.mutex:
            if isinstance(item, dict):
                item["t_enq"] = time.perf_counter()

            self.itens.append(item)
            tam_atual = len(self.itens)
            self.max_tam = max(self.max_tam, tam_atual)
            self.soma_tam += tam_atual
            self.quant_amostras += 1
            self.bloqueio_produtores += tempo_espera

        self.cheios.release()
        return True

    def retirar_da_fila(self, timeout=None):
        """
        Retira o próximo pedido disponível da fila para ser processado pelos consumidores.
        """

        if not self.cheios.acquire(timeout=timeout):
            return None

        with self.mutex:
            item = self.itens.popleft()

            if isinstance(item, dict):
                self.total_saidas += 1
                item["seq_saida"] = self.total_saidas

        self.vazios.release()
        return item

    def tam_medio(self):
        """
        Calcula a média de itens que ficaram armazenados na fila ao longo da execução.
        """

        return self.soma_tam / self.quant_amostras if self.quant_amostras else 0.0


class Cache:
    """
    Cache em memória com regra LRU (o item mais antigo é removido primeiro).
    """

    def __init__(self, capacidade, regra="LRU"):
        self.capacidade = capacidade
        self.regra = regra
        self.dict_cache = collections.OrderedDict()
        self.lock = threading.Lock()
        self.acertos = 0
        self.erros = 0
        self.trocas = 0
        self.sobrescritas = 0

    def obter(self, chave):
        """
        Busca uma resp já armazenada no cache usando o texto da consulta como chave.
        """

        with self.lock:
            if chave in self.dict_cache:
                self.acertos += 1
                if self.regra == "LRU":
                    self.dict_cache.move_to_end(chave)
                return self.dict_cache[chave]
            self.erros += 1
            return None

    def inserir(self, chave, valor):
        """
        Guarda uma nova resp no cache, aplicando a regra LRU se atingir a capacidade máxima.
        """

        if self.capacidade <= 0:
            return

        with self.lock:
            if chave in self.dict_cache:
                self.sobrescritas += 1

            elif len(self.dict_cache) >= self.capacidade:
                self.dict_cache.popitem(last=False)
                self.trocas += 1

            self.dict_cache[chave] = valor
            self.dict_cache.move_to_end(chave)

    def tam(self):
        """
        Retorna quantos itens estão guardados no cache no momento.
        """

        with self.lock:
            return len(self.dict_cache)


class Servidor:
    """
    Gerenciador principal do servidor de recuperação e IA do projeto.
    """

    def __init__(self, db=ARQ_DB, idx=ARQ_IDX, meta=ARQ_META, n_trab=2, cap_fila=50, cap_cache=64, pol="LRU",
                 usa_mmap=False, topk=3, ctx_max=2000, custo_resp=0.05, custo_tok=2e-5, p_falha=0.0,
                 tentativas=2, timeout_put=5.0, tent_put=0, usa_ollama=False, modelo_llm="llama3.2"):

        self.db, self.idx_arq, self.meta_arq = db, idx, meta
        self.n_trab, self.cap_fila, self.cap_cache, self.pol = n_trab, cap_fila, cap_cache, pol
        self.usa_mmap, self.topk, self.ctx_max = usa_mmap, topk, ctx_max
        self.custo_resp, self.custo_tok, self.p_falha, self.tentativas = custo_resp, custo_tok, p_falha, tentativas
        self.timeout_put, self.tent_put, self.usa_ollama, self.modelo_llm = timeout_put, tent_put, usa_ollama, modelo_llm
        self.lock_mut = threading.Lock()
        self.count, self.calc, self.registros = collections.Counter(), collections.Counter(), []
        self.ocupado_total = 0.0
        self.cache = Cache(cap_cache, pol)
        self.fila = Buffer(cap_fila)
        self.metadados, self.db_ok, self.indice = {}, False, None

    def incrementar(self, chave, valor = 1):
        """
        Incrementa um contador de estatísticas.
        """

        with self.lock_mut:
            self.count[chave] += valor

    def uri_banco(self):
        """
        Gera o endereço URI para conectar ao banco de dados SQLite em modo somente leitura.
        """

        return pathlib.Path(os.path.abspath(self.db)).as_uri() + "?mode=ro"

    def carregar(self):
        """
        Lê os metadados, valida a conn com o banco SQLite e carrega o índice numpy.
        """

        try:
            with open(self.meta_arq, encoding="utf-8") as arquivo:
                self.metadados = json.load(arquivo)

        except (OSError, ValueError):
            self.metadados = {"modo": "simulado", "dim": DIM}

        for tentativa_atual in range(self.tentativas + 1):
            try:
                if not os.path.exists(self.db):
                    raise FileNotFoundError(self.db)

                conn = sqlite3.connect(self.uri_banco(), uri=True)
                conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
                conn.close()

                self.db_ok = True

                break

            except (OSError, sqlite3.Error) as erro:
                self.incrementar("falhas")

                salva_no_log("FALHA", f"banco indisponível ({erro})")

                if tentativa_atual < self.tentativas:
                    self.incrementar("retentativas")
                    time.sleep(0.05 * 2 ** tentativa_atual)

        for tentativa_atual in range(self.tentativas + 1):
            try:
                self.indice = np.load(self.idx_arq, mmap_mode="r" if self.usa_mmap else None)
                break

            except (OSError, ValueError) as erro:
                self.incrementar("falhas")
                salva_no_log("FALHA", f"índice indisponível ({erro})")

                if tentativa_atual < self.tentativas:
                    self.incrementar("retentativas")
                    time.sleep(0.05 * 2 ** tentativa_atual)

    def recuperar_contexto(self, consulta, conn):
        """
        Busca os trechos de texto mais relevantes no banco usando similaridade vetorial ou busca textual.
        """

        if conn is None:
            return [], 0, 0, "nenhum"
        if self.indice is not None:

            vetor_q = vetor_consulta(consulta, self.metadados)
            similaridades = self.indice @ vetor_q
            k_elementos = min(self.topk, len(similaridades))
            ids = np.argpartition(-similaridades, k_elementos - 1)[:k_elementos]
            ids = ids[np.argsort(-similaridades[ids])]
            placeholders = ",".join("?" * len(ids))
            linhas = dict(conn.execute(f"SELECT id, texto FROM chunks WHERE id IN ({placeholders})",
                                       [int(i) for i in ids]).fetchall())
            textos = [linhas[int(i)] for i in ids if int(i) in linhas]
            metodo = "vetorial"

        else:
            termo = max(normalizar_texto(consulta).split() or [""], key=len)
            textos = [r[0] for r in conn.execute("SELECT texto FROM chunks WHERE texto LIKE ? LIMIT ?",
                                                 (f"%{termo}%", self.topk)).fetchall()]
            metodo = "lexical"

        contexto, usados = [], 0
        for texto in textos:
            bytes_texto = texto.encode("utf-8")
            espaco_restante = self.ctx_max - usados

            if espaco_restante <= 0:
                break

            if len(bytes_texto) > espaco_restante:
                texto = bytes_texto[:espaco_restante].decode("utf-8", errors="ignore")
                bytes_texto = bytes_texto[:espaco_restante]

            contexto.append(texto)
            usados += len(bytes_texto)

        return contexto, usados, usados // 4, metodo

    def gerar_resp(self, consulta, contexto, tokens):
        """
        Gera a resp final utilizando o Ollama local ou simulando o custo de processamento da IA.
        """

        for tentativa_atual in range(self.tentativas + 1):
            try:
                if self.p_falha and random.random() < self.p_falha:
                    raise ErroServico("falha injetada")

                if self.usa_ollama:
                    import ollama
                    resp_llm = ollama.generate(model=self.modelo_llm,
                                               prompt="\n".join(contexto) + f"\nPergunta: {consulta}",
                                               options={"num_predict": 64})
                    return resp_llm["response"][:200], False

                time.sleep(self.custo_resp + tokens * self.custo_tok)
                return f"resp simulada ({tokens} tokens)", False

            except Exception as erro:
                self.incrementar("falhas_geracao")

                if tentativa_atual < self.tentativas:
                    self.incrementar("retentativas")
                    time.sleep(0.01 * 2 ** tentativa_atual)

        self.incrementar("resps_degradadas")

        return "[serviço indisponível]", True

    def processar_req(self, req, conn, worker_id):
        """
        Lida com um pedido individual: confere o cache, busca o contexto no banco e gera a resp.
        """

        tempo_inicial = time.perf_counter()
        tempo_espera = tempo_inicial - req["t_enq"]
        chave_busca = normalizar_texto(req["consulta"])

        registro_resp = {
            "id": req["id"], "prod": req["prod"], "ordem": req["ordem"],
            "seq_saida": req.get("seq_saida", 0), "worker": worker_id, "espera": tempo_espera,
            "rec": 0.0, "resp": 0.0, "hit": 0, "n_trechos": 0, "bytes_ctx": 0, "tokens": 0, "degradada": 0
        }

        valor_cache = self.cache.obter(chave_busca)

        if valor_cache is not None:
            registro_resp["hit"] = 1

        else:
            tempo_inicio_rec = time.perf_counter()
            try:
                contexto, tam_bytes, tokens_total, _ = self.recuperar_contexto(req["consulta"], conn)

            except:
                contexto, tam_bytes, tokens_total = [], 0, 0

            registro_resp["rec"] = time.perf_counter() - tempo_inicio_rec
            registro_resp["n_trechos"] = len(contexto)
            registro_resp["bytes_ctx"] = tam_bytes
            registro_resp["tokens"] = tokens_total

            tempo_inicio_gen = time.perf_counter()
            texto_resp, degradada = self.gerar_resp(req["consulta"], contexto, tokens_total)
            registro_resp["resp"] = time.perf_counter() - tempo_inicio_gen
            registro_resp["degradada"] = int(degradada)
            registro_resp["resp_texto"] = texto_resp

            if not degradada:
                self.cache.inserir(chave_busca, registro_resp)

            with self.lock_mut:
                self.calc[chave_busca] += 1

        registro_resp["servico"] = time.perf_counter() - tempo_inicial

        with self.lock_mut:
            self.registros.append(registro_resp)

    def consumidor(self, worker_id):
        """
        Função executada pelas threads trabalhadoras que retiram pedidos da fila e realizam o processamento.
        """

        conn = sqlite3.connect(self.uri_banco(), uri=True, check_same_thread=False) if self.db_ok else None
        tempo_ocupado = 0.0

        while True:
            req = self.fila.retirar_da_fila()

            if req is None:
                break

            tempo_inicio = time.perf_counter()

            try:
                self.processar_req(req, conn, worker_id)

            except Exception:
                self.incrementar("falhas")

            tempo_ocupado += time.perf_counter() - tempo_inicio

        if conn:
            conn.close()

        with self.lock_mut:
            self.ocupado_total += tempo_ocupado

    def produtor(self, id_produtor, lote_consultas, intervalo_tempo):
        """
        Função executada pelas threads produtoras que geram e enviam lotes de consultas para a fila.
        """
        for indice, consulta_texto in enumerate(lote_consultas):
            req = {
                "id": f"{id_produtor}-{indice}", "prod": id_produtor, "ordem": indice,
                "consulta": consulta_texto, "bytes": len(consulta_texto.encode("utf-8"))
            }

            sucesso = False

            for _ in range(self.tent_put + 1):
                if self.fila.adicionar_na_fila(req, timeout=self.timeout_put):
                    sucesso = True
                    break
                self.incrementar("put_timeouts")

            if sucesso:
                self.incrementar("enfileiradas")
            else:
                self.incrementar("rejeitadas")

            if intervalo_tempo:
                time.sleep(intervalo_tempo)

    def consultar(self, consultas, n_prod=2, intervalo_prod=0.0):
        """
        Inicializa os recursos, dispara as threads de produtores e consumidores e mede o tempo global.
        """

        self.count.clear()
        self.registros, self.calc, self.ocupado_total = [], collections.Counter(), 0.0
        self.cache, self.fila = Cache(self.cap_cache, self.pol), Buffer(self.cap_fila)
        self.carregar()

        with Medicao() as medicao_so:
            tempo_inicio_global = time.perf_counter()
            consumidores = [threading.Thread(target=self.consumidor, args=(i + 1,)) for i in range(self.n_trab)]
            produtores = [threading.Thread(target=self.produtor, args=(j, consultas[j::n_prod], intervalo_prod)) for j
                          in range(n_prod)]

            for thread in consumidores + produtores:
                thread.start()

            for thread in produtores:
                thread.join()

            for _ in consumidores:
                self.fila.adicionar_na_fila(None)

            for thread in consumidores:
                thread.join()

            tempo_total = time.perf_counter() - tempo_inicio_global

        return self.junta_metricas(tempo_total, medicao_so.resultado, n_prod)

    def junta_metricas(self, tempo_total, metricas_so, n_prod):
        """
        Reúne todas as métricas, contadores e dados de SO em um único dicionário para fins de relatório/CSV.
        """

        registros = self.registros
        processadas = len(registros)
        enfileiradas = self.count["enfileiradas"]
        rejeitadas = self.count["rejeitadas"]
        enviadas = enfileiradas + rejeitadas
        ids_req = [r["id"] for r in registros]
        violacoes_fifo = 0
        por_produtor = collections.defaultdict(list)

        for r in registros:
            por_produtor[r["prod"]].append(r)

        for lista_prod in por_produtor.values():
            lista_prod.sort(key=lambda r: r["ordem"])
            violacoes_fifo += sum(1 for a, b in zip(lista_prod, lista_prod[1:]) if b["seq_saida"] < a["seq_saida"])

        erros = [r for r in registros if not r["hit"]]
        acertos = processadas - len(erros)
        tempo_medio_erro = float(np.mean([r["servico"] for r in erros])) if erros else 0.0
        obj_cache = self.cache

        res_final = {
            "n_trabalhadores": self.n_trab, "n_produtores": n_prod, "capacidade_fila": self.cap_fila,
            "cache_cap": self.cap_cache, "regra": self.pol, "usar_mmap": int(self.usa_mmap),
            "topk": self.topk, "ctx_max_bytes": self.ctx_max, "enviadas": enviadas, "enfileiradas": enfileiradas,
            "rejeitadas": rejeitadas, "put_timeouts": self.count["put_timeouts"], "processadas": processadas,
            "perdidos": enviadas - processadas, "duplicados": len(ids_req) - len(set(ids_req)),
            "violacoes_fifo": violacoes_fifo, "tempo_total_s": tempo_total,
            "vazao_req_s": processadas / tempo_total if tempo_total > 0 else 0.0,
            "fila_media": self.fila.tam_medio(), "fila_max": self.fila.max_tam,
            "bloqueio_produtores_s": self.fila.bloqueio_produtores,
            "utilizacao_trabalhadores": self.ocupado_total / (self.n_trab * tempo_total) if tempo_total > 0 else 0.0,
            "cache_hits": acertos, "cache_misses": len(erros),
            "taxa_acerto": acertos / processadas if processadas else 0.0,
            "taxa_erro": len(erros) / processadas if processadas else 0.0,
            "cache_tam": obj_cache.tam(), "cache_substituicoes": obj_cache.trocas,
            "geracoes_repetidas": sum(max(0, v - 1) for v in self.calc.values()),
            "tempo_economizado_s": acertos * tempo_medio_erro, "falhas": self.count["falhas"],
            "retentativas": self.count["retentativas"], "falhas_geracao": self.count["falhas_geracao"],
            "resps_degradadas": self.count["resps_degradadas"],
            "trechos_medio": float(np.mean([r["n_trechos"] for r in erros])) if erros else 0.0,
            "bytes_ctx_medio": float(np.mean([r["bytes_ctx"] for r in erros])) if erros else 0.0,
            "tokens_medio": float(np.mean([r["tokens"] for r in erros])) if erros else 0.0,
        }

        res_final.update(gera_resumo("espera", [r["espera"] for r in registros]))
        res_final.update(gera_resumo("recuperacao", [r["rec"] for r in erros]))
        res_final.update(gera_resumo("resp", [r["resp"] for r in erros]))
        res_final.update(gera_resumo("servico", [r["servico"] for r in registros]))
        res_final.update(gera_resumo("latencia", [r["espera"] + r["servico"] for r in registros]))
        res_final.update(metricas_so)

        return res_final

        return res_final